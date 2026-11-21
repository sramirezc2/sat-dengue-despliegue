"""Contratos de empaquetado offline, transporte loopback y caché sin Internet."""

import hashlib
import io
import json
import stat
import threading
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from zipfile import ZIP_STORED, ZipFile, ZipInfo

import pandas as pd
import pytest
from contexto_paquete import (
    FILES,
    FORMAT,
    ORIGINS,
    ContextUnavailable,
    obtain_context,
    package_context,
)
from ejemplos import sample_csv
from inferencia import geography, load_model, parse_upload, ranking, select_capacity
from sat_dengue_pipeline.risk.configuration import procedure
from test_inferencia import context, write_context


@pytest.fixture
def model():
    """Cargar exclusivamente el modelo versionado aprobado."""
    return load_model()


@pytest.fixture
def source(tmp_path, model):
    """Crear los doce contextos artificiales con los mismos contratos del paquete real."""
    directory = tmp_path / "source"
    directory.mkdir()
    write_context(directory, model, frames={month: context(model, month) for month in ORIGINS})
    return directory


@pytest.fixture
def package(tmp_path, source, model):
    """Empaquetar datos artificiales sin consultar contexto privado ni crudos."""
    output = tmp_path / "bundle.zip"
    receipt = package_context(model, source, output)
    return output, receipt


@pytest.fixture
def server(package):
    """Servir solo bytes artificiales en loopback, sin registrar credenciales."""
    state = {
        "data": package[0].read_bytes(),
        "requests": 0,
        "require_token": False,
        "token": "artificial-server-credential",
        "redirect": False,
    }

    class Handler(BaseHTTPRequestHandler):
        """Servidor efímero del contrato HTTP, sin dependencias de un proveedor."""

        def do_GET(self) -> None:
            """Entregar el ZIP o rechazar autorización sin imprimir los encabezados."""
            state["requests"] += 1
            if state["redirect"]:
                self.send_response(302)
                self.send_header("Location", "/other-location")
                self.end_headers()
                return
            if state["require_token"] and self.headers.get("Authorization") != (
                "Bearer " + state["token"]
            ):
                self.send_response(401)
                self.end_headers()
                return
            self.send_response(200)
            self.send_header("Content-Length", str(len(state["data"])))
            self.end_headers()
            self.wfile.write(state["data"])

        def log_message(self, format, *args) -> None:
            """No emitir logs de solicitudes ni de credenciales de prueba."""

    http = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=http.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{http.server_port}/bundle.zip", state
    http.shutdown()
    http.server_close()
    thread.join(timeout=3)


def configure_download(monkeypatch, tmp_path, url: str, digest: str) -> Path:
    """Configurar un contexto ausente y una caché privada para un único test."""
    cache = tmp_path / "cache"
    monkeypatch.setenv("SATD_DEMO_CONTEXT_DIR", str(tmp_path / "absent"))
    monkeypatch.setenv("SATD_DEMO_CONTEXT_CACHE_DIR", str(cache))
    monkeypatch.setenv("SATD_DEMO_CONTEXT_BUNDLE_URL", url)
    monkeypatch.setenv("SATD_DEMO_CONTEXT_BUNDLE_SHA256", digest)
    return cache


def test_package_is_deterministic_and_receipt_is_minimal(source, package, model, tmp_path) -> None:
    """Los mismos bytes producen el mismo ZIP; solo el recibo contiene la fecha UTC."""
    second = tmp_path / "second.zip"
    receipt = package_context(model, source, second)
    assert second.read_bytes() == package[0].read_bytes()
    assert receipt["package_sha256"] == package[1]["package_sha256"]
    assert receipt["origins"] == list(ORIGINS) and receipt["municipalities"] == 76
    assert receipt["format"] == FORMAT
    assert set(receipt) == {
        "format",
        "model_sha256",
        "raw_manifest_sha256",
        "origins",
        "municipalities",
        "package_sha256",
        "generated_at",
    }
    assert "+00:00" in receipt["generated_at"] and str(tmp_path) not in json.dumps(receipt)
    with ZipFile(second) as archive:
        assert set(archive.namelist()) == set(FILES)
        assert all(info.date_time == (1980, 1, 1, 0, 0, 0) for info in archive.infolist())


