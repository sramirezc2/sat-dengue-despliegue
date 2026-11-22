"""Recorrer la interfaz Streamlit nativa con contexto exclusivamente artificial."""

import json
import os
import re
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from xml.etree import ElementTree as ET

import inferencia
import pandas as pd
import pytest
import respaldo_cientifico
import streamlit as st
from configuracion import ROOT
from contexto_paquete import ORIGINS
from ejemplos import SAMPLE_FILENAME, sample_csv
from inferencia import capacity, geography, load_model, parse_upload
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


@pytest.mark.parametrize("entrypoint", ["demo/app.py", "streamlit_app.py"])
def test_sample_capacity_expander_and_restart(demo_context, monkeypatch, entrypoint) -> None:
    """Cargar, inferir una vez, cambiar cupos y reiniciar sin modificar posiciones."""
    calls = []
    score = type(demo_context).score

    def counted(self, X):
        """Contar scoring real del modelo congelado durante los reruns de la UI."""
        calls.append(len(X))
        return score(self, X)

    monkeypatch.setattr(type(demo_context), "score", counted)
    app = AppTest.from_file(ROOT / entrypoint, default_timeout=15).run()
    assert not app.exception and not app.error
    assert "Simulación de capacidad" in app.warning[0].value
    assert not app.get("vega_lite_chart")
    assert not any(item.value == "Respaldo científico del modelo" for item in app.subheader)
    click(app, "Cargar muestra artificial")
    assert not app.exception and not calls
    assert any("Datos artificiales" in item.value for item in app.caption)
    click(app, "Calcular prioridades T+2")
    assert not app.exception and len(calls) == 1
    science = next(item for item in app.expander if item.label == "Respaldo científico del modelo")
    assert not science.proto.expanded
    assert not science.proto.id  # Apertura local en el navegador, sin widget que provoque rerun.
    assert len(science.get("vega_lite_chart")) == 2 and len(science.metric) == 4
    assert not any(item.value == science.label for item in app.subheader)
    assert any(
        "Las alertas de 2025 no se utilizan para evaluar aciertos ni medir el desempeño del modelo."
        in item.value for item in app.caption
    )
    assert not any(
        "2025 es evaluación previamente utilizada." in item.value for item in app.caption
    )
    nodes = list(app.main)
    table = app.dataframe[0]
    excluded = next(item for item in app.expander if item.label == "Municipios no elegibles")
    frames = app.get("iframe")
    assert max(nodes.index(frame) for frame in frames) < nodes.index(table)
    legend = [item for item in app.caption if item.value.startswith("Verde oscuro")]
    assert len(legend) == 1
    assert nodes.index(frames[-1]) < nodes.index(legend[0]) < nodes.index(table)
    assert nodes.index(table) < nodes.index(excluded) < nodes.index(science)
    assert table in app.main.children.values()
    columns = [column for column in app.get("column") if column.get("iframe")]
    assert len(columns) == 2 and columns[0].weight == columns[1].weight
    assert [column.markdown[0].value for column in columns] == ["**Tolima**", "**Meta**"]
    for frame, department, count in zip(frames, ("Tolima", "Meta"), (47, 29), strict=True):
        svg = ET.fromstring(frame.proto.srcdoc)
        assert svg.attrib["height"] == "200" and svg.attrib["width"] == "100%"
        assert svg.attrib["aria-label"] == f"Prioridades por municipio de {department}"
        assert len(svg.findall("path")) == len(svg.findall("path/title")) == count
        x0, y0, width, height = map(float, svg.attrib["viewBox"].split())
        for path in svg.findall("path"):
            for x, y in re.findall(r"(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)", path.attrib["d"]):
                assert x0 < float(x) < x0 + width and y0 < float(y) < y0 + height
    assert app.selectbox[0].value == 10
    assert app.selectbox[0].options == [f"{p} %" for p in range(5, 101, 5)]
    baseline = app.dataframe[0].value.copy()
    ordered = app.session_state["ranking"].copy()
    historical = [(metric.label, metric.value) for metric in app.metric][-4:]
    assert historical == [("Sensibilidad", "47,6 %"), ("Precisión", "35,0 %"),
                          ("F1", "0,403"), ("Falsas alertas por inicio anticipado", "1,86")]
    assert len(app.get("vega_lite_chart")) == 2
    assert baseline.Priorizado.sum() == 8
    assert any("2025-12" in item.value for item in app.subheader)
    maps = [str(item.proto) for item in app.get("iframe")]
    assert len(maps) == 2
    for percentage in [*range(5, 101, 5), 10]:
        expected = min(capacity(percentage), 70)
        app.selectbox[0].select(percentage).run()
        assert not app.exception and len(calls) == 1
        actual = app.dataframe[0].value
        assert len(actual) == expected and actual.Priorizado.all()
        pd.testing.assert_frame_equal(
            actual.drop(columns="Priorizado").rename_axis(ordered.index.name),
            ordered.iloc[:expected]
        )
        pd.testing.assert_frame_equal(app.session_state["ranking"], ordered)
        assert [(metric.label, metric.value) for metric in app.metric][-4:] == historical
        assert len(app.get("vega_lite_chart")) == 2
        assert sum(str(item.proto).count("<path ") for item in app.get("iframe")) == 76
        if percentage != 10:
            assert [str(item.proto) for item in app.get("iframe")] != maps
        assert not any("score" in column.lower() or "probab" in column.lower() for column in actual)
    restarted = AppTest.from_file(ROOT / entrypoint, default_timeout=15).run()
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


