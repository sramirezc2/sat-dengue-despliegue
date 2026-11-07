"""Construcción pura de documentos, bytes y manifiesto del publicador caracterizado."""

import hashlib
import json
import math
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta

from . import domain as d
from .errors import PublicationInputError


@dataclass(frozen=True)
class PublicationConfig:
    """Identidad explícita; el dominio no consulta reloj, entorno o Git."""

    procedimiento: str
    version_datos: str
    generado: str
    candidato: str = "auto"
    version_modelo: str | None = None
    justificacion: str = "elegido a mano por bandera"

    def __post_init__(self) -> None:
        """Exigir identidades y fecha UTC antes de construir documentos."""
        try:
            parsed = datetime.fromisoformat(self.generado)
            if parsed.utcoffset() != timedelta(0):
                raise ValueError
        except (ValueError, TypeError):
            raise PublicationInputError(
                "ERROR: generado debe ser una fecha UTC explícita"
            ) from None
        for value in (self.procedimiento, self.version_datos, self.candidato, self.justificacion):
            if not isinstance(value, str) or not value.strip() or len(value) > 500:
                raise PublicationInputError("ERROR: identidad o justificación inválida")


@dataclass(frozen=True)
class PublicationFile:
    """Nombre relativo y bytes completos del resultado, todavía sin publicar."""

    name: str
    content: bytes


@dataclass(frozen=True)
class PublicationPackage:
    """Paquete inmutable de bytes; el manifiesto no entra al glob de resultados."""

    files: tuple[PublicationFile, ...]
    manifest: bytes
    audit: dict


def encode_json(value: object) -> bytes:
    """Conservar el formato UTF-8 indentado del legado y rechazar NaN/Infinity."""
    return json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False).encode("utf-8")


def _check_rows(rows: list[dict], required: set[str], keys: tuple[str, ...]) -> None:
    """Rechazar registros incompletos, ambiguos o duplicados sin reparar datos."""
    seen = set()
    for row in rows:
        if (
            not isinstance(row, dict)
            or not required <= row.keys()
            or any(not isinstance(k, str) or not isinstance(v, str) for k, v in row.items())
        ):
            raise PublicationInputError("ERROR: esquema de entrada incompleto o inválido")
        identity = tuple(row[k] for k in keys)
        if identity in seen:
            raise PublicationInputError("ERROR: claves de entrada duplicadas")
        seen.add(identity)
        if "municipality_code" in row and not re.fullmatch(r"[0-9]{5}", row["municipality_code"]):
            raise PublicationInputError("ERROR: código municipal inválido")
        if "year_month" in row and not re.fullmatch(r"[0-9]{4}-(0[1-9]|1[0-2])", row["year_month"]):
            raise PublicationInputError("ERROR: periodo inválido")
        if "horizon" in row and row["horizon"] not in {"1", "2"}:
            raise PublicationInputError("ERROR: horizonte inválido")


def validate_inputs(panel: list[dict], predictions: list[dict], comparison: list[dict]) -> None:
    """Validar entradas locales calculadas sin acoplarlas al entrenamiento."""
    _check_rows(
        panel,
        {
            "municipality_code",
            "year_month",
            "municipality_name",
            d.CASOS_DEL_CANAL,
            "p25_canal_t",
            "p50_canal_t",
            "p75_canal_t",
        },
        ("municipality_code", "year_month"),
    )
    _check_rows(
        predictions,
        {
            "candidate",
            "municipality_code",
            "year_month",
            "horizon",
            "prediction_probability",
            "prediction_label",
        },
        ("candidate", "municipality_code", "year_month", "horizon"),
    )
    _check_rows(comparison, {"candidate", "horizon"}, ("candidate", "horizon"))
    numeric_fields = {
        d.CASOS_DEL_CANAL,
        "p25_canal_t",
        "p50_canal_t",
        "p75_canal_t",
        "p75_t1",
        "p75_t2",
        "y_t1",
        "y_true",
        "prediction_probability",
        "detected_onsets",
        "real_onsets",
        "false_alerts",
        "emitted_alerts",
        "false_alarm_ratio",
        "onset_sensitivity",
        "auroc",
        "average_precision",
        "brier",
    }
    try:
        for row in (*panel, *predictions, *comparison):
            for name in numeric_fields & row.keys():
                if row[name] != "" and not math.isfinite(float(row[name])):
                    raise ValueError
        for row in predictions:
            probability = row["prediction_probability"]
            if probability and (
                not 0 <= float(probability) <= 1 or row["prediction_label"] not in {"0", "1"}
            ):
                raise ValueError
    except (ValueError, TypeError):
        raise PublicationInputError(
            "ERROR: probabilidades, decisiones o números inválidos"
        ) from None


