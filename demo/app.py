"""Tablero local Streamlit de priorización municipal con el modelo congelado del informe."""

import json
import unicodedata
from pathlib import Path
from xml.etree import ElementTree as ET

import pandas as pd
import streamlit as st
from configuracion import ROOT
from contexto_paquete import obtain_context
from ejemplos import sample_csv, template_csv
from inferencia import (
    PERCENTAGES,
    POPULATION,
    capacity,
    capacity_warning,
    geography,
    load_model,
    parse_upload,
    ranking,
    select_capacity,
)
from sat_dengue_pipeline.domain.calendar import add_months
from sat_dengue_pipeline.risk.configuration import LEGEND

SELECTED, ELIGIBLE, GRAY = "#155d4b", "#87c6ad", "#d3dce1"
st.set_page_config(page_title="SAT Dengue · Prioridades T+2", layout="wide")


def normalized(name: str) -> str:
    """Emparejar los nombres del catálogo y de los límites municipales."""
    return "".join(c for c in unicodedata.normalize("NFKD", name.lower()) if c.isalnum())


def maps(result: pd.DataFrame) -> None:
    """Marcar la selección simulada, los demás elegibles y los no elegibles."""
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
    st.caption(
        "Verde oscuro · priorizado en la simulación / Verde claro · elegible / Gris · no elegible. "
        "La tabla permite consultar la selección sin depender del color."
    )


def choose(source: str) -> None:
    """Invalidar la inferencia anterior al cambiar el origen del archivo."""
    st.session_state.source = source
    st.session_state.pop("ranking", None)
    st.session_state.pop("upload", None)


@st.cache_resource
def resources() -> tuple:
    """Cargar una sola vez el artefacto congelado y el contexto verificado."""
    model = load_model()
    return model, obtain_context(model)


def main() -> None:
    """Cargar un mes de notificaciones y calcular bajo demanda el orden de prioridad."""
    st.title("Prioridades municipales de dengue")
    st.write("Meta y Tolima · Orden de atención para el mes T+2")
    st.warning(
        "Simulación de capacidad; no corresponde a una capacidad operativa validada "
        "con las secretarías de salud"
    )
    st.caption(
        "Demostración retrospectiva; cambiar la capacidad no produce nueva evidencia "
        "científica. 2025 es evaluación previamente utilizada. " + LEGEND
    )
    st.download_button(
        "Descargar plantilla CSV",
        data=template_csv(),
        file_name="plantilla-notificaciones.csv",
        mime="text/csv",
    )
    st.caption(
        "Complete un mes entero: una fila por notificación de dengue (210) o dengue grave "
        "(220). Un municipio ausente se interpreta como cero notificaciones."
    )
    try:
        model, contexts = resources()
    except (OSError, ValueError, KeyError):
        st.error(
            "El modelo o contexto privado verificado no está disponible. "
            "El administrador debe revisar SATD_DEMO_MODEL_DIR, SATD_DEMO_CONTEXT_DIR "
            "o la configuración del paquete privado según la guía de operación. "
            "No necesita ingresar credenciales."
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
    sample.button("Cargar muestra artificial", on_click=choose, args=("sample",), width="stretch")
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
        data = sample_csv(period)
        st.caption(
            "Datos artificiales: 24 notificaciones inventadas de seis municipios de Meta y "
            "Tolima, con dengue y dengue grave. No representan observaciones ni desenlaces reales."
        )
        st.download_button(
            "Descargar muestra artificial", data=data, file_name="muestra-artificial.csv",
            mime="text/csv",
        )
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
    percentage = st.selectbox(
        "Capacidad simulada de priorización", PERCENTAGES, index=1,
        format_func=lambda value: f"{value} %", key="percentage",
        help="Aplica cupos al mismo ranking; no vuelve a ejecutar el modelo.",
    )
    result = select_capacity(st.session_state.ranking, percentage)
    eligible = result.loc[result["Posición"].notna()]
    st.divider()
    st.subheader(f"Prioridades para {add_months(month, 2)}")
    st.caption(
        f"Porcentaje seleccionado: {percentage} % · Población de referencia: {POPULATION} "
        f"municipios de Meta y Tolima · Redondeo hacia arriba: "
        f"ceil({POPULATION} × {percentage} / 100) = {capacity(percentage)} cupos. "
        f"Elegibles: {len(eligible)} · Seleccionados: {int(result.Priorizado.sum())}. "
        "Se eligen las primeras posiciones entre municipios sin exceso en T, con canal "
        "observado y predictores completos. "
        "Empates por código DIVIPOLA. " + LEGEND
    )
    limitation = capacity_warning(len(eligible), percentage)
    if limitation:
        st.warning(limitation)
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
