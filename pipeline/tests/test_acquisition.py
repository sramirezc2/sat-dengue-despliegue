"""Contratos, caché e integridad usando exclusivamente archivos temporales."""

import hashlib
import io
import json
import os
from dataclasses import FrozenInstanceError, fields, replace
from pathlib import Path
from typing import Any

import pytest

from sat_dengue_pipeline.acquisition import (
    ReleaseManifest,
    ResolvedBundle,
    ResolvedFile,
    create_source,
    resolve_release,
)
from sat_dengue_pipeline.acquisition.errors import (
    CacheError,
    DownloadError,
    IntegrityError,
    ManifestError,
    MutableRevisionError,
    SourceFileNotFoundError,
    UnknownProviderError,
)

CONTENT = b"synthetic-fixture-2018-2024\n"


@pytest.fixture
def manifest_data(tmp_path: Path) -> dict[str, Any]:
    """Crear declaración y contenido artificiales; no representan un release real.

    Args:
        tmp_path: Directorio temporal de la prueba.

    Returns:
        Manifiesto serializable con hashes calculados del contenido artificial.
    """
    origin = tmp_path / "origin"
    (origin / "nested").mkdir(parents=True)
    (origin / "nested" / "fixture.txt").write_bytes(CONTENT)
    return {
        "schema_version": 1,
        "release_id": "synthetic-test-release",
        "provider": "local",
        "location": str(origin),
        "revision": "fixture-v1",
        "coverage_start": "2018-01-01",
        "coverage_end": "2024-12-31",
        "files": [
            {
                "logical_name": "fixture",
                "remote_path": "nested/fixture.txt",
                "relative_path": "inputs/fixture.txt",
                "size_bytes": len(CONTENT),
                "sha256": hashlib.sha256(CONTENT).hexdigest(),
            }
        ],
    }


def parse(data: dict[str, Any]) -> ReleaseManifest:
    """Construir el contrato por el mismo camino JSON utilizado en producción."""
    return ReleaseManifest.from_json(json.dumps(data))


