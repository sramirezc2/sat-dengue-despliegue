"""Recorrer la interfaz Streamlit nativa con contexto exclusivamente artificial."""

import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import pandas as pd
import pytest
import streamlit as st
from configuracion import ROOT
from contexto_paquete import ORIGINS
from inferencia import load_model
from sat_dengue_pipeline.domain.canonical import COUNTS
from streamlit.testing.v1 import AppTest
from test_inferencia import context, write_context


@pytest.fixture
def demo_context(tmp_path, monkeypatch):
    """Instalar un contexto artificial aislado y vaciar solo la caché de pruebas."""
    model = load_model()
    write_context(tmp_path, model, frames={month: context(model, month) for month in ORIGINS})
    monkeypatch.setenv("SATD_DEMO_CONTEXT_DIR", str(tmp_path))
    st.cache_resource.clear()
    yield model
    st.cache_resource.clear()


def click(app: AppTest, label: str) -> AppTest:
    """Activar el botón identificado por su etiqueta visible."""
    return next(button for button in app.button if button.label == label).click().run()


def test_sample_budget_and_restart(demo_context, monkeypatch) -> None:
    """Cargar, inferir una vez, cambiar cupos y reiniciar sin modificar posiciones."""
    calls = []
    score = type(demo_context).score

    def counted(self, X):
        """Contar scoring real del modelo congelado durante los reruns de la UI."""
        calls.append(len(X))
        return score(self, X)

    monkeypatch.setattr(type(demo_context), "score", counted)
    app = AppTest.from_file(ROOT / "demo/app.py", default_timeout=15).run()
    assert not app.exception and not app.error
    assert "Simulación de capacidad" in app.warning[0].value
    click(app, "Cargar muestra artificial")
    assert not app.exception and not calls
    assert any("Datos artificiales" in item.value for item in app.caption)
    click(app, "Calcular prioridades T+2")
    assert not app.exception and len(calls) == 1
    assert app.selectbox[0].value == 10
    baseline = app.dataframe[0].value.copy()
    assert baseline.Priorizado.sum() == 8
    assert any("2025-12" in item.value for item in app.subheader)
    maps = [str(item.proto) for item in app.get("iframe")]
    assert len(maps) == 2
    for percentage, expected in [(5, 4), (15, 12), (20, 16), (10, 8)]:
        app.selectbox[0].select(percentage).run()
        assert not app.exception and len(calls) == 1
        actual = app.dataframe[0].value
        assert actual.Priorizado.sum() == expected
        pd.testing.assert_frame_equal(
            actual.drop(columns="Priorizado"), baseline.drop(columns="Priorizado")
        )
        if percentage != 10:
            assert [str(item.proto) for item in app.get("iframe")] != maps
        assert not any("score" in column.lower() or "probab" in column.lower() for column in actual)
    restarted = AppTest.from_file(ROOT / "demo/app.py", default_timeout=15).run()
    assert not restarted.exception and not restarted.dataframe
    assert len(calls) == 1
    click(restarted, "Cargar muestra artificial")
    click(restarted, "Calcular prioridades T+2")
    assert not restarted.exception and len(calls) == 2
    pd.testing.assert_frame_equal(restarted.dataframe[0].value, baseline)


def test_missing_context_is_sanitized(tmp_path, monkeypatch) -> None:
    """La ausencia de contexto muestra guía sin traceback ni rutas privadas."""
    monkeypatch.setenv("SATD_DEMO_CONTEXT_DIR", str(tmp_path / "absent"))
    st.cache_resource.clear()
    app = AppTest.from_file(ROOT / "demo/app.py").run()
    assert not app.exception and len(app.error) == 1
    assert "SATD_DEMO_CONTEXT_DIR" in app.error[0].value
    assert str(tmp_path) not in app.error[0].value
    assert not app.dataframe
    st.cache_resource.clear()


def test_corrupt_context_is_sanitized(demo_context, monkeypatch) -> None:
    """Un release ajeno detiene inferencia antes de presentar resultados."""
    index_path = Path(os.environ["SATD_DEMO_CONTEXT_DIR"]) / "contexto.json"
    index = json.loads(index_path.read_bytes())
    index["raw_manifest_sha256"] = "0" * 64
    index_path.write_text(json.dumps(index), encoding="utf-8")
    app = AppTest.from_file(ROOT / "demo/app.py").run()
    assert not app.exception and len(app.error) == 1 and not app.dataframe


def test_insufficient_eligible_warning(demo_context) -> None:
    """La UI informa la limitación y mantiene visibles los excluidos con su motivo."""
    frames = {month: context(demo_context, month) for month in ORIGINS}
    frames[ORIGINS[-1]].loc[5:, f"{COUNTS[0]}_lag1"] = pd.NA
    write_context(Path(os.environ["SATD_DEMO_CONTEXT_DIR"]), demo_context, frames=frames)
    app = AppTest.from_file(ROOT / "demo/app.py", default_timeout=15).run()
    click(app, "Cargar muestra artificial")
    click(app, "Calcular prioridades T+2")
    assert not app.exception and app.dataframe[0].value.Priorizado.sum() == 5
    assert any("se seleccionan 5" in warning.value for warning in app.warning)
    excluded = app.dataframe[1].value
    assert len(excluded) == 71 and excluded.Resultado.eq("Predictores incompletos").all()


def test_streamlit_http_health_and_restart(demo_context, tmp_path) -> None:
    """Arrancar y reiniciar dos procesos reales con salud HTTP y página inicial."""
    with socket.socket() as available:
        available.bind(("127.0.0.1", 0))
        port = available.getsockname()[1]
    command = [
        sys.executable, "-m", "streamlit", "run", str(ROOT / "demo/app.py"),
        "--server.address=127.0.0.1", f"--server.port={port}",
        "--server.headless=true", "--browser.gatherUsageStats=false",
    ]
    for attempt in range(2):
        with (tmp_path / f"server-{attempt}.log").open("w") as log:
            process = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=log)
            try:
                deadline = time.monotonic() + 20
                while True:
                    assert process.poll() is None, "Streamlit terminó antes del smoke HTTP"
                    try:
                        with urllib.request.urlopen(
                            f"http://127.0.0.1:{port}/_stcore/health", timeout=1
                        ) as response:
                            assert response.status == 200 and response.read() == b"ok"
                        break
                    except (urllib.error.URLError, TimeoutError):
                        if time.monotonic() >= deadline:
                            pytest.fail("Streamlit no respondió al smoke HTTP")
                        time.sleep(0.1)
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=2) as response:
                    assert response.status == 200 and b"Streamlit" in response.read()
            finally:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)


def test_cloud_entrypoint_uses_same_application(demo_context):
    """El launcher público conserva carga e inferencia con contexto artificial aislado."""
    app = AppTest.from_file(str(Path(__file__).resolve().parents[2] / "streamlit_app.py"))
    app.run(timeout=30)
    assert not app.exception and not app.error
    next(button for button in app.button if button.label == "Cargar muestra artificial").click()
    app.run(timeout=30)
    next(button for button in app.button if "Calcular prioridades" in button.label).click()
    app.run(timeout=30)
    assert not app.exception and not app.error
    assert len(app.dataframe) >= 1
