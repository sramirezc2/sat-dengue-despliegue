"""Pruebas del retroanálisis de ventana expansiva sobre el panel canónico artificial."""

from pathlib import Path

import pytest
import yaml
from fixtures.canonical_fixture import make_panel

import sat_dengue_pipeline.pipelines.retroanalisis.nodes as nodos
from sat_dengue_pipeline.domain.canonical import build_table
from sat_dengue_pipeline.evaluation import validacion_anual as va
from sat_dengue_pipeline.evaluation.retroanalisis import predicciones_rolling
from sat_dengue_pipeline.pipelines.retroanalisis.nodes import retroanalisis

CONFIG = Path(__file__).resolve().parents[1] / "conf/experiments/EXP001.yml"


@pytest.fixture(scope="module")
def corrida():
    """Panel canónico artificial y predicciones por origen desde 2023-06 en T+1."""
    table, schema = build_table(make_panel())
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    preds, omitidos = predicciones_rolling(table, schema, config, 1, "2023-06")
    return table, preds, omitidos


def test_un_fold_por_origen_y_omitidos_registrados(corrida) -> None:
    """Cada mes de origen es un fold propio; los meses sin soporte quedan registrados."""
    _, preds, omitidos = corrida
    assert preds.fold_id.nunique() >= 2
    assert preds.groupby("fold_id").origin_period.nunique().eq(1).all()
    assert not preds.target_period.ge("2025-01").any()
    assert omitidos and all("motivo" in o for o in omitidos)


def test_f_del_primer_anio_sale_del_panel(corrida) -> None:
    """Sin predicciones del año previo, f se elige con las filas del panel de ese año."""
    table, preds, _ = corrida
    _, anio, _ = va.validar_candidato(
        table, preds, {"candidato": preds.candidate.iloc[0], "horizonte": 1}
    )
    primero = anio.sort_values("anio").iloc[0]
    assert not preds.target_period.str.startswith(str(primero.anio - 1)).any()
    historia = va.historia_desde_panel(table, 1)
    assert (historia.anio_objetivo == primero.anio - 1).any()
    assert primero.f == va.elegir_f(historia[historia.anio_objetivo == primero.anio - 1], True)


def test_salida_solo_bajo_data(tmp_path, monkeypatch) -> None:
    """El nodo se niega a escribir fuera de data/."""
    params = {"configuracion": str(CONFIG), "horizontes": [], "primer_origen": "2019-01",
              "ultimo_objetivo": "2024-12", "salida": str(tmp_path)}
    table, schema = build_table(make_panel())
    monkeypatch.setattr(nodos, "load_canonical", lambda _: (table, schema))
    with pytest.raises(ValueError):
        retroanalisis(object(), params)
