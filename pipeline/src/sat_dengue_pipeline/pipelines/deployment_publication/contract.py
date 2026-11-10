"""Contrato de publicación autónomo: schema derivado e invariantes entre campos."""

import hashlib
import json
import re

from jsonschema import Draft202012Validator, FormatChecker, ValidationError

from .domain import _mes_siguiente
from .errors import PublicationContractError
from .package import PublicationPackage, valid_timestamp

NAME = re.compile(r"resultado_(50|73)_([0-9]{4}-(?:0[1-9]|1[0-2]))\.json")
COUNTS = {"50": 29, "73": 47}


def _require(condition: bool, message: str) -> None:
    """Fallar con excepción contractual específica, también bajo Python optimizado."""
    if not condition:
        raise PublicationContractError(message)


def decode_json(data: bytes) -> dict:
    """Rechazar JSON no objeto, constantes no finitas y claves JSON duplicadas."""

    def pairs(items: list[tuple]) -> dict:
        """Preservar orden y rechazar claves ambiguas."""
        result = {}
        for key, value in items:
            _require(key not in result, "Clave JSON duplicada")
            result[key] = value
        return result

    def constant(value: str) -> None:
        """Rechazar extensiones JSON NaN e Infinity."""
        raise PublicationContractError("Constante JSON no finita")

    try:
        result = json.loads(data, object_pairs_hook=pairs, parse_constant=constant)
        _require(isinstance(result, dict), "El documento JSON debe ser un objeto")
        return result
    except (ValueError, UnicodeError) as exc:
        raise PublicationContractError("JSON inválido") from exc


def validate_document(document: dict, schema: dict, name: str) -> None:
    """Validar forma, nombre, calendario, IDs, disponibilidad y gobernanza."""
    try:
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(document)
        match = NAME.fullmatch(name)
        _require(match is not None, "Nombre de resultado inválido")
        department, period = match.groups()
        meta, dept, governance = (document[k] for k in ("metadata", "department", "governance"))
        _require(
            dept["department_code"] == department
            and dept["requested_period"] == period
            and meta["reference_period"] == period,
            "Nombre y contenido incompatibles",
        )
        for value in (meta["generated_at"], meta["data_updated_at"]):
            if value is not None:
                _require(
                    valid_timestamp(value),
                    "Fecha RFC3339 sin zona o inválida",
                )
        towns = document["municipalities"]
        codes = [town["municipality_code"] for town in towns]
        _require(
            len(codes) == COUNTS[department] and len(set(codes)) == len(codes),
            "Cardinalidad municipal inválida",
        )
        ids = [meta["result_set_id"]]
        for town in towns:
            _require(town["municipality_code"].startswith(department), "Municipio ajeno")
            results = town["results"]
            _require(
                {result["horizon"] for result in results} == {"T1", "T2"}, "Horizontes duplicados"
            )
            summary = tuple(town[k] for k in ("cases_t", "p25", "median", "p75"))
            if town["endemic_zone_t"] == "UNAVAILABLE":
                _require(
                    all(value is None for value in summary), "Contexto no disponible incoherente"
                )
            series = town["endemic_channel_series"]
            periods = [point["period"] for point in series]
            _require(periods == sorted(set(periods)), "Serie duplicada o fuera de orden")
            if not series:
                _require(
                    town["endemic_zone_t"] == "UNAVAILABLE" and all(v is None for v in summary),
                    "Serie vacía con contexto disponible",
                )
            else:
                reference = [point for point in series if point["period"] == period]
                _require(
                    len(reference) == 1
                    and tuple(reference[0][k] for k in ("cases", "p25", "median", "p75"))
                    == summary,
                    "Serie y resumen municipal incoherentes",
                )
            for point in [town, *series]:
                q = [point[k] for k in ("p25", "median", "p75")]
                _require(
                    any(v is None for v in q) or q[0] <= q[1] <= q[2], "Percentiles desordenados"
                )
            for point in series:
                _require(point["period"][:4] == period[:4], "Serie fuera del año de referencia")
                _require(
                    point["period"] <= period or point["cases"] is None, "Casos futuros visibles"
                )
            for result in results:
                _require(
                    result["target_period"] == _mes_siguiente(period, int(result["horizon"][-1])),
                    "Objetivo incompatible",
                )
                if result["availability_status"] == "AVAILABLE":
                    _require(
                        all(
                            result[k] is not None
                            for k in (
                                "result_id",
                                "probability",
                                "threshold",
                                "model_family",
                                "model_role",
                                "model_version",
                                "procedure_id",
                            )
                        )
                        and result["availability_reason"] is None,
                        "Resultado disponible incompleto",
                    )
                    expected = (
                        "ALERT" if result["probability"] >= result["threshold"] else "NO_ALERT"
                    )
                    _require(
                        result["alert_status"] == expected, "Decisión y probabilidad incoherentes"
                    )
                    ids.append(result["result_id"])
                else:
                    _require(
                        all(result[k] is None for k in ("result_id", "probability", "threshold"))
                        and result["alert_status"] == "UNAVAILABLE"
                        and result["availability_reason"] is not None,
                        "Ausencia incoherente",
                    )
                if (
                    governance["governance_gate"] == "G5"
                    and governance["governance_status"] == "NOT_APPROVED"
                ):
                    _require(
                        governance["champion_status"] == "NOT_SELECTED"
                        and result["model_role"] in {None, "PROVISIONAL_CANDIDATE"},
                        "Promoción científica no autorizada",
                    )
        _require(len(ids) == len(set(ids)), "UUID duplicados")
        retro = document["evaluation_context"].get("development_backtest")
        if retro:
            _require(
                retro["period_start"] <= retro["period_end"] and bool(retro["rows"]),
                "Retroanálisis vacío/incoherente",
            )
            for row in retro["rows"]:
                _require(
                    row["onsets_detected"] <= row["actual_onsets"]
                    and row["false_alerts"] <= row["false_alerts_onset"] <= row["alerts_emitted"],
                    "Conteos de retroanálisis incoherentes",
                )
            for row in retro.get("curve", []):
                _require(row["onsets_detected"] <= row["alerts_emitted"], "Curva incoherente")
    except (ValidationError, KeyError, TypeError, ValueError) as exc:
        if isinstance(exc, PublicationContractError):
            raise
        raise PublicationContractError("Contrato de documento inválido") from exc


