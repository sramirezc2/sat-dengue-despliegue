"""Empaquetar contexto ya construido y obtenerlo de una fuente HTTPS verificada.

Uso offline: python demo/contexto_paquete.py --source DIRECTORIO --output PAQUETE.zip
No adquiere crudos, construye predictores, entrena ni ejecuta Kedro.
"""

import argparse
import hashlib
import io
import json
import os
import re
import stat
import tempfile
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from http.client import HTTPException
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZIP_STORED, BadZipFile, ZipFile, ZipInfo
from zlib import error as CompressionError

import pandas as pd
from configuracion import CONTEXT_DIR, ROOT, resource_directory, resource_file
from httpx2 import HTTPError
from huggingface_hub import hf_hub_download
from huggingface_hub.errors import HfHubHTTPError
from inferencia import ARTIFACT_SHA256, POPULATION, load_context, load_model
from sat_dengue_pipeline.risk.frozen import FrozenLogistic

ORIGINS = ("2024-11", "2024-12", *(f"2025-{month:02d}" for month in range(1, 11)))
FORMAT = "satd-demo-context-v1"
CACHE_DIR = ROOT / "pipeline/data/demo-context-cache"
MAX_DOWNLOAD = 16 * 1024**2
MAX_EXPANDED = 32 * 1024**2
FILES = ("bundle.json", "contexto.json", *(f"contexto-{month}.csv" for month in ORIGINS))


class ContextUnavailable(ValueError):
    """Error público de contexto sin credenciales, URL ni rutas del servidor."""


def _metadata(model: FrozenLogistic) -> dict:
    """Describir únicamente formato, identidad aprobada y cobertura del paquete."""
    if model.artifact_sha256 != ARTIFACT_SHA256:
        raise ContextUnavailable("El modelo del paquete no corresponde a la identidad aprobada.")
    return {
        "format": FORMAT,
        "model_sha256": ARTIFACT_SHA256,
        "raw_manifest_sha256": model.payload["provenance"]["raw_manifest_sha256"],
        "origins": list(ORIGINS),
        "municipalities": POPULATION,
    }


def complete_context(model: FrozenLogistic, directory: Path) -> dict[str, pd.DataFrame]:
    """Verificar con el cargador existente los doce orígenes y sus 76 municipios."""
    contexts = load_context(model, directory)
    if set(contexts) != set(ORIGINS):
        raise ContextUnavailable("El contexto requiere los doce meses de 2024-11 a 2025-10.")
    return contexts


def _archive_files(package: Path, expected_sha: str, model: FrozenLogistic) -> dict[str, bytes]:
    """Verificar hash externo e inventario antes de interpretar o extraer el ZIP."""
    with package.open("rb") as stream:
        raw = stream.read(MAX_DOWNLOAD + 1)
    if len(raw) > MAX_DOWNLOAD:
        raise ContextUnavailable("El paquete de contexto supera el límite de tamaño.")
    if hashlib.sha256(raw).hexdigest() != expected_sha:
        raise ContextUnavailable("El SHA-256 externo del contexto no coincide.")
    with ZipFile(io.BytesIO(raw)) as archive:
        entries = archive.infolist()
        if len(entries) != len(FILES) or {entry.filename for entry in entries} != set(FILES):
            raise ContextUnavailable(
                "Inventario inválido: solo se admiten los archivos del contexto."
            )
        if sum(entry.file_size for entry in entries) > MAX_EXPANDED:
            raise ContextUnavailable("El contexto expandido supera el límite de tamaño.")
        files = {}
        for entry in entries:
            # La allowlist exacta también excluye rutas absolutas, '..', unidades y '\\'.
            kind = stat.S_IFMT(entry.external_attr >> 16)
            if (
                kind not in {0, stat.S_IFREG}
                or entry.is_dir()
                or entry.flag_bits & 1
                or entry.compress_type not in {ZIP_STORED, ZIP_DEFLATED}
            ):
                raise ContextUnavailable("El paquete contiene enlaces o archivos no admitidos.")
            with archive.open(entry) as stream:
                data = stream.read(MAX_EXPANDED + 1)
            if len(data) != entry.file_size or len(data) > MAX_EXPANDED:
                raise ContextUnavailable("Tamaño de archivo de contexto inválido.")
            files[entry.filename] = data
    if json.loads(files["bundle.json"]) != _metadata(model):
        raise ContextUnavailable("Formato, cobertura o release del paquete incompatibles.")
    return files


