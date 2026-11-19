"""Tablero local Streamlit de inferencia municipal con el modelo EXP315."""

import json
import unicodedata
from pathlib import Path
from xml.etree import ElementTree as ET

import pandas as pd
import streamlit as st
from inferencia import ROOT, geography, load_model, parse_upload, ranking
from sat_dengue_pipeline.domain.calendar import add_months

COLORS = ("#d6ece5", "#87c6ad", "#338d72", "#155d4b")
GRAY = "#d3dce1"
st.set_page_config(page_title="SAT Dengue · Inferencia T+2", layout="wide")


def normalized(name: str) -> str:
    """Emparejar los nombres del catálogo y de los límites municipales."""
    return "".join(c for c in unicodedata.normalize("NFKD", name.lower()) if c.isalnum())


def maps(result: pd.DataFrame) -> None:
    """Colorear los polígonos del tablero por resultado del mismo ranking."""
    boundaries = json.loads((ROOT / "app/dashboard/src/lib/municipal-boundaries.json").read_bytes())
    ranks = result["Puntuación T+2"].rank(method="average", pct=True)
    for department, prefix in [("Tolima", "73"), ("Meta", "50")]:
        rows = result[result.index.str.startswith(prefix)]
        lookup = {normalized(row["Municipio"]): row for _, row in rows.iterrows()}
        st.markdown(f"**{department}**")
        svg = ET.Element(
            "svg",
            {
                "viewBox": "0 0 1000 400",
                "width": "100%",
                "role": "img",
                "aria-label": f"Resultados por municipio de {department}",
            },
        )
        for area in boundaries[department.lower()]:
            row = lookup[normalized(area["name"])]
            status, p = row["Resultado"], row["Puntuación T+2"]
            code = row.name
            color = COLORS[min(int(ranks[code] * 4), 3)] if pd.notna(p) else GRAY
            polygon = ET.SubElement(
                svg,
                "path",
                {
                    "d": area["path"],
                    "fill": color,
                    "fill-rule": "evenodd",
                    "stroke": "#ffffff",
                    "stroke-width": "1.7",
                },
            )
            risk = f" · puntuación {p:.3f}" if pd.notna(p) else ""
            ET.SubElement(polygon, "title").text = f"{area['name']}{risk} · {status}"
        st.iframe(ET.tostring(svg, encoding="unicode"), height="content")
    st.caption("Verde claro a oscuro · menor a mayor puntuación relativa / Gris · Sin estimación")


def choose(source: str) -> None:
    """Invalidar la inferencia anterior al cambiar el origen del archivo."""
    st.session_state.source = source
    st.session_state.pop("ranking", None)
    st.session_state.pop("upload", None)


def main() -> None:
    """Cargar una entrada, revisar su resumen y ejecutar inferencia bajo demanda."""
    st.title("Inferencia municipal de dengue")
    st.write("Meta y Tolima · Puntuación de inicio de exceso en el mes T+2")
    try:
        model = load_model()
    except (OSError, ValueError, KeyError):
        st.error(
            "Falta el paquete verificado de EXP315. Revise el inventario y los archivos "
            "privados model.json y context.csv según el README."
        )
        return
    cities = geography()
    months = sorted(model.context.year_month.unique())
    st.caption(
        f"EXP315 · Regresión logística con clima · Meses disponibles: {months[0]} a "
        f"{months[-1]}. El release contiene datos históricos consolidados."
    )
    st.subheader("Notificaciones del mes")
    uploader, sample = st.columns(2)
    uploader.button("Subir archivo", on_click=choose, args=("file",), width="stretch")
    sample.button("Cargar muestra dummy", on_click=choose, args=("sample",), width="stretch")
    source = st.session_state.get("source")
    if source == "file":
        upload = st.file_uploader(
            "Archivo mensual CSV o Excel",
            type=["csv", "xlsx"],
            key="upload",
            max_upload_size=5,
            on_change=lambda: st.session_state.pop("ranking", None),
            help="INI_SIN y código municipal. COD_EVE distingue 210 y 220.",
        )
        if upload is None:
            return
        data, suffix = upload.getvalue(), Path(upload.name).suffix
    elif source == "sample":
        suffix = ".csv"
        period = months[-1]
        data = (
            "cod_DPTO_O,INI_SIN,Confirmados,COD_EVE\n"
            + "\n".join(
                f"{code},{period}-01,{flag},210"
                for code, flag in [
                    ("50001", 1),
                    ("73001", 1),
                    ("50006", 0),
                    ("73026", 0),
                ]
            )
        ).encode()
        st.caption("Muestra artificial de notificaciones. Usa el mismo modelo entrenado.")
    else:
        return
    try:
        month, counts, summary = parse_upload(data, suffix, cities.index)
    except ValueError as error:
        st.error(str(error))
        return
    for col, (label, value) in zip(st.columns(len(summary)), summary.items(), strict=True):
        col.metric(label, value)
    st.write(f"Mes de origen **{month}** · Mes objetivo **{add_months(month, 2)}**")
    if month not in months:
        st.warning("El mes está fuera de la cobertura verificada de clima e historia.")
        return
    st.caption(
        "Cada fila es una notificación. El conteo grave se toma del contexto histórico "
        "si el archivo no contiene ese evento para el municipio."
    )
    if st.button("Calcular ranking T+2", type="primary"):
        st.session_state.ranking = ranking(model, month, counts, cities)
    if "ranking" not in st.session_state:
        return
    result = st.session_state.ranking
    eligible = result.loc[result["Puntuación T+2"].notna()].copy()
    st.divider()
    st.subheader(f"Priorización para {add_months(month, 2)}")
    st.caption(
        f"{len(eligible)} municipios con puntuación. "
        "Un valor mayor indica mayor prioridad relativa. "
        "El evento es el paso de un mes sin exceso (T+1) a uno con exceso (T+2)."
    )
    far = next(
        record
        for record in model.decisions["metrics"]["candidate"]
        if record["metric"] == "false_alarm_ratio"
    )
    if far["evaluable"]:
        st.caption(
            f"Evaluación histórica: {far['numerator']} de {far['denominator']} señales "
            f"fueron falsas alarmas ({far['value']:.1%})."
        )
    left, right = st.columns([3, 2])
    with left:
        if eligible.empty:
            st.info("Ningún municipio de la carga cumple las condiciones del modelo.")
        else:
            st.dataframe(
                eligible.rename_axis("DIVIPOLA"),
                column_order=[
                    "Municipio",
                    "Notificaciones",
                    "Fuente dengue grave",
                    "Zona en T",
                    "Puntuación T+2",
                    "Resultado",
                ],
                column_config={"Puntuación T+2": st.column_config.NumberColumn(format="%.2f")},
                width="stretch",
            )
        with st.expander("Municipios sin estimación"):
            st.dataframe(
                result.loc[
                    result["Puntuación T+2"].isna(),
                    ["Municipio", "Notificaciones", "Resultado"],
                ],
                width="stretch",
            )
    with right:
        maps(result)
    st.caption(
        f"Ejecución {model.execution} · Demostración histórica. "
        "La emisión de alertas operativas requiere validación prospectiva."
    )


main()
