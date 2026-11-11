"""Configuración independiente de T16, cerrada y limitada a contratos existentes."""

import copy
import json
from pathlib import Path

from jsonschema import Draft202012Validator

from sat_dengue_pipeline.domain.canonical import PREDICTORS
from sat_dengue_pipeline.domain.margin import MARGIN_COLUMNS, MARGIN_SOURCES
from sat_dengue_pipeline.domain.temporal import TemporalPolicy
from sat_dengue_pipeline.experiments.decisions import ThresholdPolicy
from sat_dengue_pipeline.factory.configuration import adapter_spec, temporal_plan
from sat_dengue_pipeline.models.familias import ADAPTERS
from sat_dengue_pipeline.raw.contract import sha256

from .registry import confined, read_yaml

METRICS = [
    "average_precision",
    "auroc",
    "brier",
    "onset_sensitivity",
    "false_alarm_ratio",
    "alert_volume",
    "alert_fraction",
]
BASELINES = ["train_prevalence", "non_excess_persists_no_new_onset"]
# Con protocolo rolling_origin se agregan las líneas base del canal endémico (política v2).
BASELINES_ROLLING = [*BASELINES, "canal_p75", "canal_ajustado", "canal_fuera_exceso"]


def validate_configuration(config: dict) -> dict:
    """Validar todos los campos antes de adquirir datos o crear un estimador ajustado."""
    schema = json.loads(Path(__file__).with_name("configuration.schema.json").read_bytes())
    errors = list(Draft202012Validator(schema).iter_errors(config))
    if errors:
        raise ValueError("Esquema cerrado de configuración inválido")
    config = copy.deepcopy(config)
    TemporalPolicy(config["reserved_start"])
    if config["reserved_start"] != "2025-01":
        raise ValueError("La frontera global no es configurable")
    horizons = config["horizons"]
    if horizons not in ([1], [2], [1, 2]) or type(config["seed"]) is not int or config["seed"] < 0:
        raise ValueError("Horizontes o semilla inválidos")
    predictors = config["predictors"]
    if not predictors or predictors != [p for p in PREDICTORS if p in predictors]:
        raise ValueError("Predictores no canónicos, repetidos o desordenados")
    availability = {p: -int(p.rsplit("lag", 1)[1]) if "_lag" in p else 0 for p in PREDICTORS}
    if config["predictor_availability"] != availability:
        raise ValueError("Disponibilidad canónica alterada")
    if set(config["roles_by_horizon"]) != {str(h) for h in horizons} or (
        set(config["threshold"]["max_false_alarm_ratio_by_horizon"]) != {str(h) for h in horizons}
    ):
        raise ValueError("Roles o umbrales sin correspondencia con horizontes")
    if any(
        type(config[k]) is not int or config[k] < 0
        for k in ("label_delay_months", "embargo_months")
    ):
        raise ValueError("Disponibilidad o embargo inválidos")
    for h in horizons:
        temporal_plan(config, h)
        ThresholdPolicy(
            tuple(config["threshold"]["grid"]),
            config["threshold"]["max_false_alarm_ratio_by_horizon"][str(h)],
        )
    prep = config["preparation"]
    # El bloque de margen se declara en preparación y nunca en el canónico: si
    # está apagado, la receta tiene que quedar byte a byte como la histórica.
    if prep["variables_g"]:
        if prep.get("margin_source", MARGIN_SOURCES[0]) not in MARGIN_SOURCES:
            raise ValueError("Fuente de casos del bloque de margen no declarada")
        if prep["matrix_columns"][-len(MARGIN_COLUMNS) :] != MARGIN_COLUMNS:
            raise ValueError("El bloque de margen debe cerrar la matriz, en su orden fijo")
    elif any(column in prep["matrix_columns"] for column in MARGIN_COLUMNS):
        raise ValueError("Columnas de margen en la matriz sin declarar variables_g")
    rolling = config.get("protocol", "fixed_roles") == "rolling_origin"
    if config["metrics"] != METRICS or config["baselines"] != (
        BASELINES_ROLLING if rolling else BASELINES
    ):
        raise ValueError("Métricas/líneas base fuera del contrato implementado")
    if rolling != ("rolling" in config):
        raise ValueError("La ventana expansiva requiere el bloque rolling, y solo ella lo admite")
    if rolling:
        ventana = config["rolling"]
        if not (
            "2019-01" <= ventana["first_origin"] < ventana["last_target"] < config["reserved_start"]
        ):
            raise ValueError("Ventana expansiva fuera del periodo autorizado")
    candidate = config["candidate"]
    key = (candidate["family"], candidate["adapter_version"])
    if key not in ADAPTERS:
        raise ValueError("Familia/versión no implementada")
    ADAPTERS[key](adapter_spec(config))
    if config["calibration"]["parameters"]["random_state"] != config["seed"]:
        raise ValueError("Semilla de calibración distinta")
    # Las políticas nominales deben describir el comportamiento realmente implementado.
    if {
        k: config["calibration"][k] for k in ("representations", "method", "tie", "convergence")
    } != {
        "representations": ["original", "sigmoid"],
        "method": "logistic_on_raw_probability",
        "tie": "original",
        "convergence": "fail",
    }:
        raise ValueError("Calibración no implementada")
    threshold = config["threshold"]
    if any(
        threshold[k] != v
        for k, v in {
            "comparison": "probability_greater_or_equal_threshold",
            "denominator": "emitted_evaluable_alerts_TP_plus_FP",
            "zero_alerts": "infeasible",
            "objective": "maximum_onset_sensitivity",
            "tiebreak": ["fewer_false_alerts", "lower_false_alarm_ratio", "higher_threshold"],
        }.items()
    ):
        raise ValueError("Política de umbral no implementada")
    data = config["data"]
    if data["mode"] == "synthetic" and data != {
        "mode": "synthetic",
        "manifest": None,
        "manifest_sha256": None,
        "require_private": False,
    }:
        raise ValueError("Fixture no admite fuente externa")
    if config["schema_version"] == 3:
        from sat_dengue_pipeline.evaluation.scientific.configuration import validate_scientific

        validate_scientific(config)
    return config