def build_package(
    panel_rows: list[dict],
    prediction_rows: list[dict],
    comparison_rows: list[dict],
    retroanalisis: dict | None,
    config: PublicationConfig,
) -> PublicationPackage:
    """Construir la publicación completa sin I/O ni modificación de entradas.

    Args:
        panel_rows: Panel mensual ya calculado, como registros CSV explícitos.
        prediction_rows: Probabilidades/decisiones calculadas previamente.
        comparison_rows: Comparación congelada; no se recalculan métricas.
        retroanalisis: Bloque opcional separado de la comparación congelada.
        config: Identidades y fecha UTC inyectadas.

    Returns:
        Documentos serializados, manifiesto y auditoría de selección/omisiones.
    """
    validate_inputs(panel_rows, prediction_rows, comparison_rows)
    panel = d.leer_panel(panel_rows)
    if config.candidato == "auto":
        candidate, reason = d.elegir_candidato(comparison_rows)
    else:
        candidate, reason = config.candidato, config.justificacion
    predictions, thresholds = d.leer_predicciones(prediction_rows, candidate)
    comparison = d.leer_comparacion(comparison_rows, candidate)
    candidates = d.leer_todos_los_candidatos(comparison_rows, candidate)
    candidates += d.canal_endemico(panel, predictions)
    candidates.sort(key=lambda r: (r["horizon"], -(r["onsets_detected"] or 0)))
    model_version = config.version_modelo or f"{candidate}-{config.procedimiento[:12]}"
    horizons: dict[str, set[str]] = defaultdict(set)
    for _, period, horizon in predictions:
        horizons[period].add(horizon)
    periods = sorted(period for period, hs in horizons.items() if hs == {"1", "2"})
    files = []
    for department in d.DEPARTAMENTOS:
        for period in periods:
            document = d.construir_documento(
                departamento=department,
                periodo=period,
                panel=panel,
                predicciones=predictions,
                umbrales=thresholds,
                comparacion=comparison,
                candidatos=candidates,
                retroanalisis=retroanalisis,
                candidato=candidate,
                procedimiento=config.procedimiento,
                version_modelo=model_version,
                version_datos=config.version_datos,
                generado=config.generado,
            )
            files.append(
                PublicationFile(f"resultado_{department}_{period}.json", encode_json(document))
            )
    files.sort(key=lambda file: file.name)
    selection = {
        "requested": config.candidato,
        "forced": config.candidato != "auto",
        "reason": reason,
    }
    manifest = {
        "schema": "satd-publication-v1",
        "procedure": config.procedimiento,
        "candidate": candidate,
        "data_version": config.version_datos,
        "model_version": model_version,
        "generated_at": config.generado,
        "selection": selection,
        "files": [
            {
                "name": f.name,
                "size_bytes": len(f.content),
                "sha256": hashlib.sha256(f.content).hexdigest(),
            }
            for f in files
        ],
    }
    return PublicationPackage(
        tuple(files),
        encode_json(manifest),
        {
            "candidate": candidate,
            "selection": selection,
            "omitted_periods": sorted(set(horizons) - set(periods)),
            "thresholds": {
                h: {"value": t.valor, "margin": t.margen} for h, t in sorted(thresholds.items())
            },
        },
    )
