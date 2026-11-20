"""Tablero local Streamlit de priorización municipal con el modelo congelado del informe."""

import json
import unicodedata
from pathlib import Path
from xml.etree import ElementTree as ET

import pandas as pd
import streamlit as st
from inferencia import ROOT, geography, load_context, load_model, parse_upload, ranking
from sat_dengue_pipeline.domain.calendar import add_months
from sat_dengue_pipeline.risk.configuration import LEGEND

SELECTED, ELIGIBLE, GRAY = "#155d4b", "#87c6ad", "#d3dce1"
st.set_page_config(page_title="SAT Dengue · Prioridades T+2", layout="wide")


def normalized(name: str) -> str:
    """Emparejar los nombres del catálogo y de los límites municipales."""
    return "".join(c for c in unicodedata.normalize("NFKD", name.lower()) if c.isalnum())


def maps(result: pd.DataFrame) -> None:
    """Marcar en el mapa los ocho priorizados, los demás elegibles y los no elegibles."""
    boundaries = json.loads((ROOT / "app/dashboard/src/lib/municipal-boundaries.json").read_bytes())
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
                "aria-label": f"Prioridades por municipio de {department}",
            },
        )
        for area in boundaries[department.lower()]:
            row = lookup[normalized(area["name"])]
            position = row["Posición"]
            color = SELECTED if row["Priorizado"] else ELIGIBLE if pd.notna(position) else GRAY
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
            label = f"posición {position}" if pd.notna(position) else row["Resultado"]
            ET.SubElement(polygon, "title").text = f"{area['name']} · {label}"
        st.iframe(ET.tostring(svg, encoding="unicode"), height="content")
    st.caption("Verde oscuro · priorizado (8 cupos) / Verde claro · elegible / Gris · no elegible")


def choose(source: str) -> None:
    """Invalidar la inferencia anterior al cambiar el origen del archivo."""
    st.session_state.source = source
    st.session_state.pop("ranking", None)
    st.session_state.pop("upload", None)


@st.cache_resource
def resources() -> tuple:
    """Cargar una sola vez el artefacto congelado y el contexto verificado."""
    model = load_model()
    return model, load_context(model)


def main() -> None:
    """Cargar un mes de notificaciones y calcular bajo demanda el orden de prioridad."""
    st.title("Prioridades municipales de dengue")
    st.write("Meta y Tolima · Orden de atención para el mes T+2")
    try:
        model, contexts = resources()
    except (OSError, ValueError, KeyError):
        st.error(
            "Falta el modelo congelado o el contexto privado de predictores. "
            "Revise modelos/logistica-conclima-t2 y pipeline/data/demo según el README."
        )
        return
    cities = geography()
    months = sorted(contexts)
    st.caption(
        "Modelo congelado logistica-conclima-t2 · Regresión logística con clima · "
        f"Meses de origen disponibles: {months[0]} a {months[-1]}."
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
            help="Una fila por notificación: INI_SIN, COD_DPTO_R, COD_MUN_R y COD_EVE 210/220.",
        )
        if upload is None:
            return
        data, suffix = upload.getvalue(), Path(upload.name).suffix
    elif source == "sample":
        suffix = ".csv"
        period = months[-1]
        data = (
            "COD_DPTO_R,COD_MUN_R,INI_SIN,COD_EVE\n"
            + "\n".join(
                f"{code[:2]},{code[2:]},{period}-01,{event}"
                for code, event in [
                    ("50001", 210),
                    ("50001", 220),
                    ("73001", 210),
                    ("50006", 210),
                    ("73026", 210),
                ]
            )
        ).encode()
        st.caption("Muestra artificial de notificaciones. Usa el mismo modelo congelado.")
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
    if month not in contexts:
        st.warning("El mes está fuera de los orígenes publicados (2024-11 a 2025-10).")
        return
    st.caption(
        "Cada fila es una notificación de dengue o dengue grave, sin filtrar confirmados. "
        "La carga representa el mes completo: un municipio sin filas cuenta cero."
    )
    if st.button("Calcular prioridades T+2", type="primary"):
        try:
            st.session_state.ranking = ranking(model, month, counts, contexts[month])
        except ValueError as error:
            st.error(str(error))
            return
    if "ranking" not in st.session_state:
        return
    result = st.session_state.ranking
    eligible = result.loc[result["Posición"].notna()]
    st.divider()
    st.subheader(f"Prioridades para {add_months(month, 2)}")
    st.caption(
        f"Se priorizan 8 municipios entre {len(eligible)} sin exceso en el origen. "
        "Empates por código DIVIPOLA. " + LEGEND
    )
    left, right = st.columns([3, 2])
    with left:
        st.dataframe(
            eligible.rename_axis("DIVIPOLA"),
            column_order=[
                "Posición",
                "Municipio",
                "Departamento",
                "Notificaciones",
                "Zona en T",
                "Priorizado",
            ],
            width="stretch",
        )
        with st.expander("Municipios no elegibles"):
            st.dataframe(
                result.loc[
                    result["Posición"].isna(),
                    ["Municipio", "Departamento", "Notificaciones", "Resultado"],
                ].rename_axis("DIVIPOLA"),
                width="stretch",
            )
    with right:
        maps(result)
    st.caption(
        "Demostración retrospectiva. La emisión de alertas operativas requiere validación "
        "prospectiva."
    )


main()
