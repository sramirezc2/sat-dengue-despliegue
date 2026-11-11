"""Protocolo de ventana expansiva para experiment_run y filtro opcional de población.

Rama separada del flujo de cinco roles fijos: reentrena en cada mes de origen con el arnés
``run_candidate`` (vía ``predicciones_rolling``) y evalúa con ``validacion_anual`` contra las líneas
base del canal endémico, emitiendo cada mes las mismas alertas que cada línea base. Los campos
de configuración que la activan son opcionales; si faltan, la fábrica conserva su comportamiento.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from sat_dengue_pipeline.evaluation import validacion_anual as va
from sat_dengue_pipeline.evaluation.retroanalisis import predicciones_rolling

BASES_CANAL = ["canal_p75", "canal_ajustado", "canal_fuera_exceso"]
METRICAS_ROLLING = [
    "inicios",
    "alertas",
    "inicios_detectados",
    "falsas",
    "carga_100mm",
    "diferencia_vs_canal",
    "ic95_lo",
    "ic95_hi",
]


def filtrar_poblacion(table: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
    """Conservar solo los departamentos declarados en ``population.department_codes``.

    Args:
        table: Panel canónico (nacional).
        config: Configuración del experimento.

    Returns:
        El panel sin cambios si no hay población declarada; si la hay, solo esas filas.

    Raises:
        ValueError: Si el filtro deja el panel vacío.
    """
    codigos = (config.get("population") or {}).get("department_codes")
    if not codigos:
        return table
    out = table[table.department_code.isin([str(c) for c in codigos])].reset_index(drop=True)
    if out.empty:
        raise ValueError("La población declarada no tiene filas en el panel")
    return out


@dataclass
class RollingRun:
    """Resultados con los mismos atributos que el runner publica para FactoryRun."""

    results: dict[str, Any] = field(default_factory=dict)
    support: dict[str, Any] = field(default_factory=dict)
    temporal: dict[str, Any] = field(default_factory=dict)
    audit: dict[str, Any] = field(default_factory=dict)
    identities: dict[str, Any] = field(default_factory=dict)
    label_reads: dict[str, Any] = field(default_factory=dict)


def _registros(valores: dict[str, Any]) -> list[dict[str, Any]]:
    """Convertir una fila de resultados a registros métrica/valor para MLflow y evidencia.

    Args:
        valores: Métricas con nombre.

    Returns:
        Lista de registros ``{"metric", "value"}`` con valores finitos o None.
    """
    out = []
    for nombre in METRICAS_ROLLING:
        v = valores.get(nombre)
        out.append({"metric": nombre, "value": None if v is None or pd.isna(v) else float(v)})
    return out


def ejecutar(table: pd.DataFrame, schema: dict, config: dict[str, Any], audit: dict) -> RollingRun:
    """Correr la ventana expansiva por horizonte y compararla con las líneas base del canal.

    Args:
        table: Panel canónico ya filtrado por población.
        schema: Esquema del productor canónico.
        config: Configuración validada del experimento.
        audit: Auditoría del panel canónico, para la evidencia.

    Returns:
        RollingRun con métricas por horizonte y línea base, detalle anual y meses omitidos.
    """
    ventana = config.get("rolling") or {}
    primer, ultimo = ventana.get("first_origin", "2019-01"), ventana.get("last_target", "2024-12")
    run = RollingRun(audit=audit)
    run.temporal = {
        "protocol": "rolling_origin",
        "first_origin": primer,
        "last_target": ultimo,
        "reserved_start": config["reserved_start"],
    }
    for h in config["horizons"]:
        # La cobertura del conjunto común no entra al soporte: este payload va a
        # la certificación y su forma está fijada por pruebas de contrato.
        preds, omitidos, _ = predicciones_rolling(table, schema, config, int(h), primer, ultimo)
        run.support[str(h)] = {
            "predicciones": int(len(preds)),
            "folds": int(preds.fold_id.nunique()) if len(preds) else 0,
            "meses_omitidos": omitidos,
        }
        if preds.empty or preds.fold_id.nunique() < 2:
            raise ValueError(f"Sin soporte para la ventana expansiva en T+{h}")
        df = va.desde_pipeline(table, preds, str(preds.candidate.iloc[0]), int(h))
        anios = tuple(
            sorted(
                int(a) for a in df.anio_objetivo.unique() if a < int(config["reserved_start"][:4])
            )
        )
        historia = va.historia_desde_panel(table, int(h))
        resumen = va.comparar(df, anios, historia=historia, bases=tuple(BASES_CANAL))
        metricas = {}
        for fila in resumen.itertuples():
            if fila.linea_base not in BASES_CANAL:
                continue
            metricas[fila.linea_base] = _registros(
                {
                    "inicios": fila.inicios,
                    "alertas": fila.alertas,
                    "inicios_detectados": fila.base_detectados,
                    "falsas": fila.base_falsas,
                    "carga_100mm": fila.base_carga_100mm,
                }
            )
            metricas[f"candidate_vs_{fila.linea_base}"] = _registros(
                {
                    "inicios": fila.inicios,
                    "alertas": fila.alertas,
                    "inicios_detectados": fila.candidato_detectados,
                    "falsas": fila.candidato_falsas,
                    "carga_100mm": fila.candidato_carga_100mm,
                    "diferencia_vs_canal": fila.diferencia,
                    "ic95_lo": fila.ic95_lo,
                    "ic95_hi": fila.ic95_hi,
                }
            )
        run.results[str(h)] = {
            "metrics": metricas,
            "principal": "candidate_vs_canal_fuera_exceso",
            "regla_operativa": "mismas alertas por mes que canal_fuera_exceso",
            "anios": list(anios),
            "por_anio": va.por_anio(df, "canal_fuera_exceso", anios, historia=historia).to_dict(
                "records"
            ),
        }
    return run
