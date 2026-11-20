"""Inferencia mensual con el modelo congelado del informe (logistica-conclima-t2)."""

import csv
import hashlib
import io
import json
from pathlib import Path
from xml.etree.ElementTree import ParseError
from zipfile import BadZipFile, ZipFile

import pandas as pd
from openpyxl.utils.exceptions import InvalidFileException
from sat_dengue_pipeline.domain.canonical import COUNTS, KEYS, PREDICTORS
from sat_dengue_pipeline.domain.endemic_channel import CHANNEL, classify_endemic_zone
from sat_dengue_pipeline.raw.producers import epidemiology_normalization
from sat_dengue_pipeline.raw.temporal import parse_date
from sat_dengue_pipeline.risk.frozen import FrozenLogistic, load_artifact
from sat_dengue_pipeline.risk.inference import InferenceCoverage, prioritize

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "modelos/logistica-conclima-t2"
ARTIFACT_SHA256 = "d0a883a7528afd5d3d1fdbe43d44e5c5a396c109ab20ed49845a198ccdb75c8c"
CONTEXT_DIR = ROOT / "pipeline/data/demo"
METADATA = ["department_code", "municipality_name"]
REASONS = {
    "EXCESS_AT_ORIGIN": "Exceso en el mes de origen",
    "ORIGIN_STATE_MISSING": "Sin canal endémico en el origen",
    "REQUIRED_PREDICTORS_MISSING": "Predictores incompletos",
}


def load_model(directory: Path = ARTIFACT) -> FrozenLogistic:
    """Cargar el artefacto congelado y exigir su SHA-256 aprobado.

    La procedencia esperada es la registrada en el propio artefacto: la demo no
    necesita un clon git ni el release crudo para puntuar, y la identidad del
    modelo queda garantizada por el SHA-256 de sus bytes y su manifiesto.
    """
    provenance = json.loads((directory / "model.json").read_bytes())["provenance"]
    return load_artifact(directory, ARTIFACT_SHA256, provenance)


def load_context(model: FrozenLogistic, directory: Path = CONTEXT_DIR) -> dict[str, pd.DataFrame]:
    """Leer el contexto privado por origen y verificar huellas, release y tipos."""
    index = json.loads((directory / "contexto.json").read_bytes())
    if index["raw_manifest_sha256"] != model.payload["provenance"]["raw_manifest_sha256"]:
        raise ValueError("El contexto procede de un release distinto del modelo.")
    dtypes = dict(zip(PREDICTORS, model.payload["state"]["dtypes"], strict=True))
    contexts = {}
    for origin, digest in index["files"].items():
        data = (directory / f"contexto-{origin}.csv").read_bytes()
        if hashlib.sha256(data).hexdigest() != digest:
            raise ValueError("El contexto privado difiere de su índice.")
        frame = pd.read_csv(
            io.BytesIO(data),
            dtype={c: "string" for c in [*KEYS, *METADATA]},
            float_precision="round_trip",
        )
        contexts[origin] = frame.astype(dtypes)
    return contexts


def geography() -> pd.Series:
    """Leer el catálogo municipal de Meta y Tolima."""
    geo = pd.read_csv(ROOT / "pipeline/conf/geografia/divipola_coordenadas.csv", dtype=str)
    return geo.loc[geo.cod_dpto.isin(["50", "73"])].set_index("cod_mpio").nom_mpio


def read_table(data: bytes, suffix: str) -> pd.DataFrame:
    """Leer una hoja Excel o un CSV como texto, con límites de tamaño."""
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
                return book.parse(header=None, dtype=str, keep_default_na=False)
        except (BadZipFile, InvalidFileException, KeyError, ParseError, OSError) as error:
            raise ValueError("El archivo Excel no se puede leer.") from error
    if suffix.lower() == ".csv":
        try:
            separator = (
                csv.Sniffer().sniff(data.decode("utf-8-sig").splitlines()[0], ",;\t").delimiter
            )
            return pd.read_csv(stream, sep=separator, header=None, dtype=str, keep_default_na=False)
        except (IndexError, csv.Error, UnicodeError, pd.errors.ParserError) as error:
            raise ValueError(
                "Revise la cabecera, el separador y la codificación UTF-8 del CSV."
            ) from error
    raise ValueError("Elija un archivo CSV o XLSX.")