@pytest.mark.parametrize("kind", ["missing-month", "wrong-population", "csv-tamper", "release"])
def test_packaging_rejects_invalid_context(source, model, tmp_path, kind) -> None:
    """No crear un paquete con cobertura insuficiente, datos alterados o release ajeno."""
    index_path = source / "contexto.json"
    index = json.loads(index_path.read_bytes())
    first = ORIGINS[0]
    path = source / f"contexto-{first}.csv"
    if kind == "missing-month":
        del index["files"][first]
    elif kind == "wrong-population":
        data = context(model, first).iloc[:-1].to_csv(index=False).encode()
        path.write_bytes(data)
        index["files"][first] = hashlib.sha256(data).hexdigest()
    elif kind == "csv-tamper":
        path.write_bytes(path.read_bytes() + b"\n")
    else:
        index["raw_manifest_sha256"] = "0" * 64
    index_path.write_text(json.dumps(index), encoding="utf-8")
    with pytest.raises(ValueError):
        package_context(model, source, tmp_path / "invalid.zip")
    assert not (tmp_path / "invalid.zip").exists()


def test_local_valid_context_takes_precedence(source, model, monkeypatch) -> None:
    """Con contexto local válido no se consulta ni se exige una URL o hash remoto."""
    monkeypatch.setenv("SATD_DEMO_CONTEXT_DIR", str(source))
    monkeypatch.setenv("SATD_DEMO_CONTEXT_BUNDLE_URL", "invalid-remote-source")
    assert set(obtain_context(model)) == set(ORIGINS)


def test_local_invalid_context_does_not_fall_back(
    source, model, server, package, monkeypatch, tmp_path
) -> None:
    """Un directorio presente pero corrupto falla cerrado sin usar otra fuente."""
    url, state = server
    configure_download(monkeypatch, tmp_path, url, package[1]["package_sha256"])
    monkeypatch.setenv("SATD_DEMO_CONTEXT_DIR", str(source))
    (source / f"contexto-{ORIGINS[0]}.csv").write_bytes(b"corrupt")
    with pytest.raises(ContextUnavailable):
        obtain_context(model, allow_test_http=True)
    assert state["requests"] == 0


def test_download_cache_restart_and_inference(
    model, server, package, monkeypatch, tmp_path
) -> None:
    """Una descarga basta; otro arranque usa caché íntegra y conserva ranking/selección."""
    url, state = server
    cache = configure_download(monkeypatch, tmp_path, url, package[1]["package_sha256"])
    first = obtain_context(model, allow_test_http=True)
    monkeypatch.delenv("SATD_DEMO_CONTEXT_BUNDLE_URL")
    second = obtain_context(model, allow_test_http=True)
    assert state["requests"] == 1 and set(first) == set(ORIGINS)
    assert (cache / package[1]["package_sha256"] / "bundle.zip").read_bytes() == package[
        0
    ].read_bytes()
    pd.testing.assert_frame_equal(first[ORIGINS[-1]], second[ORIGINS[-1]])
    month, counts, _ = parse_upload(sample_csv(ORIGINS[-1]), ".csv", geography().index)
    ordered = ranking(model, month, counts, second[month])
    for percentage, expected in [(5, 4), (10, 8), (15, 12), (20, 16)]:
        result = select_capacity(ordered, percentage)
        assert result.Priorizado.sum() == expected
        pd.testing.assert_series_equal(result["Posición"], ordered["Posición"])
    assert procedure()["budget"] == 8


@pytest.mark.parametrize("kind", ["external-hash", "bad-zip", "internal-hash", "other-release"])
def test_bad_download_is_not_installed_or_kept(
    model, server, package, monkeypatch, tmp_path, kind
) -> None:
    """No conservar descargas con hash externo/interno inválido, ZIP roto o release ajeno."""
    url, state = server
    digest = package[1]["package_sha256"]
    if kind == "external-hash":
        digest = "0" * 64
    elif kind == "bad-zip":
        state["data"] = b"not a zip"
        digest = hashlib.sha256(state["data"]).hexdigest()
    else:

        def change(name, data):
            """Alterar el índice o un CSV dentro de un paquete de prueba con hash válido."""
            if kind == "internal-hash" and name == f"contexto-{ORIGINS[0]}.csv":
                return data + b"\n"
            if kind == "other-release" and name == "contexto.json":
                index = json.loads(data)
                index["raw_manifest_sha256"] = "0" * 64
                return json.dumps(index).encode()
            return data

        state["data"] = rewrite_zip(state["data"], change=change)
        digest = hashlib.sha256(state["data"]).hexdigest()
    cache = configure_download(monkeypatch, tmp_path, url, digest)
    with pytest.raises(ContextUnavailable):
        obtain_context(model, allow_test_http=True)
    assert not list(cache.iterdir())


