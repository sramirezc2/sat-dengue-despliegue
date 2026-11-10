"""La fábrica acepta la familia logistic_onset sin abrir combinaciones mezcladas."""

import copy
from pathlib import Path

import pytest
import yaml

from sat_dengue_pipeline.experiment_management.configuration import validate_configuration

RAIZ = Path(__file__).resolve().parents[1]


def _logistica() -> dict:
    """EXP001 (fixture sintético) con el candidato y la preparación de la receta logística."""
    base = yaml.safe_load((RAIZ / "conf/experiments/EXP001.yml").read_text(encoding="utf-8"))
    receta = yaml.safe_load(
        (RAIZ / "conf/retroanalisis/logistica_sin_clima.yml").read_text(encoding="utf-8")
    )
    cfg = copy.deepcopy(base)
    for clave in ("predictors", "preparation", "candidate"):
        cfg[clave] = copy.deepcopy(receta[clave])
    cfg["seed"] = receta["seed"]
    cfg["calibration"]["parameters"]["random_state"] = receta["seed"]
    return cfg


def test_acepta_logistica() -> None:
    """Una configuración logística completa pasa la validación de esquema y adaptador."""
    validate_configuration(_logistica())


def test_xgboost_existente_sigue_valido() -> None:
    """EXP001 sigue validando igual que antes."""
    validate_configuration(
        yaml.safe_load((RAIZ / "conf/experiments/EXP001.yml").read_text(encoding="utf-8"))
    )


@pytest.mark.parametrize(
    "clave,valor", [("rounds", 300), ("parameters", {}), ("expected_native_configuration", {})]
)
def test_rechaza_campos_xgboost_en_logistica(clave: str, valor: object) -> None:
    """La logística no admite campos propios de XGBoost."""
    cfg = _logistica()
    cfg["candidate"][clave] = valor
    with pytest.raises(ValueError):
        validate_configuration(cfg)


def test_rechaza_familia_desconocida() -> None:
    """Solo se aceptan las familias implementadas."""
    cfg = _logistica()
    cfg["candidate"]["family"] = "random_forest"
    with pytest.raises(ValueError):
        validate_configuration(cfg)


def test_xgboost_exige_sus_campos() -> None:
    """XGBoost sigue exigiendo rondas, parámetros y configuración nativa esperada."""
    cfg = yaml.safe_load((RAIZ / "conf/experiments/EXP001.yml").read_text(encoding="utf-8"))
    del cfg["candidate"]["rounds"]
    with pytest.raises(ValueError):
        validate_configuration(cfg)