def _write_files(files: dict[str, bytes], directory: Path) -> None:
    """Escribir exclusivamente archivos de la allowlist en un directorio temporal privado."""
    directory.mkdir(mode=0o700)
    for name, data in files.items():
        if name not in FILES:
            raise ContextUnavailable("Nombre de archivo de contexto no admitido.")
        with (directory / name).open("xb") as stream:
            stream.write(data)
        (directory / name).chmod(0o600)


def package_context(model: FrozenLogistic, source: Path, output: Path) -> dict:
    """Crear un ZIP determinista y un recibo de identidad sin rutas ni secretos.

    Args:
        model: Modelo aprobado cargado mediante load_model.
        source: Directorio con índice y doce CSV previamente construidos offline.
        output: Paquete nuevo; nunca sobrescribe un paquete o recibo existente.

    Returns:
        Recibo con identidad, hash externo y fecha UTC; la fecha queda fuera del ZIP.
    """
    source = resource_directory("SATD_DEMO_CONTEXT_DIR", CONTEXT_DIR, source)
    complete_context(model, source)
    parent = resource_directory("Salida offline", output.parent, output.parent, create=True)
    output = parent / output.name
    receipt_path = output.with_suffix(".manifest.json")
    if output.exists() or output.is_symlink() or receipt_path.exists() or receipt_path.is_symlink():
        raise ContextUnavailable("El paquete o recibo de salida ya existe.")
    with tempfile.TemporaryDirectory(prefix=".pack-", dir=parent) as temporary:
        work = Path(temporary)
        package = work / "bundle.zip"
        with ZipFile(package, "w", compression=ZIP_STORED) as archive:
            for name in sorted(FILES):
                data = (
                    json.dumps(_metadata(model), sort_keys=True, separators=(",", ":")).encode()
                    if name == "bundle.json"
                    else resource_file(source, name).read_bytes()
                )
                entry = ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                entry.create_system = 3
                entry.external_attr = (stat.S_IFREG | 0o600) << 16
                archive.writestr(entry, data)
        package.chmod(0o600)
        digest = hashlib.sha256(package.read_bytes()).hexdigest()
        _write_files(_archive_files(package, digest, model), work / "context")
        complete_context(model, work / "context")
        receipt = {
            **_metadata(model),
            "package_sha256": digest,
            "generated_at": datetime.now(UTC).isoformat(),
        }
        receipt_temp = work / "manifest.json"
        receipt_temp.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        receipt_temp.chmod(0o600)
        os.replace(package, output)
        os.replace(receipt_temp, receipt_path)
    return receipt


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """No reenviar credenciales ni URL firmadas a un destino de redirección."""

    def redirect_request(
        self, req: urllib.request.Request, fp: object, code: int,
        msg: str, headers: object, newurl: str,
    ) -> None:
        """Rechazar toda redirección; el operador debe configurar la URL final."""
        return None


