"""Tablero local Streamlit de priorización municipal con el modelo congelado del informe."""

import json
import unicodedata
from pathlib import Path
from xml.etree import ElementTree as ET

import pandas as pd
import streamlit as st
from configuracion import ROOT
from contexto_paquete import obtain_context
from ejemplos import SAMPLE_FILENAME, sample_csv
from inferencia import (
    PERCENTAGES,
    POPULATION,
    capacity,
    capacity_warning,
    compare_priorities,
    geography,
    load_model,
    parse_upload,
    ranking,
    select_capacity,
)
from respaldo_cientifico import (
    INTRODUCTION,
    chart_data,
    comparison_chart,
    descriptive_metrics,
    load_support,
    spanish,
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
    for column, (department, prefix) in zip(
        st.columns(2), [("Tolima", "73"), ("Meta", "50")], strict=True,
    ):
        with column:
            rows = result[result.index.str.startswith(prefix)]
            lookup = {normalized(row["Municipio"]): row for _, row in rows.iterrows()}
            st.markdown(f"**{department}**")
            # Marco común con margen para todos los polígonos de ambos departamentos.
            svg = ET.Element(
                "svg",
                {
                    "viewBox": "270 0 460 400",
                    "height": "200",
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


def scientific_support() -> None:
    """Mostrar historia de la receta; un error de respaldo no afecta al ranking actual."""
    try:
        support = load_support()
    except (OSError, ValueError, KeyError, TypeError):
        st.error("No se puede mostrar el respaldo científico: el archivo está ausente o inválido.")
        return
    st.write(INTRODUCTION)
    counts = support["counts"]
    intervals = support["intervals"]
    sensitivity, burden = chart_data(support)
    dark = st.context.theme.type == "dark"
    st.markdown("**Resultado histórico principal T+2**")
    st.altair_chart(
        comparison_chart(sensitivity, "Inicios anticipados (%)", 100, dark=dark), width="stretch",
    )
    difference = intervals["sensitivity_difference_pp"]
    st.write(
        f"Ventaja del modelo: {spanish(difference['estimate'], signed=True)} puntos porcentuales. "
        f"IC del 95 %: {spanish(difference['low'], signed=True)} a "
        f"{spanish(difference['high'], signed=True)}."
    )
    st.caption(
        "Confirmación retrospectiva 2023–2024, T+2. Presupuesto nominal del 10 %: "
        f"{counts['alerts_per_method']} alertas por método durante {support['origin_months']} "
        f"meses, equivalentes a {spanish(counts['alerts_per_method'] / support['origin_months'])} "
        "alertas mensuales."
    )
    st.markdown("**Carga de falsas alertas**")
    st.altair_chart(
        comparison_chart(
            burden, ["Falsas alertas por cada 100", "municipio-mes evaluables"], 25, dark=dark,
        ),
        width="stretch",
    )
    difference = intervals["false_alerts_difference_per100"]
    st.write(
        f"Diferencia: {spanish(difference['estimate'], 2)} falsas alertas por cada 100 "
        f"municipio-mes. IC del 95 %: {spanish(difference['low'], 2)} a "
        f"{spanish(difference['high'], 2)}."
    )
    st.caption(
        "Una falsa alerta corresponde a un municipio priorizado en el que no se observó "
        "el inicio de exceso definido para el mes objetivo."
    )
    metrics = descriptive_metrics(support)
    cards = (
        ("Sensibilidad", f"{spanish(100 * metrics['sensitivity'])} %",
         f"{counts['model_anticipated']} / {counts['evaluable_onsets']}. "
         "De los inicios reales, cuántos anticipó."),
        ("Precisión", f"{spanish(100 * metrics['precision'])} %",
         f"{counts['model_anticipated']} / {counts['alerts_per_method']}. "
         "De las alertas emitidas, cuántas anticiparon un inicio."),
        ("F1", spanish(metrics['f1'], 3),
         f"2 × {counts['model_anticipated']} / ({counts['alerts_per_method']} + "
         f"{counts['evaluable_onsets']}). Balance entre precisión y sensibilidad."),
        ("Falsas alertas por inicio anticipado", spanish(metrics['false_per_hit'], 2),
         f"{counts['alerts_per_method'] - counts['model_anticipated']} / "
         f"{counts['model_anticipated']}. Falsas alertas por cada inicio anticipado."),
    )
    for column, (label, value, definition) in zip(st.columns(4), cards, strict=True):
        column.markdown(f"**{label}**")
        column.metric(label, value, label_visibility="collapsed")
        column.caption(definition)


def priority_comparison(
    ordered: pd.DataFrame, counts: pd.DataFrame, context: pd.DataFrame, percentage: int,
) -> None:
    """Presentar coincidencias de listas; aislar errores sin afectar otros resultados."""
    st.write(
        "Compara los municipios priorizados por el modelo y las alertas generadas por el "
        "canal endémico con la información cargada. No determina cuál método acertará, "
        "porque aún no se conocen los desenlaces de T+2."
    )
    try:
        comparison = compare_priorities(ordered, counts, context, percentage)
    except (ValueError, KeyError, TypeError, ArithmeticError):
        st.error(
            "No se puede calcular la comparación de prioridades. Revise los conteos y "
            "el P75 histórico de T+2 del contexto; no se imputan valores."
        )
        return
    categories = comparison["Comparación"].value_counts()
    cards = (
        ("Coinciden", "Ambos", "Seleccionados tanto por el modelo como por el canal."),
        ("Solo modelo", "Solo modelo", "Seleccionados por el modelo, pero no por el canal."),
        ("Solo canal", "Solo canal", "Alertados por el canal, fuera del top del modelo."),
    )
    for column, (label, category, definition) in zip(st.columns(3), cards, strict=True):
        column.metric(label, int(categories.get(category, 0)))
        column.caption(definition)
    st.caption(
        f"Capacidad simulada: {percentage} % · Cupos máximos: {capacity(percentage)} · "
        f"Alertas del modelo: {int(comparison['Comparación'].ne('Solo canal').sum())} · "
        f"Alertas del canal: {int(comparison['Alerta canal'].sum())}. "
        "El canal utiliza solo los municipios que superan su umbral; puede emitir menos alertas "
        "que cupos disponibles."
    )
    st.dataframe(comparison, width="stretch")
    st.caption(
        "Esta comparación describe las listas generadas con los datos cargados; "
        "no mide aciertos ni desempeño."
    )


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
        "científica. Las alertas de 2025 no se utilizan para evaluar aciertos ni medir "
        "el desempeño del modelo. " + LEGEND
    )
    try:
        model, contexts = resources()
    except (OSError, ValueError, KeyError):
        st.error(
            "El modelo o contexto verificado no está disponible. "
            "El administrador debe revisar SATD_DEMO_MODEL_DIR, SATD_DEMO_CONTEXT_DIR "
            "o la configuración del paquete según la guía de operación. "
            "No necesita ingresar credenciales."
        )
        return
    cities = geography()
    months = sorted(contexts)
    artificial_sample = sample_csv(months[-1])
    st.caption(
        "Modelo congelado logistica-conclima-t2 · Regresión logística con clima · "
        f"Meses de origen disponibles: {months[0]} a {months[-1]}."
    )
    st.download_button(
        "Descargar plantilla CSV", data=artificial_sample,
        file_name=SAMPLE_FILENAME, mime="text/csv",
    )
    st.caption(
        "Descargue un archivo de ejemplo con datos artificiales, listo para cargar o modificar. "
        "Complete un mes entero: una fila por notificación de dengue (210) o dengue grave "
        "(220). Un municipio ausente se interpreta como cero notificaciones."
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
        data = artificial_sample
        st.caption(
            "Datos artificiales: 55 notificaciones inventadas de ocho municipios de Meta y "
            "Tolima, con dengue y dengue grave. No representan observaciones ni desenlaces reales."
        )
        st.download_button(
            "Descargar muestra artificial", data=artificial_sample, file_name=SAMPLE_FILENAME,
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
    maps(result)
    st.dataframe(
        result.loc[result.Priorizado].sort_values("Posición").rename_axis("DIVIPOLA"),
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
    st.caption(
        "Demostración retrospectiva. La emisión de alertas operativas requiere validación "
        "prospectiva."
    )
    with st.expander("Comparación de prioridades del mes", expanded=False):
        priority_comparison(st.session_state.ranking, counts, contexts[month], percentage)
    with st.expander("Respaldo científico del modelo", expanded=False):
        scientific_support()


main()
