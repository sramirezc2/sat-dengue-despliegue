"""Certificación N=3 en procesos/directorios nuevos, previa al consumidor."""

import json
import subprocess
import sys
import tempfile
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import TypeVar

from sat_dengue_pipeline.acquisition.contracts import ResolvedBundle

from .contract import BuildConfig
from .serialization import CanonicalArtifact, atomic_write, canonical_bytes, verify_artifact

T = TypeVar("T")


@dataclass(frozen=True)
class Reconstruction:
    """Recibo transitorio de una reconstrucción aislada."""

    artifact: CanonicalArtifact
    audit: dict
    pid: int


@dataclass(frozen=True)
class CertifiedCanonical:
    """Única salida liberada después de comparar tres reconstrucciones completas."""

    artifact: CanonicalArtifact
    hashes: tuple[str, ...]
    semantic_digests: tuple[str, ...]
    worker_pids: tuple[int, ...]
    audit: dict


def isolated_build(
    bundle: ResolvedBundle, config: BuildConfig, root: Path, inventory: dict | None
) -> Reconstruction:
    """Ejecutar un intérprete nuevo y compartir solamente referencias a crudos."""
    request = {
        "bundle": {
            **asdict(bundle),
            "files": [{**asdict(file), "path": str(file.path.resolve())} for file in bundle.files],
        },
        "config": config.payload(),
        "inventory": inventory,
    }
    path = root / "request.json"
    atomic_write(path, canonical_bytes(request))
    completed = subprocess.run(
        [sys.executable, "-m", "sat_dengue_pipeline.raw.worker", str(path)],
        capture_output=True,
        check=False,
        timeout=1200,
        cwd=root,
    )
    if completed.returncode:
        raise ValueError("La reconstrucción aislada falló; no se libera salida")
    receipt = json.loads((root / "receipt.json").read_bytes())
    artifact = CanonicalArtifact(
        root / receipt["semantic_digest"] / "canonical.json",
        receipt["semantic_digest"],
        receipt["serialized_sha256"],
    )
    verify_artifact(artifact)
    return Reconstruction(artifact, receipt["audit"], receipt["pid"])


def canonical_reproducibility(
    bundle: ResolvedBundle,
    config: BuildConfig,
    root: Path,
    inventory: dict | None = None,
    *,
    executor: Callable = isolated_build,
) -> CertifiedCanonical:
    """Reconstruir N=3 desde crudos y comparar también bytes y auditorías exactos.

    Args:
        bundle: Archivos crudos verificados nuevamente en cada proceso.
        config: Perfil científico común, sin cachear derivados.
        root: Directorio de trabajo, fuera de publicaciones.
        inventory: Contrato explícito del fixture, nunca sustituto del aprobado.
        executor: Ejecutor de procesos; permite inyectar divergencias en pruebas.

    Returns:
        Una salida certificada, únicamente si las tres reconstrucciones coinciden.
    """
    root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="n3-", dir=root) as work:
        results = []
        for repetition in range(3):
            directory = Path(work) / str(repetition)
            directory.mkdir()
            results.append(executor(bundle, config, directory, inventory))
        if len({result.pid for result in results}) != 3:
            raise ValueError("N=3 requiere procesos distintos")
        first = results[0]
        expected = verify_artifact(first.artifact)
        for result in results[1:]:
            if (
                result.artifact.semantic_digest != first.artifact.semantic_digest
                or result.artifact.serialized_sha256 != first.artifact.serialized_sha256
                or verify_artifact(result.artifact) != expected
                or result.audit != first.audit
            ):
                raise ValueError("Divergencia N=3: entrenamiento bloqueado")
        final = root / "certified" / first.artifact.semantic_digest / "canonical.json"
        atomic_write(final, expected)
        return CertifiedCanonical(
            CanonicalArtifact(
                final, first.artifact.semantic_digest, first.artifact.serialized_sha256
            ),
            tuple(result.artifact.serialized_sha256 for result in results),
            tuple(result.artifact.semantic_digest for result in results),
            tuple(result.pid for result in results),
            first.audit,
        )


def certify_then_consume(
    bundle: ResolvedBundle,
    config: BuildConfig,
    root: Path,
    consumer: Callable[[CertifiedCanonical], T],
    inventory: dict | None = None,
    *,
    executor: Callable = isolated_build,
) -> T:
    """Invocar al consumidor de entrenamiento solo después del gate N=3."""
    certificate = canonical_reproducibility(bundle, config, root, inventory, executor=executor)
    verify_artifact(certificate.artifact)
    return consumer(certificate)