@pytest.mark.parametrize(("available", "eligible"), [(0, 0), (5, 5), (74, 70)])
def test_insufficient_eligible_warning(demo_context, available, eligible) -> None:
    """La UI informa la limitación y mantiene visibles los excluidos con su motivo."""
    frames = {month: context(demo_context, month) for month in ORIGINS}
    frames[ORIGINS[-1]].loc[available:, f"{COUNTS[0]}_lag1"] = pd.NA
    write_context(Path(os.environ["SATD_DEMO_CONTEXT_DIR"]), demo_context, frames=frames)
    app = AppTest.from_file(ROOT / "demo/app.py", default_timeout=15).run()
    click(app, "Cargar muestra artificial")
    click(app, "Calcular prioridades T+2")
    initial_maps = "".join(item.proto.srcdoc for item in app.get("iframe"))
    assert initial_maps.count('fill="#155d4b"') == min(8, eligible)
    assert initial_maps.count('fill="#87c6ad"') == max(eligible - 8, 0)
    assert initial_maps.count('fill="#d3dce1"') == 76 - eligible
    app.selectbox[0].select(100).run()
    assert not app.exception and len(app.dataframe[0].value) == eligible
    assert app.dataframe[0].value.Priorizado.all()
    assert any(f"se seleccionan {eligible}" in warning.value for warning in app.warning)
    assert any(f"Faltan {76 - eligible}" in warning.value for warning in app.warning)
    svg = "".join(item.proto.srcdoc for item in app.get("iframe"))
    assert svg.count("<path ") == 76
    assert svg.count('fill="#d3dce1"') == 76 - eligible
    excluded = app.dataframe[1].value
    assert len(excluded) == 76 - eligible
    assert excluded.Resultado.eq("Exceso en el mes de origen").sum() == 6
    assert excluded.Resultado.eq("Predictores incompletos").sum() == 70 - eligible


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