def _download(url: str, token: str | None, output: Path, *, allow_test_http: bool) -> None:
    """Descargar con TLS, límite de tamaño y errores sin valores privados."""
    parsed = urllib.parse.urlsplit(url)
    local_test = (
        allow_test_http
        and parsed.scheme == "http"
        and parsed.hostname in {"127.0.0.1", "localhost", "::1"}
    )
    if (
        (parsed.scheme != "https" and not local_test)
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.fragment
    ):
        raise ContextUnavailable("El paquete requiere una URL HTTPS sin credenciales incrustadas.")
    headers = {"Accept": "application/zip"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    opener = urllib.request.build_opener(_NoRedirect())
    with opener.open(request, timeout=15) as response, output.open("xb") as stream:
        if response.status != 200:
            raise ContextUnavailable("El servidor no entregó el paquete de contexto.")
        output.chmod(0o600)
        size = 0
        while data := response.read(64 * 1024):
            size += len(data)
            if size > MAX_DOWNLOAD:
                raise ContextUnavailable("El paquete de contexto supera el límite de tamaño.")
            stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def _cached_context(model: FrozenLogistic, cache: Path, digest: str) -> dict[str, pd.DataFrame]:
    """Revalidar ZIP y extracción; detectar incluso un índice y CSV alterados juntos."""
    cache = resource_directory("Caché de contexto", cache, cache)
    package = resource_file(cache, "bundle.zip")
    try:
        files = _archive_files(package, digest, model)
    except (ValueError, KeyError, TypeError, BadZipFile, CompressionError):
        # Solo el ZIP de esta entrada privada de caché; nunca el contexto offline del operador.
        package.unlink()
        raise
    directory = resource_directory("Contexto extraído", cache / "context", cache / "context")
    for name, expected in files.items():
        if resource_file(directory, name).read_bytes() != expected:
            raise ContextUnavailable("El contexto de caché difiere del paquete verificado.")
    return complete_context(model, directory)


def _download_hugging_face(output: Path) -> None:
    """Obtener un Dataset público en una revisión inmutable, sin credenciales.

    La caché propia recibe una copia regular: el cliente del Hub puede devolver
    enlaces internos de su caché, que nunca se extraen ni se modifican.
    """
    repo = os.environ.get("SATD_DEMO_HF_REPO_ID", "")
    revision = os.environ.get("SATD_DEMO_HF_REVISION", "")
    filename = os.environ.get("SATD_DEMO_HF_FILENAME", "context-real-v1.zip")
    if (
        re.fullmatch(r"[\w.-]+/[\w.-]+", repo) is None
        or re.fullmatch(r"[0-9a-f]{40}", revision) is None
        or filename != "context-real-v1.zip"
    ):
        raise ContextUnavailable("Configure el Dataset público y su revisión completa.")
    downloaded = Path(hf_hub_download(
        repo_id=repo, repo_type="dataset", filename=filename,
        revision=revision, token=False,
    ))
    with downloaded.open("rb") as source, output.open("xb") as target:
        data = source.read(MAX_DOWNLOAD + 1)
        if len(data) > MAX_DOWNLOAD:
            raise ContextUnavailable("El paquete de contexto supera el límite de tamaño.")
        target.write(data)
    output.chmod(0o600)


def obtain_context(
    model: FrozenLogistic, *, allow_test_http: bool = False
) -> dict[str, pd.DataFrame]:
    """Usar directorio local o instalar una sola vez un paquete verificado en caché.

    Args:
        model: Modelo aprobado; fija la identidad del release esperado.
        allow_test_http: Solo para servidor loopback de las pruebas; la UI nunca lo activa.

    Returns:
        Los doce contextos verificados. Una fuente local o caché corrupta falla cerrada.
    """
    try:
        local = resource_directory("SATD_DEMO_CONTEXT_DIR", CONTEXT_DIR, required=False)
        if local.exists():
            return complete_context(model, local)
        url = os.environ.get("SATD_DEMO_CONTEXT_BUNDLE_URL", "")
        digest = os.environ.get("SATD_DEMO_CONTEXT_BUNDLE_SHA256", "")
        if re.fullmatch(r"[0-9a-f]{64}", digest) is None:
            raise ContextUnavailable("Configure el SHA-256 del contexto privado.")
        cache = resource_directory("SATD_DEMO_CONTEXT_CACHE_DIR", CACHE_DIR, create=True)
        installed = cache / digest
        if installed.exists() or installed.is_symlink():
            return _cached_context(model, installed, digest)
        if not url and not os.environ.get("SATD_DEMO_HF_REPO_ID"):
            raise ContextUnavailable("Configure la URL del contexto privado.")
        with tempfile.TemporaryDirectory(prefix=".download-", dir=cache) as temporary:
            staging = Path(temporary)
            package = staging / "bundle.zip"
            if os.environ.get("SATD_DEMO_HF_REPO_ID"):
                if url:
                    raise ContextUnavailable("Configure una sola fuente remota de contexto.")
                _download_hugging_face(package)
            else:
                _download(
                    url, os.environ.get("SATD_DEMO_CONTEXT_TOKEN"), package,
                    allow_test_http=allow_test_http,
                )
            _write_files(_archive_files(package, digest, model), staging / "context")
            contexts = complete_context(model, staging / "context")
            # Otra instancia puede haber terminado la misma instalación mientras se descargaba.
            if installed.exists():
                return _cached_context(model, installed, digest)
            os.replace(staging, installed)
            return contexts
    except (
        OSError, ValueError, KeyError, TypeError, BadZipFile, CompressionError,
        RuntimeError, HTTPException, HTTPError, HfHubHTTPError,
    ):
        pass
    # Fuera del except: tampoco se conserva una excepción de red con URL/token en __context__.
    raise ContextUnavailable(
        "Contexto privado no disponible o inválido. El administrador debe revisar "
        "el directorio o la fuente remota, revisión y SHA-256 del paquete."
    )


def main() -> int:
    """Empaquetar offline sin imprimir rutas, predictores ni errores del transporte."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        receipt = package_context(load_model(), args.source, args.output)
    except (OSError, ValueError, KeyError, TypeError, BadZipFile, CompressionError, RuntimeError):
        print("No se pudo empaquetar: revise el modelo, los doce contextos y la salida nueva.")
        return 1
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
