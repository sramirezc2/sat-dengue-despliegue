"""experiment_run con ventana expansiva, población y líneas base del canal (sintético)."""

import copy
import json
from pathlib import Path

import pytest
import yaml
from test_experiment_management import change_config, repository  # noqa: F401

from sat_dengue_pipeline.experiment_management import runner
from sat_dengue_pipeline.experiment_management.configuration import validate_configuration
from sat_dengue_pipeline.factory.rolling_protocol import BASES_CANAL, filtrar_poblacion

RAIZ = Path(__file__).resolve().parents[1]
RECETA = yaml.safe_load(
    (RAIZ / "conf/retroanalisis/logistica_sin_clima.yml").read_text(encoding="utf-8")
)


def _a_rolling(config: dict) -> None:
    """Convertir una receta de fixture en logística con ventana expansiva y población."""
    for clave in ("predictors", "preparation", "candidate"):
        config[clave] = copy.deepcopy(RECETA[clave])
    config["seed"] = RECETA["seed"]
    config["calibration"]["parameters"]["random_state"] = RECETA["seed"]
    config["protocol"] = "rolling_origin"
    config["rolling"] = {"first_origin": "2023-06", "last_target": "2024-12"}
    config["population"] = {"department_codes": ["50", "73"]}
    config["baselines"] = [*config["baselines"], *BASES_CANAL]


def test_validacion_del_protocolo() -> None:
    """Ventana expansiva válida; bloque rolling y líneas base del canal solo con ese protocolo."""
    base = yaml.safe_load((RAIZ / "conf/experiments/EXP001.yml").read_text(encoding="utf-8"))
    cfg = copy.deepcopy(base)
    _a_rolling(cfg)
    validate_configuration(cfg)
    sin_bloque = copy.deepcopy(cfg)
    del sin_bloque["rolling"]
    fijo_con_canal = copy.deepcopy(base)
    fijo_con_canal["baselines"] = [*base["baselines"], *BASES_CANAL]
    reservado = copy.deepcopy(cfg)
    reservado["rolling"]["last_target"] = "2025-03"
    for malo in (sin_bloque, fijo_con_canal, reservado):
        with pytest.raises(ValueError):
            validate_configuration(malo)


def test_filtro_de_poblacion() -> None:
    """Sin población no cambia nada; con población solo quedan esos departamentos."""
    import pandas as pd

    t = pd.DataFrame({"department_code": ["50", "73", "05"], "x": [1, 2, 3]})
    assert len(filtrar_poblacion(t, {})) == 3
    assert set(
        filtrar_poblacion(t, {"population": {"department_codes": ["73"]}}).department_code
    ) == {"73"}
    with pytest.raises(ValueError):
        filtrar_poblacion(t, {"population": {"department_codes": ["99"]}})


def test_experiment_run_rolling_de_punta_a_punta(repository):  # noqa: F811
    """La fábrica corre la ventana expansiva y publica métricas contra el canal."""
    change_config(repository, "EXP001", _a_rolling)
    rec = runner.execute("EXP001", root=repository, execution_id="rolling", tracking=False)
    assert rec["status"] == "COMPLETED" and rec["candidate"] == "logistic_onset"
    carpeta = repository / "docs/evidence/experiments/EXP001/rolling"
    metricas = json.loads((carpeta / "metrics.json").read_bytes())
    validacion = json.loads((carpeta / "validation.json").read_bytes())
    for h, res in metricas.items():
        assert res["principal"] == "candidate_vs_canal_fuera_exceso"
        assert {"canal_fuera_exceso", "candidate_vs_canal_fuera_exceso"} <= set(res["metrics"])
        assert validacion["support"][h]["folds"] >= 2
    assert validacion["temporal"]["protocol"] == "rolling_origin"


def test_experiment_run_cinco_roles_con_contrato(repository):  # noqa: F811
    """Con roles fijos y contrato, la evidencia trae comparadores, controles y veredicto."""
    from sat_dengue_pipeline.evaluation.contrato import PARAMETROS_DEFECTO

    def _contrato(config: dict) -> None:
        for clave in ("predictors", "preparation", "candidate"):
            config[clave] = copy.deepcopy(RECETA[clave])
        config["seed"] = RECETA["seed"]
        config["calibration"]["parameters"]["random_state"] = RECETA["seed"]
        config["population"] = {"department_codes": ["50", "73"]}
        config["contract"] = {**PARAMETROS_DEFECTO, "replicas": 200}

    change_config(repository, "EXP001", _contrato)
    rec = runner.execute("EXP001", root=repository, execution_id="contrato", tracking=False)
    assert rec["status"] == "COMPLETED"
    metricas = json.loads(
        (repository / "docs/evidence/experiments/EXP001/contrato/metrics.json").read_bytes()
    )
    for res in metricas.values():
        c = res["contract"]
        assert {"canal_condicionado", "candidato", "control_ranking_aleatorio"} <= set(c["medidas"])
        assert c["veredicto"] in {
            "CUMPLE",
            "NO_CUMPLE_POR_EFECTO",
            "PRECISION_INSUFICIENTE",
            "NO_EVALUABLE",
            "INVALIDO",
        }