def parse_upload(data: bytes, suffix: str, cities: pd.Index) -> tuple[str, pd.DataFrame, dict]:
    """Contar las notificaciones de un mes completo con el productor canónico.

    Cada notificación aceptada cuenta por residencia y evento, sin filtrar
    Confirmados; el total es dengue (210) más dengue grave (220). Un municipio sin
    filas en la carga cuenta cero, igual que en el panel de entrenamiento.
    """
    frame = read_table(data, suffix)
    if len(frame) < 2:
        raise ValueError("El archivo necesita encabezados y al menos una notificación.")
    frame.columns = frame.iloc[0].str.strip().str.upper()
    frame = frame.iloc[1:].copy()
    if not frame.columns.is_unique or not {"INI_SIN", "COD_DPTO_R", "COD_MUN_R"} <= set(frame):
        raise ValueError("Se requieren encabezados únicos, INI_SIN, COD_DPTO_R y COD_MUN_R.")
    days = frame.INI_SIN.map(parse_date)
    if days.isna().any():
        raise ValueError("Hay fechas INI_SIN inválidas.")
    months = days.map(lambda d: d.isoformat()[:7]).unique()
    if len(months) != 1:
        raise ValueError("Cargue un solo mes de inicio de síntomas.")
    events = {"210": "210", "220": "220", "DENGUE": "210", "DENGUE GRAVE": "220"}
    event = pd.Series("210", index=frame.index)
    for field in ("COD_EVE", "NOMBRE_EVENTO"):
        if field in frame:
            parsed = frame[field].str.strip().str.upper().map(events)
            if parsed.isna().any() or (
                field == "NOMBRE_EVENTO" and "COD_EVE" in frame and not parsed.equals(event)
            ):
                raise ValueError("Revise el evento de dengue (210) o dengue grave (220).")
            event = parsed
    frame["COD_EVE"] = event
    month = months[0]
    columns = ["COD_DPTO_R", "COD_MUN_R", "INI_SIN", "COD_EVE"]
    monthly, audit = epidemiology_normalization(
        {
            "dengue_notifications": frame.loc[event.eq("210"), columns],
            "severe_dengue_notifications": frame.loc[event.eq("220"), columns],
        },
        pd.DataFrame({"municipality_code": cities}),
        InferenceCoverage(month, start=month, epi_start=month),
    )
    rejected = {
        reason: sum(a["rejected"][reason] for a in audit.values())
        for reason in ("invalid_residence", "unknown_municipality")
    }
    counts = monthly.set_index(KEYS[0])[COUNTS].reindex(cities, fill_value=0).astype("Int64")
    summary = {
        "Filas": len(frame),
        "Notificaciones": sum(a["accepted"] for a in audit.values()),
        "Municipios con casos": int(counts[COUNTS[2]].gt(0).sum()),
        "Fuera de Meta y Tolima": rejected["unknown_municipality"],
        "Residencia inválida": rejected["invalid_residence"],
    }
    return month, counts, summary


def ranking(
    model: FrozenLogistic, month: str, counts: pd.DataFrame, context: pd.DataFrame
) -> pd.DataFrame:
    """Priorizar con la regla publicada: ocho cupos entre municipios sin exceso en T.

    Los conteos del origen se sustituyen por los de la carga y la zona del canal se
    recalcula con el conteo de dengue, como en la tabla canónica. Rezagos, clima y
    percentiles proceden del contexto del mismo origen. El orden lo decide
    risk.inference.prioritize: puntuación descendente y DIVIPOLA ascendente.
    """
    table = context.set_index(KEYS[0])
    for name in COUNTS:
        table[name] = counts[name].reindex(table.index).astype("Int64")
    table[CHANNEL[3]] = pd.array(
        [
            pd.NA if pd.isna(p25) or pd.isna(now) else classify_endemic_zone(now, p25, p50, p75)
            for now, p25, p50, p75 in table[[COUNTS[0], *CHANNEL[:3]]].itertuples(
                index=False, name=None
            )
        ],
        dtype="string",
    )
    table = table.reset_index()[[*KEYS, *METADATA, *PREDICTORS]]
    roles = {"key": KEYS, "metadata": METADATA, "feature": PREDICTORS, "target": [], "control": []}
    rows, _ = prioritize(table, {"column_roles": roles}, month, model)
    result = pd.DataFrame(rows).set_index("municipality_code")
    current = table.set_index(KEYS[0])
    return pd.DataFrame(
        {
            "Posición": result.risk_rank.astype("Int64"),
            "Municipio": result.municipality_name,
            "Departamento": result.department_name,
            "Notificaciones": current[COUNTS[2]],
            "Zona en T": current[CHANNEL[3]],
            "Priorizado": result.selected_for_attention,
            "Resultado": result.ineligibility_reason.map(REASONS).fillna("Elegible"),
        }
    ).sort_values(["Posición", "Municipio"], na_position="last")