def rewrite_zip(data: bytes, *, extra: ZipInfo | None = None, change=None) -> bytes:
    """Crear un ZIP adversarial a partir de un paquete artificial válido."""
    output = io.BytesIO()
    with ZipFile(io.BytesIO(data)) as original, ZipFile(output, "w", ZIP_STORED) as altered:
        for info in original.infolist():
            content = original.read(info.filename)
            if extra and info.filename == extra.filename:
                continue
            altered.writestr(info, change(info.filename, content) if change else content)
        if extra:
            altered.writestr(extra, b"target")
    return output.getvalue()


@pytest.mark.parametrize("name", ["../escape", "/absolute", "C:\\escape", "symlink"])
def test_archive_rejects_escape_and_links(model, server, monkeypatch, tmp_path, name) -> None:
    """Ningún miembro no permitido o enlace puede salir de la extracción temporal."""
    url, state = server
    entry = ZipInfo(f"contexto-{ORIGINS[0]}.csv" if name == "symlink" else name)
    if name == "symlink":
        entry.create_system = 3
        entry.external_attr = (stat.S_IFLNK | 0o777) << 16
    state["data"] = rewrite_zip(state["data"], extra=entry)
    digest = hashlib.sha256(state["data"]).hexdigest()
    cache = configure_download(monkeypatch, tmp_path, url, digest)
    with pytest.raises(ContextUnavailable):
        obtain_context(model, allow_test_http=True)
    assert not list(cache.iterdir()) and not (tmp_path / "escape").exists()


def test_cached_context_tamper_is_rejected(model, server, package, monkeypatch, tmp_path) -> None:
    """Alterar índice y CSV juntos no elude la identidad externa de la caché."""
    url, state = server
    cache = configure_download(monkeypatch, tmp_path, url, package[1]["package_sha256"])
    obtain_context(model, allow_test_http=True)
    folder = cache / package[1]["package_sha256"] / "context"
    csv_path = folder / f"contexto-{ORIGINS[0]}.csv"
    csv_path.write_bytes(csv_path.read_bytes() + b"\n")
    index_path = folder / "contexto.json"
    index = json.loads(index_path.read_bytes())
    index["files"][ORIGINS[0]] = hashlib.sha256(csv_path.read_bytes()).hexdigest()
    index_path.write_text(json.dumps(index), encoding="utf-8")
    with pytest.raises(ContextUnavailable):
        obtain_context(model, allow_test_http=True)
    assert state["requests"] == 1


def test_authorization_and_errors_do_not_expose_secrets(
    model, server, package, monkeypatch, tmp_path, caplog
) -> None:
    """Sin token hay error controlado; Bearer funciona y no aparece en errores/recibos."""
    url, state = server
    state["require_token"] = True
    configure_download(
        monkeypatch,
        tmp_path,
        url + "?signature=artificial-private-query",
        package[1]["package_sha256"],
    )
    with pytest.raises(ContextUnavailable) as missing:
        obtain_context(model, allow_test_http=True)
    monkeypatch.setenv("SATD_DEMO_CONTEXT_TOKEN", state["token"])
    assert set(obtain_context(model, allow_test_http=True)) == set(ORIGINS)
    monkeypatch.setenv("SATD_DEMO_CONTEXT_CACHE_DIR", str(tmp_path / "another-cache"))
    state["token"] = "other-artificial-credential"
    with pytest.raises(ContextUnavailable) as denied:
        obtain_context(model, allow_test_http=True)
    for error in [missing.value, denied.value]:
        assert error.__context__ is None and error.__cause__ is None
        formatted = "".join(traceback.format_exception(error))
        assert "artificial-server-credential" not in formatted
        assert "artificial-private-query" not in formatted and url not in formatted
    assert "artificial-server-credential" not in caplog.text
    assert "artificial-private-query" not in json.dumps(package[1])


