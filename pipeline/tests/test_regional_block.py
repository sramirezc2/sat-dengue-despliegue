"""Bloque regional, catálogo de derivadas y el rezago por mes calendario.

Cada afirmación construye el caso que la discrimina: valores calculados a mano,
un municipio que se excluye de su propio agregado, un hueco de calendario que
tiene que producir una ausencia y no una resta contra el mes equivocado.
"""

import pandas as pd
import pytest

from sat_dengue_pipeline.domain.derived import (
    DERIVED_BLOCKS,
    DERIVED_COLUMNS,
    declared_derived,
)
from sat_dengue_pipeline.domain.regional import REGIONAL_COLUMNS, regional_features


def historia() -> pd.DataFrame:
    """Un departamento con tres municipios y otro con uno solo, cuatro meses."""
    filas = []
    zonas = {
        ("73001", "2020-01"): "EXCESO", ("73001", "2020-02"): "ALERTA",
        ("73002", "2020-01"): "EXITO", ("73002", "2020-02"): "EXCESO",
        ("73003", "2020-01"): "EXCESO", ("73003", "2020-02"): "EXCESO",
        ("50001", "2020-01"): "EXITO", ("50001", "2020-02"): "EXITO",
    }
    casos = {"73001": 10.0, "73002": 20.0, "73003": 40.0, "50001": 5.0}
    for (municipio, mes), zona in zonas.items():
        filas.append(
            {
                "municipality_code": municipio,
                "department_code": municipio[:2],
                "year_month": mes,
                "zona_canal_t": zona,
                "dengue_notifications_count": casos[municipio],
            }
        )
    return pd.DataFrame(filas)


def test_los_agregados_excluyen_al_propio_municipio() -> None:
    """Es la condición que separa el bloque de releer el `zona_canal_t` propio.

    En 2020-01 el departamento 73 tiene a 73001 y 73003 en exceso y a 73002 no.
    Visto desde 73001, los *demás* son 73002 y 73003: uno de dos en exceso, 0,5.
    Visto desde 73002, los demás son los dos en exceso: 1,0. Si el agregado se
    incluyera a sí mismo, los dos verían 2 de 3.
    """
    bloque = regional_features(historia())
    assert bloque.loc[("73001", "2020-01")].presion_exceso_t == pytest.approx(0.5)
    assert bloque.loc[("73002", "2020-01")].presion_exceso_t == pytest.approx(1.0)
    # Y los casos: desde 73001 son los de 73002 y 73003, 60 en total.
    import numpy as np

    assert bloque.loc[("73001", "2020-01")].presion_casos_t == pytest.approx(np.log1p(60.0))


def test_un_departamento_de_un_solo_municipio_no_tiene_presion() -> None:
    """Sin vecinos no hay información, y eso es una ausencia, no un cero.

    Un cero diría «ningún vecino en exceso», que es una afirmación distinta.
    """
    bloque = regional_features(historia())
    assert pd.isna(bloque.loc[("50001", "2020-01")].presion_exceso_t)
    assert pd.isna(bloque.loc[("50001", "2020-02")].presion_exceso_t)


def test_la_velocidad_usa_el_mes_anterior_y_no_la_fila_anterior() -> None:
    """Con un hueco de calendario no hay velocidad; nunca una resta contra t-2."""
    completo = historia()
    con_hueco = completo.query("not (municipality_code == '73001' and year_month == '2020-01')")
    bloque = regional_features(con_hueco)
    assert pd.isna(bloque.loc[("73001", "2020-02")].presion_exceso_vel)
    assert not pd.isna(regional_features(completo).loc[("73001", "2020-02")].presion_exceso_vel)


def test_un_insumo_ausente_falla_con_su_nombre() -> None:
    """Quien lo lea tiene que saber qué columna falta."""
    with pytest.raises(ValueError, match="zona_canal_t"):
        regional_features(historia().drop(columns=["zona_canal_t"]))


def test_el_catalogo_fija_un_solo_orden() -> None:
    """Las columnas van en el orden del catálogo, no en el que se declaren.

    Sin esto, dos recetas con los mismos bloques podrían producir matrices
    internas distintas y el adaptador no tendría contra qué compararlas.
    """
    assert len(DERIVED_COLUMNS) == len(set(DERIVED_COLUMNS)), "sin columnas repetidas"
    g_y_h = declared_derived({"variables_h": True, "variables_g": True})
    h_y_g = declared_derived({"variables_g": True, "variables_h": True})
    assert g_y_h == h_y_g
    assert list(g_y_h) == [c for c in DERIVED_COLUMNS if c in g_y_h]
    assert g_y_h[-3:] == tuple(REGIONAL_COLUMNS)
    assert declared_derived({}) == ()
    # Todo interruptor del catálogo tiene columnas y todas están en el orden.
    for interruptor, bloque in DERIVED_BLOCKS:
        assert bloque, interruptor
        assert set(bloque) <= set(DERIVED_COLUMNS)
