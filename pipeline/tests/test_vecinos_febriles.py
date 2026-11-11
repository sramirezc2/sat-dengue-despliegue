"""Bloques de vecinos y de febriles: valores a mano, exclusión del propio y fuga.

Cada afirmación construye el caso que la discrimina: cuatro municipios en línea, de
modo que los vecinos más cercanos se saben de antemano; un mes sin notificaciones;
y un panel con un municipio sin coordenadas, que tiene que dejar el bloque como no
aplicable en vez de vaciar filas.
"""

import numpy as np
import pandas as pd
import pytest

from sat_dengue_pipeline.domain.derived import DERIVED_COLUMNS, declared_derived
from sat_dengue_pipeline.domain.febriles import FEBRILES_COLUMNS, febriles_features
from sat_dengue_pipeline.domain.vecinos import (
    VECINOS_COLUMNS,
    leer_coordenadas,
    vecinos_features,
    vecinos_mas_cercanos,
)

# Cuatro municipios sobre el ecuador, a 1, 2 y 4 grados del primero.
COORDS = pd.DataFrame(
    {
        "cod_mpio": ["73001", "73002", "73003", "73004"],
        "longitud": [0.0, 1.0, 2.0, 4.0],
        "latitud": [0.0, 0.0, 0.0, 0.0],
    }
)


def historia() -> pd.DataFrame:
    """Cuatro municipios, dos meses, con casos y zonas conocidos."""
    filas = []
    casos = {"73001": 1.0, "73002": 10.0, "73003": 100.0, "73004": 1000.0}
    zonas = {"73001": "EXITO", "73002": "EXCESO", "73003": "EXCESO", "73004": "EXITO"}
    for mes, factor in (("2020-01", 1.0), ("2020-02", 2.0)):
        for municipio, c in casos.items():
            filas.append(
                {
                    "municipality_code": municipio,
                    "year_month": mes,
                    "zona_canal_t": zonas[municipio],
                    "dengue_notifications_count": c * factor,
                    "total_notifications_count": c * factor * 2,
                }
            )
    return pd.DataFrame(filas)


def test_los_vecinos_son_los_mas_cercanos_y_nunca_el_propio() -> None:
    """Con k = 2, el primero tiene como vecinos al segundo y al tercero."""
    vecinos = vecinos_mas_cercanos(list(COORDS.cod_mpio), COORDS, k=2)
    assert vecinos["73001"] == ["73002", "73003"]
    assert vecinos["73004"] == ["73003", "73002"]
    assert all(m not in vs for m, vs in vecinos.items())


def test_los_agregados_de_vecinos_se_calculan_a_mano() -> None:
    """El primero, con k = 2, suma los casos de sus dos vecinos y promedia su exceso."""
    bloque = vecinos_features(historia(), COORDS, k=2)
    assert list(bloque.columns) == VECINOS_COLUMNS
    fila = bloque.loc[("73001", "2020-01")]
    assert fila.vecinos_casos_t == pytest.approx(np.log1p(110.0))
    assert fila.vecinos_exceso_t == pytest.approx(1.0)
    febrero = bloque.loc[("73001", "2020-02")]
    assert febrero.vecinos_casos_vel == pytest.approx(np.log1p(220.0) - np.log1p(110.0))
    assert np.isnan(fila.vecinos_casos_vel)


def test_sin_coordenadas_el_bloque_no_aplica() -> None:
    """Un municipio sin coordenadas deja el bloque ausente, no filas vacías sueltas."""
    bloque = vecinos_features(historia(), COORDS.iloc[:3], k=2)
    assert bloque.isna().all().all()


def test_febriles_se_calculan_a_mano_y_toleran_meses_sin_notificaciones() -> None:
    """La proporción es dengue / total, y 0 cuando no hubo notificaciones."""
    h = historia()
    h.loc[(h.municipality_code == "73001") & (h.year_month == "2020-01"), :] = [
        "73001",
        "2020-01",
        "EXITO",
        0.0,
        0.0,
    ]
    bloque = febriles_features(h)
    assert list(bloque.columns) == FEBRILES_COLUMNS
    assert bloque.loc[("73002", "2020-01")].prop_dengue_t == pytest.approx(0.5)
    assert bloque.loc[("73002", "2020-01")].otros_febriles_t == pytest.approx(np.log1p(10.0))
    assert bloque.loc[("73001", "2020-01")].prop_dengue_t == 0.0
    assert bloque.loc[("73001", "2020-01")].otros_febriles_t == 0.0


def test_los_bloques_nuevos_entran_al_catalogo_al_final() -> None:
    """Sus columnas van al final del orden canónico y se declaran con su interruptor."""
    assert list(DERIVED_COLUMNS[-6:]) == [*FEBRILES_COLUMNS, *VECINOS_COLUMNS]
    assert declared_derived({"variables_vecinos": True}) == tuple(VECINOS_COLUMNS)
    assert declared_derived({"variables_febriles": True}) == tuple(FEBRILES_COLUMNS)


def test_las_coordenadas_versionadas_cubren_tolima_y_meta() -> None:
    """Los 76 municipios del panel de referencia tienen centroide DIVIPOLA."""
    co = leer_coordenadas()
    assert {"73", "50"} <= set(co.cod_mpio.str[:2])
    assert co.cod_mpio.str[:2].isin(["73", "50"]).sum() == 76
    assert co.latitud.notna().all() and co.longitud.notna().all()