def test_manifest_canonical_hash_and_neutral_immutable_bundle(
    manifest_data: dict[str, Any], tmp_path: Path
) -> None:
    """Producir un bundle sin tipos de proveedor y un digest canónico reproducible."""
    manifest = parse(manifest_data)
    reordered = dict(reversed(list(manifest_data.items())))
    assert manifest.manifest_sha256 == parse(reordered).manifest_sha256
    expected = hashlib.sha256(
        json.dumps(
            manifest_data, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode()
    ).hexdigest()
    assert manifest.manifest_sha256 == expected
    bundle = resolve_release(manifest, tmp_path / "cache", create_source(manifest))
    assert isinstance(bundle, ResolvedBundle)
    assert bundle.files[0].path.read_bytes() == CONTENT
    assert bundle.files[0].path.is_absolute()
    assert bundle.files[0].path.parts[-4:] == (
        manifest.release_id,
        manifest.manifest_sha256,
        "inputs",
        "fixture.txt",
    )
    assert {f.name for f in fields(bundle)} == {
        "release_id",
        "manifest_sha256",
        "coverage_start",
        "coverage_end",
        "files",
    }
    assert {f.name for f in fields(ResolvedFile)} == {
        "logical_name",
        "path",
        "size_bytes",
        "sha256",
    }
    with pytest.raises(FrozenInstanceError):
        bundle.release_id = "changed"  # type: ignore[misc]


@pytest.mark.parametrize(
    "changes",
    [
        {"schema_version": 2},
        {"schema_version": True},
        {"schema_version": "1"},
        {"files": []},
        {"provider": ""},
        {"location": None},
        {"revision": ""},
        {"release_id": "../escape"},
        {"coverage_start": "invalid"},
        {"coverage_end": "2017-12-31"},
        {"coverage_start": "20180101"},
        {"extra": "unknown"},
    ],
)
def test_manifest_rejects_invalid_fields(
    manifest_data: dict[str, Any], changes: dict[str, Any]
) -> None:
    """Fallar antes de descargar si el esquema o los campos son inválidos."""
    with pytest.raises(ManifestError):
        parse(manifest_data | changes)


@pytest.mark.parametrize("text", ["{}", "[]", "null", "{bad", '{"files": [4]}'])
def test_manifest_rejects_missing_or_malformed_json(text: str) -> None:
    """Rechazar declaraciones incompletas o JSON sin estructura de manifiesto."""
    with pytest.raises(ManifestError):
        ReleaseManifest.from_json(text)


@pytest.mark.parametrize(
    "field,value",
    [
        ("sha256", "not-a-hash"),
        ("sha256", "A" * 64),
        ("size_bytes", -1),
        ("size_bytes", True),
        ("size_bytes", "5"),
        ("logical_name", ""),
        ("relative_path", "/absolute"),
        ("relative_path", "../outside"),
        ("relative_path", "a/../outside"),
        ("relative_path", "a//b"),
        ("relative_path", "a/./b"),
        ("relative_path", "C:/outside"),
        ("relative_path", "a\\b"),
        ("relative_path", ""),
        ("remote_path", "/absolute"),
        ("remote_path", "../outside"),
    ],
)
def test_file_rejects_invalid_hash_size_or_path(
    manifest_data: dict[str, Any], field: str, value: Any
) -> None:
    """Validar destinos y orígenes antes de cualquier acceso al filesystem."""
    manifest_data["files"][0][field] = value
    with pytest.raises(ManifestError):
        parse(manifest_data)


@pytest.mark.parametrize(
    "changes",
    [
        {"relative_path": "different.txt"},
        {"logical_name": "second"},
        {"logical_name": "second", "relative_path": "INPUTS/FIXTURE.TXT"},
        {"logical_name": "second", "relative_path": "inputs/fixture.txt/child"},
    ],
)
def test_manifest_rejects_duplicate_names_and_conflicting_destinations(
    manifest_data: dict[str, Any], changes: dict[str, str]
) -> None:
    """Evitar alias, destinos duplicados y conflictos archivo/directorio."""
    manifest_data["files"].append(manifest_data["files"][0] | changes)
    with pytest.raises(ManifestError):
        parse(manifest_data)


def test_unknown_provider_is_rejected_by_factory(manifest_data: dict[str, Any]) -> None:
    """Concentrar la selección y el error de proveedor en la fábrica."""
    with pytest.raises(UnknownProviderError):
        create_source(parse(manifest_data | {"provider": "unknown"}))


@pytest.mark.parametrize("revision", ["main", "latest", "v1", "abc123"])
def test_huggingface_requires_full_commit(manifest_data: dict[str, Any], revision: str) -> None:
    """No aceptar ramas, etiquetas o hashes abreviados como revisión inmutable."""
    manifest = parse(
        manifest_data
        | {
            "provider": "huggingface",
            "location": "fixture-owner/fixture-dataset",
            "revision": revision,
        }
    )
    with pytest.raises(MutableRevisionError):
        create_source(manifest)


def test_valid_cache_hit_never_downloads_again(
    manifest_data: dict[str, Any], tmp_path: Path
) -> None:
    """Reutilizar solo el archivo cuyo tamaño y hash ya fueron comprobados."""
    manifest = parse(manifest_data)
    bundle = resolve_release(manifest, tmp_path / "cache", create_source(manifest))
    # El origen desaparece: un hit válido no necesita consultarlo.
    (Path(manifest.location) / manifest.files[0].remote_path).unlink()
    assert resolve_release(manifest, tmp_path / "cache", create_source(manifest)) == bundle


def test_same_size_corruption_is_rematerialized(
    manifest_data: dict[str, Any], tmp_path: Path
) -> None:
    """No confiar en el tamaño si el contenido de la caché cambió."""
    manifest = parse(manifest_data)
    source = create_source(manifest)
    bundle = resolve_release(manifest, tmp_path / "cache", source)
    bundle.files[0].path.write_bytes(b"x" * len(CONTENT))
    repaired = resolve_release(manifest, tmp_path / "cache", source)
    assert repaired.files[0].path.read_bytes() == CONTENT


@pytest.mark.parametrize(
    "changes,match",
    [
        ({"size_bytes": len(CONTENT) + 1}, "Tamaño incorrecto"),
        ({"sha256": "0" * 64}, "SHA-256 incorrecto"),
    ],
)
def test_integrity_failure_has_no_visible_partial_file(
    manifest_data: dict[str, Any], tmp_path: Path, changes: dict[str, Any], match: str
) -> None:
    """No publicar entradas que incumplan tamaño o hash, y limpiar el temporal."""
    manifest_data["files"][0].update(changes)
    manifest = parse(manifest_data)
    cache = tmp_path / "cache"
    with pytest.raises(IntegrityError, match=match):
        resolve_release(manifest, cache, create_source(manifest))
    assert not any(path.is_file() for path in cache.rglob("*"))


def test_replace_happens_only_after_integrity_validation(
    manifest_data: dict[str, Any], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Publicar desde un temporal en el mismo directorio mediante os.replace."""
    manifest = parse(manifest_data)
    original_replace = os.replace
    replaced = []

    def checked_replace(source: Path, destination: Path) -> None:
        """Verificar el archivo justo en la frontera de publicación atómica."""
        assert source.parent == destination.parent
        assert source.suffix == ".tmp"
        assert source.read_bytes() == CONTENT
        assert not destination.exists()
        replaced.append(destination)
        original_replace(source, destination)

    monkeypatch.setattr(os, "replace", checked_replace)
    resolve_release(manifest, tmp_path / "cache", create_source(manifest))
    assert len(replaced) == 1


def test_interrupted_transfer_preserves_previous_release_and_cleans_temporary(
    manifest_data: dict[str, Any], tmp_path: Path
) -> None:
    """Mantener un release válido previo al fallar la adquisición de otra revisión."""
    manifest = parse(manifest_data)
    cache = tmp_path / "cache"
    previous = resolve_release(manifest, cache, create_source(manifest))

    class InterruptedSource:
        """Fuente que simula interrupción después de escribir algunos bytes."""

        def materialize(self, file: Any, destination: Path) -> None:
            """Escribir bytes parciales y fallar sin exponer el mensaje externo."""
            destination.write_bytes(b"partial")
            raise RuntimeError("https://signed.invalid/?secret=must-not-appear")

    next_manifest = replace(manifest, revision="fixture-v2")
    with pytest.raises(DownloadError, match="Descarga interrumpida") as failure:
        resolve_release(next_manifest, cache, InterruptedSource())
    assert "secret" not in str(failure.value)
    assert previous.files[0].path.read_bytes() == CONTENT
    assert not list(cache.rglob("*.tmp"))
    next_bundle = resolve_release(next_manifest, cache, create_source(next_manifest))
    assert next_bundle.files[0].path != previous.files[0].path


def test_missing_local_file_is_explicit(manifest_data: dict[str, Any], tmp_path: Path) -> None:
    """Informar un archivo ausente sin incluir rutas ni credenciales."""
    manifest = parse(manifest_data)
    (Path(manifest.location) / manifest.files[0].remote_path).unlink()
    with pytest.raises(SourceFileNotFoundError, match="Archivo ausente"):
        resolve_release(manifest, tmp_path / "cache", create_source(manifest))


def test_source_and_cache_symlinks_cannot_escape(
    manifest_data: dict[str, Any], tmp_path: Path
) -> None:
    """Rechazar escapes por symlink aunque las rutas declaradas sean relativas."""
    manifest = parse(manifest_data)
    outside = tmp_path / "outside"
    outside.mkdir()
    cache = tmp_path / "cache"
    cache.mkdir()
    (cache / manifest.release_id).symlink_to(outside, target_is_directory=True)
    with pytest.raises(CacheError, match="escapa"):
        resolve_release(manifest, cache, create_source(manifest))
    local_file = Path(manifest.location) / manifest.files[0].remote_path
    local_file.unlink()
    local_file.symlink_to(outside / "absent.txt")
    with pytest.raises(CacheError, match="escapa"):
        resolve_release(manifest, tmp_path / "other-cache", create_source(manifest))


class FakeS3:
    """Cliente de objetos versionados completamente en memoria."""

    def __init__(self) -> None:
        """Inicializar el registro de llamadas simuladas."""
        self.calls: list[tuple[str, str]] = []

    def download_file(self, *, bucket: str, key: str, destination: Path) -> None:
        """Simular la transferencia sin importar boto3 ni consultar AWS."""
        self.calls.append((bucket, key))
        destination.write_bytes(CONTENT)


class ChunkedResponse(io.BytesIO):
    """Respuesta que impide lecturas completas y devuelve bloques pequeños."""

    def read(self, size: int = -1) -> bytes:
        """Exigir tamaños de bloque explícitos incluso para archivos pequeños."""
        assert 0 < size <= 64 * 1024
        return super().read(min(size, 3))


@pytest.mark.parametrize("provider", ["local", "huggingface", "zenodo", "s3"])
def test_all_providers_produce_equivalent_local_bundles(
    manifest_data: dict[str, Any], tmp_path: Path, provider: str
) -> None:
    """Usar la misma caché e integridad para los cuatro proveedores simulados."""
    locations = {
        "local": manifest_data["location"],
        "huggingface": "fixture-owner/fixture-dataset",
        "zenodo": "17",  # ID exclusivamente de la respuesta falsa; no es un release registrado.
        "s3": "fixture-bucket",
    }
    revisions = {"local": "fixture-v1", "huggingface": "a" * 40, "zenodo": "17", "s3": "v1"}
    manifest = parse(
        manifest_data
        | {"provider": provider, "location": locations[provider], "revision": revisions[provider]}
    )
    hub_calls = []
    http_calls = []
    s3 = FakeS3()

    def hub_download(**kwargs: Any) -> str:
        """Reemplazar el cliente oficial de Hugging Face con una copia local."""
        hub_calls.append(kwargs)
        assert kwargs["repo_type"] == "dataset"
        assert kwargs["token"] is False
        assert kwargs["revision"] == "a" * 40
        assert kwargs["filename"] == "nested/fixture.txt"
        path = Path(kwargs["cache_dir"]) / "sdk-fixture.txt"
        path.write_bytes(CONTENT)
        return str(path)

    def open_http(url: str, *, timeout: float) -> io.BytesIO:
        """Simular metadatos y descarga HTTPS, sin cliente de red real."""
        assert url.startswith("https://zenodo.org/")
        assert timeout == 30.0
        http_calls.append(url)
        if url.endswith("/api/records/17"):
            return io.BytesIO(json.dumps({"id": 17, "conceptrecid": "16"}).encode())
        assert url.endswith("/records/17/files/nested%2Ffixture.txt")
        return ChunkedResponse(CONTENT)

    source = create_source(manifest, hub_download=hub_download, open_http=open_http, s3_client=s3)
    bundle = resolve_release(manifest, tmp_path / "cache", source)
    assert isinstance(bundle, ResolvedBundle)
    assert bundle.release_id == manifest_data["release_id"]
    assert bundle.coverage_start == "2018-01-01"
    assert bundle.coverage_end == "2024-12-31"
    assert bundle.files[0].path.read_bytes() == CONTENT
    assert bundle.files[0].size_bytes == len(CONTENT)
    assert bundle.files[0].sha256 == hashlib.sha256(CONTENT).hexdigest()
    assert len(hub_calls) == (1 if provider == "huggingface" else 0)
    assert len(http_calls) == (2 if provider == "zenodo" else 0)
    assert s3.calls == ([("fixture-bucket", "v1/nested/fixture.txt")] if provider == "s3" else [])
    assert not list((tmp_path / "cache").rglob("*.tmp"))
    assert not list((tmp_path / "cache").rglob(".hf-*"))


@pytest.mark.parametrize("location,revision", [("10.5281/zenodo.concept", "17"), ("17", "latest")])
def test_zenodo_rejects_concept_doi_or_mutable_revision(
    manifest_data: dict[str, Any], location: str, revision: str
) -> None:
    """Exigir el registro versionado antes de intentar cualquier petición."""
    manifest = parse(
        manifest_data | {"provider": "zenodo", "location": location, "revision": revision}
    )
    with pytest.raises(MutableRevisionError):
        create_source(manifest)


@pytest.mark.parametrize(
    "metadata", [{"id": 18, "conceptrecid": "16"}, {"id": 17, "conceptrecid": "17"}]
)
def test_zenodo_verifies_server_record_identity(
    manifest_data: dict[str, Any], tmp_path: Path, metadata: dict[str, Any]
) -> None:
    """No aceptar que el servidor resuelva un concepto o una versión diferente."""
    manifest = parse(manifest_data | {"provider": "zenodo", "location": "17", "revision": "17"})

    def open_http(url: str, *, timeout: float) -> io.BytesIO:
        """Responder solo a la consulta de identidad del registro falso."""
        assert url.endswith("/api/records/17")
        return io.BytesIO(json.dumps(metadata).encode())

    with pytest.raises(MutableRevisionError):
        resolve_release(manifest, tmp_path / "cache", create_source(manifest, open_http=open_http))


def test_s3_requires_explicit_client(manifest_data: dict[str, Any]) -> None:
    """No inicializar boto3 ni buscar credenciales implícitamente."""
    manifest = parse(manifest_data | {"provider": "s3", "location": "fixture-bucket"})
    with pytest.raises(ManifestError, match="cliente versionado"):
        create_source(manifest)


def test_default_huggingface_adapter_calls_official_client_without_token(
    manifest_data: dict[str, Any], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Sustituir el SDK oficial en su frontera, manteniendo el wrapper real."""
    import huggingface_hub

    manifest = parse(
        manifest_data
        | {
            "provider": "huggingface",
            "location": "fixture-owner/fixture-dataset",
            "revision": "b" * 40,
        }
    )
    calls = []

    def fake_official(**kwargs: Any) -> str:
        """Devolver un archivo temporal sin invocar la red del SDK."""
        calls.append(kwargs)
        return str(Path(manifest_data["location"]) / "nested/fixture.txt")

    monkeypatch.setattr(huggingface_hub, "hf_hub_download", fake_official)
    bundle = resolve_release(manifest, tmp_path / "cache", create_source(manifest))
    assert bundle.files[0].path.read_bytes() == CONTENT
    assert calls[0]["token"] is False
    assert calls[0]["repo_type"] == "dataset"


def test_failed_repair_keeps_previous_cache_bytes_and_removes_temporary(
    manifest_data: dict[str, Any], tmp_path: Path
) -> None:
    """No reemplazar una copia existente si falla la reparación de su integridad."""
    manifest = parse(manifest_data)
    source = create_source(manifest)
    cache = tmp_path / "cache"
    bundle = resolve_release(manifest, cache, source)
    previous_bytes = b"old-content".ljust(len(CONTENT), b" ")
    bundle.files[0].path.write_bytes(previous_bytes)
    (Path(manifest.location) / manifest.files[0].remote_path).write_bytes(b"incomplete")
    with pytest.raises(IntegrityError):
        resolve_release(manifest, cache, source)
    assert bundle.files[0].path.read_bytes() == previous_bytes
    assert not list(cache.rglob("*.tmp"))


def test_boundaries_actually_block_network_and_publication() -> None:
    """Comprobar que el guard de pytest bloquea los accesos antes de realizarlos."""
    import socket

    with pytest.raises(pytest.fail.Exception, match="red"):
        socket.getaddrinfo("network-test.invalid", 443)
    with pytest.raises(AssertionError):
        (Path(__file__).resolve().parents[2] / "datos/resultados/forbidden").open("wb")


def test_resolver_runs_as_kedro_node_with_temporary_configuration(
    manifest_data: dict[str, Any], tmp_path: Path
) -> None:
    """Integrar el servicio sin registrar un pipeline que carezca de release real."""
    from kedro.io import DataCatalog, MemoryDataset
    from kedro.pipeline import Pipeline, node
    from kedro.runner import SequentialRunner

    manifest = parse(manifest_data)
    catalog = DataCatalog(
        {
            "manifest": MemoryDataset(manifest),
            "cache": MemoryDataset(tmp_path / "cache"),
            "source": MemoryDataset(create_source(manifest)),
        }
    )
    pipeline = Pipeline([node(resolve_release, ["manifest", "cache", "source"], "bundle")])
    outputs = SequentialRunner().run(pipeline, catalog)
    bundle = outputs["bundle"].load()
    assert isinstance(bundle, ResolvedBundle)
    assert bundle.files[0].path.read_bytes() == CONTENT
