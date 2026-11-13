"""Identidad inmutable aprobada y confinamiento al worktree activo."""

import hashlib
import subprocess
from pathlib import Path
from typing import Any

import yaml

from sat_dengue_pipeline.models.logistic import canonical_json

BASE = "a9c2c1abac386053b2e78f072bdb44e0141f4045"
RECIPE = "conf/retroanalisis/noche/log_conclima.yml"
RECIPE_SHA = "7d67f0595cfdd990e331682ae581d4f49d1f74f83a107f4d9474540412443ec8"
CONTRACT = "satd-risk-ranking-v1"
PROCEDURE = "SATD-RISK-2025-LOG-CLIMATE-v1"
GENERATED = "2024-11-01T00:00:00Z"
LEGEND = (
    "Orden de prioridad retrospectivo. La posición no representa una probabilidad "
    "calibrada ni una autorización para uso operativo."
)
ROOT = Path(__file__).resolve().parents[4]


def digest(value: Any) -> str:
    """Identificar contenido finito con la representación canónica del adaptador."""
    return hashlib.sha256(canonical_json(value)).hexdigest()


def sha(data: bytes) -> str:
    """Identificar bytes exactos."""
    return hashlib.sha256(data).hexdigest()


def recipe() -> dict:
    """Leer exclusivamente los bytes de la receta aprobada en este worktree."""
    path = ROOT / "pipeline" / RECIPE
    content = path.read_bytes()
    if sha(content) != RECIPE_SHA:
        raise ValueError("La receta difiere de la identidad aprobada")
    return yaml.safe_load(content)


def lineage() -> dict:
    """Registrar código y lock sin consultar otro worktree ni credenciales."""
    source = ROOT / "pipeline/src/sat_dengue_pipeline"
    code = {
        p.relative_to(source).as_posix(): sha(p.read_bytes())
        for p in sorted(source.rglob("*"))
        if p.suffix in {".py", ".json"}
    }
    return {
        "code_sha": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "code_tree_sha256": digest(code),
        "lock_sha256": sha((ROOT / "pipeline/uv.lock").read_bytes()),
    }


def local_path(value: str, *, published: bool = False) -> Path:
    """Confinar entradas/salidas y rechazar enlaces antes de resolver rutas.

    Args:
        value: Ruta relativa al subproyecto, nunca otro worktree.
        published: Admitir únicamente la nueva frontera versionada de publicación.

    Returns:
        Ruta absoluta validada dentro de este worktree.
    """
    relative = Path(value)
    if relative.is_absolute():
        raise ValueError("Se requiere una ruta relativa del worktree")
    target = ROOT / "pipeline" / relative
    # /private/tmp no interviene: tampoco se aceptan escapes por symlink.
    if any(p.is_symlink() for p in (target, *target.parents) if p != ROOT.parent):
        raise ValueError("Las rutas de prioridades no admiten enlaces")
    allowed = ROOT / ("datos/resultados/risk-ranking" if published else "pipeline/data")
    if not target.resolve().is_relative_to(allowed.resolve()):
        raise ValueError("Ruta fuera del espacio autorizado para prioridades")
    return target.resolve()


def procedure() -> dict:
    """Declaración científica cerrada, independiente de rutas y modos de ejecución."""
    return {
        "id": PROCEDURE,
        "recipe_sha256": RECIPE_SHA,
        "horizon": 2,
        "train_start": "2012-01",
        "train_end": "2024-09",
        "available_end": "2024-10",
        "first_origin": "2024-11",
        "last_origin": "2025-10",
        "budget": 8,
        "population": {"50": 29, "73": 47},
        "eligibility": "OBSERVED_NON_EXCESS_COMPLETE_X_AT_T",
        "tie_break": "SCORE_DESC_DIVIPOLA_ASC",
        "generated_at": GENERATED,
    }
