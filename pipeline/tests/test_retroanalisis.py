"""Pruebas del retroanálisis de ventana expansiva sobre el panel canónico artificial."""

from pathlib import Path

import pandas as pd
import pytest
import yaml
from fixtures.canonical_fixture import make_panel

import sat_dengue_pipeline.pipelines.retroanalisis.nodes as nodos
from sat_dengue_pipeline.domain.canonical import build_table
from sat_dengue_pipeline.domain.margin import MARGIN_COLUMNS
from sat_dengue_pipeline.evaluation import validacion_anual as va
from sat_dengue_pipeline.evaluation.retroanalisis import KEYS, conjunto_comun, predicciones_rolling
from sat_dengue_pipeline.pipelines.retroanalisis.nodes import retroanalisis

CONFIG = Path(__file__).resolve().parents[1] / "conf/experiments/EXP001.yml"
RECETAS = Path(__file__).resolve().parents[1] / "conf/retroanalisis"


def _config_receta(nombre: str) -> dict:
    """Receta versionada del retroanálisis, por nombre de archivo."""
    return yaml.safe_load((RECETAS / f"{nombre}.yml").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def corrida():
    """Panel canónico artificial y predicciones por origen desde 2023-06 en T+1."""
    table, schema = build_table(make_panel())
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    preds, omitidos, _ = predicciones_rolling(table, schema, config, 1, "2023-06")
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


def params_artificiales(**cambios) -> dict:
    """Receta mínima declarando las exigencias que el panel artificial sí cumple."""
    params = {
        "configuracion": str(CONFIG),
        "horizontes": [],
        "primer_origen": "2023-06",
        "ultimo_objetivo": "2024-12",
        "primer_entrenamiento": "2018-01",
        "cobertura_desde": "2018-01",
        "municipios_minimos": 2,
        "salida": "data/prueba-retroanalisis",
    }
    params.update(cambios)
    return params


def test_salida_solo_bajo_data(tmp_path, monkeypatch) -> None:
    """El nodo se niega a escribir fuera de data/."""
    params = params_artificiales(salida=str(tmp_path))
    table, schema = build_table(make_panel())
    monkeypatch.setattr(nodos, "load_canonical", lambda _: (table, schema))
    with pytest.raises(ValueError, match="data/"):
        retroanalisis(object(), params)


def test_un_panel_que_no_sostiene_la_medicion_no_se_mide(tmp_path, monkeypatch) -> None:
    """El fixture sintético contra las exigencias reales: falla antes de medir.

    Esta es la corrida que reportaba éxito en 6,3 segundos: `canonical.mode`
    sintético, dos municipios desde 2018-01, los 163 orígenes omitidos y tres
    CSV vacíos. La guarda tiene que nombrar el modo canónico, porque es lo que
    hay que cambiar.
    """
    table, schema = build_table(make_panel())
    monkeypatch.setattr(nodos, "load_canonical", lambda _: (table, schema))
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValueError, match="approved"):
        retroanalisis(object(), params_artificiales(cobertura_desde="2007-01"))
    with pytest.raises(ValueError, match="approved"):
        retroanalisis(object(), params_artificiales(municipios_minimos=76))
    # Y el panel vacío —un filtro de departamentos que no existe— tampoco mide.
    with pytest.raises(ValueError, match="departamentos"):
        retroanalisis(object(), params_artificiales(departamentos=["99"]))
    assert not (tmp_path / "data/prueba-retroanalisis").exists()


def test_un_horizonte_sin_folds_no_reporta_exito(tmp_path, monkeypatch) -> None:
    """Sin folds evaluables el nodo falla y deja el diagnóstico, no un resumen vacío."""
    table, schema = build_table(make_panel())
    vacias = pd.DataFrame(columns=["fold_id", "candidate", "target_period"])
    omitidos = [{"origin_period": "2023-06", "motivo": "Fold sin soporte"}]
    monkeypatch.setattr(nodos, "load_canonical", lambda _: (table, schema))
    monkeypatch.setattr(
        nodos, "predicciones_rolling", lambda *a, **k: (vacias, omitidos, {"filas_comunes": 0})
    )
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValueError, match="sin folds en T\\+1"):
        retroanalisis(object(), params_artificiales(horizontes=[1]))
    salida = tmp_path / "data/prueba-retroanalisis"
    assert (salida / "omitidos.csv").exists()
    assert not (salida / "resumen.csv").exists()


