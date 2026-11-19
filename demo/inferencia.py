"""Inferencia mensual con el ajuste de EXP315 y el contexto canónico de su ejecución."""

import csv
import hashlib
import io
import json
from dataclasses import dataclass
from pathlib import Path
from xml.etree.ElementTree import ParseError
from zipfile import BadZipFile, ZipFile

import pandas as pd
from openpyxl.utils.exceptions import InvalidFileException
from sat_dengue_pipeline.domain.calendar import add_months
from sat_dengue_pipeline.domain.canonical import CLIMATE, COUNTS, KEYS, PREDICTORS
from sat_dengue_pipeline.domain.endemic_channel import CHANNEL, classify_endemic_zone
from sat_dengue_pipeline.experiment_management.evidence import verify_execution
from sat_dengue_pipeline.experiments.decisions import apply_sigmoid
from sat_dengue_pipeline.models.logistic import predict_exported
from sat_dengue_pipeline.raw.temporal import parse_date

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = "EXP315"


@dataclass
class Model:
    """Artefactos privados de una corrida completada."""

    execution: str
    state: dict
    context: pd.DataFrame
    decisions: dict


def load_model(root: Path = ROOT) -> Model:
    """Vincular modelo, predictores y decisiones al inventario de la misma corrida."""
    inventories = list((root / "docs/evidence/experiments" / EXPERIMENT).glob("*/inventory.json"))
    if len(inventories) != 1:
        raise ValueError("Se necesita el inventario de una ejecución completa de EXP315.")
    inventory = inventories[0]
    receipt = verify_execution(root, inventory.relative_to(root).as_posix())
    if receipt["status"] != "COMPLETED" or receipt["experiment_type"] != "scientific":
        raise ValueError("EXP315 aún no tiene un ajuste completado.")
    execution = receipt["execution_id"]
    evidence = inventory.parent
    lineage = json.loads((evidence / "lineage.json").read_bytes())
    private = root / "pipeline/data/experiments" / execution / "inference-fit"

    def read_verified(name: str, key: str) -> bytes:
        data = (private / name).read_bytes()
        if hashlib.sha256(data).hexdigest() != lineage[key]:
            raise ValueError("El paquete privado difiere del inventario de EXP315.")
        return data

    state = json.loads(read_verified("model.json", "inference_model_sha256"))
    context = pd.read_csv(
        io.BytesIO(read_verified("context.csv", "inference_context_sha256")),
        dtype={KEYS[0]: str},
        float_precision="round_trip",
    )
    validation = json.loads((evidence / "validation.json").read_bytes())
    config = json.loads((evidence / "configuration.json").read_bytes())
    available = validation["temporal"]["2"]["support"]["threshold_selection"]["available"]
    context = context.loc[context.year_month.gt(add_months(available, config["embargo_months"]))]
    decisions = json.loads((evidence / "metrics.json").read_bytes())["2"]
    return Model(execution, state, context, decisions)


def geography() -> pd.Series:
    """Leer el catálogo municipal de Meta y Tolima."""
    geo = pd.read_csv(ROOT / "pipeline/conf/geografia/divipola_coordenadas.csv", dtype=str)
    return geo.loc[geo.cod_dpto.isin(["50", "73"])].set_index("cod_mpio").nom_mpio