def test_http_is_test_only_and_redirects_are_blocked(
    model, server, package, monkeypatch, tmp_path
) -> None:
    """La UI no admite HTTP y nunca reenvía credenciales mediante redirecciones."""
    url, state = server
    configure_download(monkeypatch, tmp_path, url, package[1]["package_sha256"])
    with pytest.raises(ContextUnavailable):
        obtain_context(model)
    assert state["requests"] == 0
    state["redirect"] = True
    monkeypatch.setenv("SATD_DEMO_CONTEXT_TOKEN", state["token"])
    with pytest.raises(ContextUnavailable):
        obtain_context(model, allow_test_http=True)
    assert state["requests"] == 1


def test_download_limit_is_enforced(model, server, package, monkeypatch, tmp_path) -> None:
    """Un límite de transporte impide guardar o extraer bytes excesivos."""
    import contexto_paquete

    url, _ = server
    cache = configure_download(monkeypatch, tmp_path, url, package[1]["package_sha256"])
    monkeypatch.setattr(contexto_paquete, "MAX_DOWNLOAD", 100)
    with pytest.raises(ContextUnavailable):
        obtain_context(model, allow_test_http=True)
    assert not list(cache.iterdir())


def test_corrupt_cached_package_is_discarded(model, server, package, monkeypatch, tmp_path) -> None:
    """No conservar un ZIP corrupto de caché ni iniciar una descarga silenciosa al fallar."""
    url, state = server
    cache = configure_download(monkeypatch, tmp_path, url, package[1]["package_sha256"])
    obtain_context(model, allow_test_http=True)
    archive = cache / package[1]["package_sha256"] / "bundle.zip"
    archive.write_bytes(b"corrupt cached package")
    with pytest.raises(ContextUnavailable):
        obtain_context(model, allow_test_http=True)
    assert not archive.exists() and state["requests"] == 1


def test_packaging_excludes_unrelated_private_files(source, model, tmp_path) -> None:
    """El paquete nunca incluye archivos ajenos al índice y la allowlist del formato."""
    (source / "raw-source.csv").write_bytes(b"unrelated artificial source")
    output = tmp_path / "whitelist.zip"
    package_context(model, source, output)
    with ZipFile(output) as archive:
        assert set(archive.namelist()) == set(FILES)


def test_streamlit_bootstrap_caches_across_interactions_and_restart(
    model, server, package, monkeypatch, tmp_path
) -> None:
    """La UI usa una descarga y un scoring, incluso tras varios cambios de capacidad."""
    import contexto_paquete
    import streamlit as st
    from configuracion import ROOT
    from streamlit.testing.v1 import AppTest
    from test_app import click

    url, state = server
    configure_download(monkeypatch, tmp_path, url, package[1]["package_sha256"])
    original = obtain_context
    calls = []
    score = type(model).score

    def local_bootstrap(frozen):
        """Habilitar solo en esta prueba el servidor loopback del transporte real."""
        return original(frozen, allow_test_http=True)

    def counted(frozen, matrix):
        """Observar llamadas reales al scoring congelado desde Streamlit."""
        calls.append(len(matrix))
        return score(frozen, matrix)

    monkeypatch.setattr(contexto_paquete, "obtain_context", local_bootstrap)
    monkeypatch.setattr(type(model), "score", counted)
    st.cache_resource.clear()
    try:
        app = AppTest.from_file(ROOT / "demo/app.py", default_timeout=15).run()
        assert not app.exception and not app.error and state["requests"] == 1
        click(app, "Cargar muestra artificial")
        click(app, "Calcular prioridades T+2")
        for percentage in (5, 15, 20, 10):
            app.selectbox[0].select(percentage).run()
            assert not app.exception and state["requests"] == 1 and len(calls) == 1
        st.cache_resource.clear()
        restarted = AppTest.from_file(ROOT / "demo/app.py", default_timeout=15).run()
        assert not restarted.exception and not restarted.error
        assert state["requests"] == 1 and len(calls) == 1
    finally:
        st.cache_resource.clear()
