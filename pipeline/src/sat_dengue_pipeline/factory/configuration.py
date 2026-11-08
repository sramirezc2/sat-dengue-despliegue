"""Configuración normativa única, conforme al documento aprobado de fábrica."""

import copy
import json
import re
from pathlib import Path
from typing import Any

from sat_dengue_pipeline.domain.canonical import PREDICTORS
from sat_dengue_pipeline.experiments.roles import ROLES, RoleSupport, RoleWindow, TemporalPlan
from sat_dengue_pipeline.experiments.rolling import stable_digest
from sat_dengue_pipeline.models.adapters import AdapterSpec

SPECIFICATION = "T16-FACTORY-XGB-S53-v1"


def project_root() -> Path:
    """Localizar únicamente este subproyecto, sin árboles hermanos."""
    return Path(__file__).resolve().parents[3]


def validate_configuration(configuration: dict[str, Any]) -> dict[str, Any]:
    """Exigir conformidad documental exacta, excepto ubicaciones operacionales."""
    config = copy.deepcopy(configuration)
    document = project_root().parent / "docs/decisions/task16-experiment-specification.md"
    text = document.read_text()
    match = re.search(r"```json\n(.*?)\n```", text, re.S)
    if not text.startswith("Estado: APROBADA PARA VALIDACIÓN DE FÁBRICA\n") or match is None:
        raise ValueError("La especificación de fábrica no está aprobada")
    approved = json.loads(match[1])
    scientific = {k: v for k, v in config.items() if k != "runtime"}
    expected = {k: v for k, v in approved.items() if k != "runtime"}
    if scientific != expected or config["specification"] != SPECIFICATION:
        raise ValueError("Configuración distinta de la especificación aprobada")
    if config["predictors"] != PREDICTORS or config["horizons"] != [1, 2] or config["seed"] != 53:
        raise ValueError("Esquema, horizontes o semilla de fábrica alterados")
    for key in ("workspace", "evidence"):
        value = Path(config["runtime"][key])
        anchor = project_root() if key == "workspace" else project_root().parent
        allowed = anchor / ("data" if key == "workspace" else "docs/evidence/task16")
        if value.is_absolute() or not (anchor / value).resolve().is_relative_to(allowed.resolve()):
            raise ValueError("Ubicación operacional fuera del confinamiento")
    for horizon in config["horizons"]:
        temporal_plan(config, horizon)
    return config


def scientific_configuration(config: dict[str, Any]) -> dict[str, Any]:
    """Excluir solo directorios operativos de la identidad científica compartida."""
    return {k: v for k, v in config.items() if k != "runtime"}


def temporal_plan(config: dict[str, Any], horizon: int) -> TemporalPlan:
    """Materializar los cinco roles aprobados sin una política temporal paralela."""
    roles = config["roles_by_horizon"][str(horizon)]
    return TemporalPlan(
        horizon=horizon,
        windows=tuple(RoleWindow(name, roles[name]["start"], roles[name]["end"]) for name in ROLES),
        embargo_months=config["embargo_months"],
        reserved_start=config["reserved_start"],
        supports={name: RoleSupport(**roles[name]["support"]) for name in ROLES},
    )


def adapter_spec(config: dict[str, Any]) -> AdapterSpec:
    """Congelar familia, versión, 33 entradas y preparación efectiva completa."""
    value = {key: config[key] for key in ("candidate", "preparation", "predictors")}
    return AdapterSpec(
        config["candidate"]["family"],
        config["candidate"]["adapter_version"],
        json.dumps(value, sort_keys=True),
        config["seed"],
    )


def configuration_digest(config: dict[str, Any]) -> str:
    """Identificar todas las decisiones aprobadas, sin ruta privada o credencial."""
    return stable_digest(scientific_configuration(config))