def test_el_panel_declarado_si_se_mide(tmp_path, monkeypatch) -> None:
    """La guarda no es un bloqueo permanente: lo declarado y sostenible sí corre.

    Sin esta prueba, una guarda que rechazara todo pasaría las dos anteriores.
    """
    table, schema = build_table(make_panel())
    monkeypatch.setattr(nodos, "load_canonical", lambda _: (table, schema))
    monkeypatch.chdir(tmp_path)
    resumen, por_anio, curva, omitidos = retroanalisis(
        object(), params_artificiales(horizontes=[1])
    )
    assert not resumen.empty and not por_anio.empty and not curva.empty
    assert (tmp_path / "data/prueba-retroanalisis/resumen.csv").exists()
    assert {"horizonte", "receta"} <= set(omitidos.columns)
    # El quinto CSV audita el conjunto común, aunque no vuelva en la tupla.
    conjunto = pd.read_csv(tmp_path / "data/prueba-retroanalisis/conjunto.csv")
    assert conjunto.filas_comunes.gt(0).all()
    assert conjunto.filas_preparadas.ge(conjunto.filas_comunes).all()
    # El sexto guarda el puntaje de cada fila evaluada, por receta.
    preds = pd.read_csv(tmp_path / "data/prueba-retroanalisis/predicciones.csv")
    assert {"receta", "raw_probability", "origin_period", "municipality_code"} <= set(
        preds.columns
    )
    assert 0 < len(preds) <= int(conjunto.filas_comunes.sum())


def test_respeta_demora_de_etiqueta() -> None:
    """Con demora de etiqueta, ningún objetivo deja su etiqueta en el periodo reservado."""
    table, schema = build_table(make_panel())
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    assert config["label_delay_months"] >= 1
    preds, _, _ = predicciones_rolling(table, schema, config, 1, "2023-06")
    ultimo = max(preds.target_period)
    assert str(pd.Period(ultimo, freq="M") + config["label_delay_months"]) <= "2024-12"


def _preparacion_del_panel(cfg: dict, horizonte: int = 1):
    """Preparar el panel artificial con una receta, sin correr folds."""
    from sat_dengue_pipeline.domain.calendar import add_months
    from sat_dengue_pipeline.preparation import prepare_horizon

    table, schema = build_table(make_panel())
    demora = cfg["label_delay_months"]
    disponible = table.year_month.map(lambda t: add_months(t, horizonte + demora))
    origins = table.loc[disponible.le("2024-12"), KEYS].reset_index(drop=True)
    _, _, prepared, _ = prepare_horizon(
        table, schema, origins, horizonte, cfg["predictor_availability"]
    )
    return table, prepared


def test_el_conjunto_de_filas_es_el_mismo_con_g_y_sin_g() -> None:
    """La propiedad que hace atribuible la comparación entre las dos recetas.

    Si el filtro del bloque se aplicara solo cuando G está encendida, las dos
    corridas entrenarían sobre conjuntos distintos y la diferencia entre ellas
    dejaría de ser atribuible al bloque. Aquí se mide que las claves coinciden
    exactamente y que lo único que cambia es el ancho de X.
    """
    base, g = _config_receta("logistica_sin_clima"), _config_receta("logistica_g")
    table, prepared = _preparacion_del_panel(base)
    sin_g, derivadas_base, cobertura_base = conjunto_comun(prepared, table, 1, base["preparation"])
    con_g, derivadas_g, cobertura_g = conjunto_comun(prepared, table, 1, g["preparation"])
    pd.testing.assert_frame_equal(sin_g.keys, con_g.keys)
    assert cobertura_base == cobertura_g
    assert cobertura_base["filas_sin_bloque"] > 0, "el panel artificial debe ejercer el filtro"
    assert derivadas_base == () and derivadas_g == tuple(MARGIN_COLUMNS)
    assert list(con_g.X) == [*list(sin_g.X), *MARGIN_COLUMNS]
    assert not con_g.X[MARGIN_COLUMNS].isna().any().any()


def test_el_arnes_acepta_las_derivadas_solo_declaradas() -> None:
    """from_prepared pasa el bloque al arnés; sin declararlo, el arnés lo rechaza."""
    from sat_dengue_pipeline.experiments.rolling import from_prepared

    g = _config_receta("logistica_g")
    table, prepared = _preparacion_del_panel(g)
    con_g, derivadas, _ = conjunto_comun(prepared, table, 1, g["preparation"])
    data = from_prepared(con_g, 1, label_delay_months=g["label_delay_months"], derived=derivadas)
    assert data.derived == tuple(MARGIN_COLUMNS)
    assert list(data.X)[-6:] == MARGIN_COLUMNS
    with pytest.raises(ValueError):
        from_prepared(con_g, 1, label_delay_months=g["label_delay_months"])