def load_configuration(root: Path, entry: dict) -> dict:
    """Vincular tipo de experimento, release y archivo congelado antes de ejecución."""
    path = confined(root, entry["configuration"], "pipeline/conf/experiments")
    config = validate_configuration(read_yaml(path, expected_sha256=entry["configuration_sha256"]))
    protocol = confined(root, entry["protocol"], "docs/experiments")
    if sha256(protocol) != entry["protocol_sha256"]:
        raise ValueError("Protocolo congelado alterado")
    data = config["data"]
    if (entry["experiment_type"] == "synthetic_fixture") != (data["mode"] == "synthetic"):
        raise ValueError("Fixture y experimento científico no pueden intercambiar fuentes")
    if data["mode"] == "raw":
        manifest = confined(root, data["manifest"], "pipeline/conf/releases")
        if sha256(manifest) != data["manifest_sha256"] or not data["require_private"]:
            raise ValueError("Release real sin hash/aprobación privada")
        from sat_dengue_pipeline.acquisition.contracts import ReleaseManifest
        from sat_dengue_pipeline.acquisition.raw_manifest import validate_raw_manifest

        validate_raw_manifest(ReleaseManifest.from_json(manifest.read_text(encoding="utf-8")))
        # V1 sigue siendo legible. La compuerta de ejecución exige selección y N=3;
        # no se infiere un perfil para volver entrenable una receta histórica incompleta.
        if "canonical" in data:
            from sat_dengue_pipeline.acquisition.raw_manifest import canonical_build_config

            canonical_build_config(data["canonical"]["profile"])
            confined(root, data["canonical"]["certificate"], "docs/evidence", exists=False)
    if config["schema_version"] == 3:
        contract = config["scientific_evaluation"]["contract"]
        document = confined(root, contract["path"], "docs/experiments")
        if sha256(document) != contract[
            "sha256"
        ] or "PROPUESTA_PARA_APROBACION" not in document.read_text(encoding="utf-8"):
            raise ValueError("Contrato propuesto ausente o distinto del congelado")
    config["specification"] = entry["experiment_id"]
    config["governance"] = {
        "purpose": entry["experiment_type"],
        "champion_status": "NOT_SELECTED",
        "operational_authorization": False,
        "reserved_evidence": "consumed_retrospective_evidence",
    }
    return config