def parse_upload(data: bytes, suffix: str, cities: pd.Index) -> tuple[str, pd.DataFrame, dict]:
    """Reducir las notificaciones válidas de un mes a conteos por residencia y evento."""
    if len(data) > 5 * 1024**2:
        raise ValueError("El archivo supera 5 MB.")
    stream = io.BytesIO(data)
    if suffix.lower() == ".xlsx":
        try:
            with ZipFile(stream) as archive:
                if sum(f.file_size for f in archive.infolist()) > 32 * 1024**2:
                    raise ValueError("El contenido del Excel supera 32 MB.")
            with pd.ExcelFile(stream, engine="openpyxl") as book:
                if len(book.sheet_names) != 1:
                    raise ValueError("El Excel debe contener una sola hoja.")
                frame = book.parse(header=None, dtype=str, keep_default_na=False)
        except (BadZipFile, InvalidFileException, KeyError, ParseError, OSError) as error:
            raise ValueError("El archivo Excel no se puede leer.") from error
    elif suffix.lower() == ".csv":
        try:
            separator = (
                csv.Sniffer().sniff(data.decode("utf-8-sig").splitlines()[0], ",;\t").delimiter
            )
            frame = pd.read_csv(
                stream, sep=separator, header=None, dtype=str, keep_default_na=False
            )
        except (IndexError, csv.Error, UnicodeError, pd.errors.ParserError) as error:
            raise ValueError(
                "Revise la cabecera, el separador y la codificación UTF-8 del CSV."
            ) from error
    else:
        raise ValueError("Elija un archivo CSV o XLSX.")

    if len(frame) < 2:
        raise ValueError("El archivo necesita encabezados y al menos una notificación.")
    frame.columns = frame.iloc[0].str.strip().str.lower()
    frame = frame.iloc[1:].copy()
    if not frame.columns.is_unique or not {"ini_sin", "confirmados"} <= set(frame):
        raise ValueError("Se requieren encabezados únicos, INI_SIN y Confirmados.")
    if {"cod_dpto_r", "cod_mun_r"} <= set(frame):
        dep, mun = frame.cod_dpto_r.str.strip(), frame.cod_mun_r.str.strip()
        if not (dep.str.fullmatch(r"[0-9]{1,2}") & mun.str.fullmatch(r"[0-9]{1,3}")).all():
            raise ValueError("Los códigos de residencia no son válidos.")
        code = dep.str.zfill(2) + mun.str.zfill(3)
    elif key := next((c for c in ("municipality_code", "cod_dpto_o") if c in frame), None):
        code = frame[key].str.strip()
    else:
        raise ValueError(
            "Falta el código DIVIPOLA municipal de cinco dígitos o el par de residencia."
        )
    if not code.str.fullmatch(r"[0-9]{5}").all():
        raise ValueError("Se requiere el DIVIPOLA municipal de cinco dígitos.")
    scoped = code.str.startswith(("50", "73"))
    rows = frame.loc[scoped]
    if rows.empty or not code[scoped].isin(cities).all():
        raise ValueError("Revise los códigos municipales de Meta y Tolima.")
    days = rows.ini_sin.map(parse_date)
    flags = rows.confirmados.str.strip()
    if days.isna().any() or not flags.isin(["0", "1"]).all():
        raise ValueError(
            "Hay fechas INI_SIN inválidas o valores de Confirmados distintos de 0 y 1."
        )
    months = days.map(lambda d: d.isoformat()[:7]).unique()
    if len(months) != 1:
        raise ValueError("Cargue un solo mes de inicio de síntomas.")
    events = {"210": "210", "220": "220", "DENGUE": "210", "DENGUE GRAVE": "220"}
    event = pd.Series("210", index=rows.index)
    for field in ("cod_eve", "nombre_evento"):
        if field in rows:
            parsed = rows[field].str.strip().str.upper().map(events)
            if parsed.isna().any() or (
                field == "nombre_evento" and "cod_eve" in rows and not parsed.equals(event)
            ):
                raise ValueError("Revise el evento de dengue (210) o dengue grave (220).")
            event = parsed
    counts = flags.astype(int).groupby([code[scoped], event]).sum().unstack()
    counts = counts.reindex(columns=["210", "220"]).rename(
        columns={"210": "dengue", "220": "grave"}
    )
    summary = {
        "Filas": len(frame),
        "Confirmados": int(flags.astype(int).sum()),
        "Municipios": len(counts),
        "Fuera de Meta y Tolima": int((~scoped).sum()),
    }
    return months[0], counts, summary


def ranking(model: Model, month: str, counts: pd.DataFrame, cities: pd.Series) -> pd.DataFrame:
    """Recalcular el canal al origen y puntuar municipios elegibles con la política congelada."""
    context = model.context.loc[model.context.year_month.eq(month)].set_index(KEYS[0])
    if context.empty:
        raise ValueError("El mes está fuera de la cobertura de clima e historia del paquete.")
    features = context.reindex(cities.index)[PREDICTORS].copy()
    features[COUNTS[0]] = counts.dengue.reindex(cities.index)
    features[COUNTS[1]] = counts.grave.reindex(cities.index).fillna(features[COUNTS[1]])
    features[COUNTS[2]] = features[COUNTS[0]] + features[COUNTS[1]]
    inputs = features[[COUNTS[0], *CHANNEL[:3]]].dropna()
    features[CHANNEL[3]] = pd.Series(
        {
            code: classify_endemic_zone(current, p25, p50, p75)
            for code, current, p25, p50, p75 in inputs.itertuples(name=None)
        },
        dtype="str",
    )
    ready = features.notna().all(axis=1) & features.zona_canal_t.ne("EXCESO")
    probability = pd.Series(float("nan"), index=cities.index)
    if ready.any():
        values = predict_exported(features.loc[ready], model.state)
        if model.decisions["representation"] == "sigmoid":
            values = apply_sigmoid(values, **model.decisions["calibrator"])
        probability.loc[ready] = values
    status = pd.Series("Historia incompleta", index=cities.index)
    status.loc[features[CLIMATE].isna().any(axis=1)] = "Clima incompleto"
    status.loc[features.zona_canal_t.eq("EXCESO")] = "Exceso en el mes de origen"
    status.loc[features[COUNTS[0]].isna()] = "Sin conteo de dengue"
    status.loc[~cities.index.isin(counts.index)] = "Sin datos en la carga"
    status.loc[ready] = "Bajo el umbral"
    status.loc[probability.ge(model.decisions["threshold"])] = "Alcanza el umbral"
    result = pd.DataFrame(
        {
            "Municipio": cities,
            "Casos": features[COUNTS[0]],
            "Zona en T": features.zona_canal_t,
            "Probabilidad T+2": probability,
            "Resultado": status,
        }
    )
    return result.sort_values(["Probabilidad T+2", "Municipio"], ascending=[False, True])