def test_downloads_are_same_upload_ready_resource(demo_context, monkeypatch):
    """Ambos botones usan los mismos bytes artificiales del último mes y nombre."""
    downloads = {}
    uploads = []
    original = st.download_button
    parse = inferencia.parse_upload

    def capture_upload(data, suffix, cities):
        """Observar los bytes de la carga integrada en el parser habitual."""
        uploads.append(data)
        return parse(data, suffix, cities)

    def capture(label, **kwargs):
        """Observar el recurso servido conservando el renderizado nativo."""
        downloads[label] = (kwargs["data"], kwargs["file_name"])
        return original(label, **kwargs)

    monkeypatch.setattr(st, "download_button", capture)
    monkeypatch.setattr(inferencia, "parse_upload", capture_upload)
    app = AppTest.from_file(ROOT / "demo/app.py").run()
    click(app, "Cargar muestra artificial")
    first = downloads["Descargar plantilla CSV"]
    assert first == downloads["Descargar muestra artificial"]
    assert first == (sample_csv(ORIGINS[-1]), SAMPLE_FILENAME)
    assert SAMPLE_FILENAME == "muestra-artificial.csv"
    month, counts, summary = parse_upload(first[0], ".csv", geography().index)
    assert month == "2025-10" and len(counts) == 76
    assert summary["Notificaciones"] == 55 and summary["Municipios con casos"] == 8
    assert uploads == [first[0]]
    click(app, "Calcular prioridades T+2")
    assert not app.exception and not app.error
    assert app.dataframe[0].value.Priorizado.sum() == 8
    pd.testing.assert_frame_equal(
        app.session_state["ranking"],
        inferencia.ranking(demo_context, month, counts, context(demo_context, month)),
    )


@pytest.mark.parametrize("corruption", [None, b"{invalid", b"{}"])
def test_scientific_support_expander_error_keeps_ranking(
    demo_context, monkeypatch, tmp_path, corruption,
):
    """Respaldo ausente o corrupto informa un error local; el ranking permanece disponible."""
    app = AppTest.from_file(ROOT / "demo/app.py").run()
    click(app, "Cargar muestra artificial")
    click(app, "Calcular prioridades T+2")
    ordered = app.session_state["ranking"].copy()
    path = tmp_path / "invalid-support.json"
    if corruption is not None:
        path.write_bytes(corruption)
    monkeypatch.setattr(respaldo_cientifico, "SUPPORT_PATH", path)
    app.selectbox[0].select(25).run()
    assert not app.exception and len(app.error) == 1
    assert "respaldo científico" in app.error[0].value
    science = next(item for item in app.expander if item.label == "Respaldo científico del modelo")
    assert len(science.error) == 1 and science.error[0] is app.error[0]
    assert not science.proto.expanded
    assert not science.proto.id  # Apertura local en el navegador, sin widget que provoque rerun.
    assert len(app.dataframe[0].value) == 19 and len(app.get("iframe")) == 2
    pd.testing.assert_frame_equal(app.session_state["ranking"], ordered)
    assert not app.get("vega_lite_chart") and len(app.metric) == 8