def validate_package(package: PublicationPackage, schema: dict) -> dict:
    """Verificar el conjunto cerrado, hashes y metadatos antes de cualquier promoción."""
    manifest = decode_json(package.manifest)
    _require(
        set(manifest)
        == {
            "schema",
            "procedure",
            "candidate",
            "data_version",
            "model_version",
            "generated_at",
            "selection",
            "files",
        },
        "Campos de manifiesto inválidos",
    )
    selection = manifest["selection"]
    _require(
        isinstance(selection, dict) and set(selection) == {"requested", "forced", "reason"},
        "Auditoría de selección inválida",
    )
    _require(
        isinstance(selection["requested"], str)
        and bool(selection["requested"])
        and type(selection["forced"]) is bool
        and selection["forced"] == (selection["requested"] != "auto")
        and isinstance(selection["reason"], str)
        and bool(selection["reason"]),
        "Override no auditable",
    )
    for key in ("procedure", "candidate", "data_version", "model_version"):
        _require(
            isinstance(manifest[key], str) and 0 < len(manifest[key]) <= 128,
            "Identidad de manifiesto inválida",
        )
    names = [file.name for file in package.files]
    _require(names == sorted(set(names)), "Nombres duplicados o fuera de orden")
    expected = [
        {
            "name": file.name,
            "size_bytes": len(file.content),
            "sha256": hashlib.sha256(file.content).hexdigest(),
        }
        for file in package.files
    ]
    _require(manifest.get("files") == expected, "Manifiesto, tamaños o SHA-256 incompatibles")
    _require(manifest.get("schema") == "satd-publication-v1", "Versión de manifiesto desconocida")
    for file in package.files:
        document = decode_json(file.content)
        validate_document(document, schema, file.name)
        _require(
            document["metadata"]["generated_at"] == manifest["generated_at"]
            and document["metadata"]["data_version"] == manifest["data_version"],
            "Metadatos distintos",
        )
        _require(
            document["governance"]["governance_status"] == "NOT_APPROVED"
            and document["governance"]["champion_status"] == "NOT_SELECTED",
            "Gobernanza modificada",
        )
        for town in document["municipalities"]:
            for result in town["results"]:
                if result["availability_status"] == "AVAILABLE":
                    _require(
                        result["model_family"] == manifest["candidate"]
                        and result["model_version"] == manifest["model_version"]
                        and result["procedure_id"] == manifest["procedure"],
                        "Linaje incompatible",
                    )
    return manifest