def test_comparison_channel_capacity_expander(demo_context, monkeypatch) -> None:
    """La comparación renderiza la unión y tarjetas, sin un segundo scoring al cambiar cupos."""
    calls = []
    score = type(demo_context).score

    def counted(self, frame):
        calls.append(len(frame))
        return score(self, frame)

    monkeypatch.setattr(type(demo_context), "score", counted)
    app = AppTest.from_file(ROOT / "demo/app.py", default_timeout=15).run()
    assert not any(e.label == "Comparación de prioridades del mes" for e in app.expander)
    click(app, "Cargar muestra artificial")
    click(app, "Calcular prioridades T+2")
    ordered = app.session_state["ranking"].copy()
    historical = [(m.label, m.value) for m in app.metric][-4:]
    _, counts, _ = parse_upload(sample_csv(ORIGINS[-1]), ".csv", geography().index)
    potential = sorted(
        counts.index[counts[COUNTS[0]].gt(0) & ordered["Posición"].notna().reindex(counts.index)]
    )
    assert len(potential) == 2  # Seis municipios exceden P75 en T del contexto artificial.
    for percentage in (10, 5, 100, 10):
        app.selectbox[0].select(percentage).run()
        assert not app.exception and not app.error and len(calls) == 1
        comparison = next(
            e for e in app.expander if e.label == "Comparación de prioridades del mes"
        )
        science = next(e for e in app.expander if e.label == "Respaldo científico del modelo")
        assert not comparison.proto.expanded and not comparison.proto.id
        assert not comparison.get("vega_lite_chart") and len(comparison.metric) == 3
        assert len(science.get("vega_lite_chart")) == 2 and len(science.metric) == 4
        nodes = list(app.main)
        excluded = next(e for e in app.expander if e.label == "Municipios no elegibles")
        assert nodes.index(excluded) < nodes.index(comparison) < nodes.index(science)
        table = comparison.dataframe[0].value
        model = set(app.dataframe[0].value.index)
        channel = set(potential[:capacity(percentage)])
        assert set(table.index) == model | channel
        assert table.index[table["Alerta canal"]].tolist() == [
            c for c in table.index if c in channel
        ]
        assert [(m.label, m.value) for m in comparison.metric] == [
            ("Coinciden", str(len(model & channel))),
            ("Solo modelo", str(len(model - channel))),
            ("Solo canal", str(len(channel - model))),
        ]
        assert sum(int(m.value) for m in comparison.metric) == len(table)
        assert table["Posición modelo"].tolist() == ordered.loc[table.index, "Posición"].tolist()
        assert list(table) == [
            "Municipio", "Departamento", "Posición modelo", "Alerta canal", "Comparación",
        ]
        assert comparison.markdown[0].value == (
            "Compara los municipios priorizados por el modelo y las alertas generadas por el "
            "canal endémico con la información cargada. No determina cuál método acertará, "
            "porque aún no se conocen los desenlaces de T+2."
        )
        assert comparison.caption[-1].value == (
            "Esta comparación describe las listas generadas con los datos cargados; "
            "no mide aciertos ni desempeño."
        )
        assert any(f"Alertas del canal: {len(channel)}." in c.value for c in comparison.caption)
        assert [(m.label, m.value) for m in app.metric][-4:] == historical
        pd.testing.assert_frame_equal(app.session_state["ranking"], ordered)


@pytest.mark.parametrize("defect", ["column", "value"])
def test_comparison_expander_context_error_is_isolated(demo_context, monkeypatch, defect) -> None:
    """Un P75 inaccesible para comparar no invalida resultados ni respaldo histórico."""
    original = inferencia.compare_priorities

    def incomplete(ordered, counts, context, percentage):
        frame = context.copy()
        if defect == "column":
            frame = frame.drop(columns="p75_h5_t2")
        else:
            frame.loc[0, "p75_h5_t2"] = pd.NA
        return original(ordered, counts, frame, percentage)

    monkeypatch.setattr(inferencia, "compare_priorities", incomplete)
    app = AppTest.from_file(ROOT / "demo/app.py", default_timeout=15).run()
    click(app, "Cargar muestra artificial")
    click(app, "Calcular prioridades T+2")
    ordered = app.session_state["ranking"].copy()

    def forbidden(*args, **kwargs):
        pytest.fail("No se debe repetir la inferencia")

    monkeypatch.setattr(type(demo_context), "score", forbidden)
    app.selectbox[0].select(5).run()
    comparison = next(e for e in app.expander if e.label == "Comparación de prioridades del mes")
    science = next(e for e in app.expander if e.label == "Respaldo científico del modelo")
    assert not app.exception and len(app.error) == len(comparison.error) == 1
    assert app.error[0] is comparison.error[0] and not comparison.proto.expanded
    assert not comparison.dataframe and not comparison.metric
    assert len(app.dataframe[0].value) == 4 and len(app.get("iframe")) == 2
    assert not science.error and len(science.metric) == 4
    assert len(science.get("vega_lite_chart")) == 2
    pd.testing.assert_frame_equal(app.session_state["ranking"], ordered)
