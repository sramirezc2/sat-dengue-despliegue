"""Bloque de presión epidémica regional: las tres variables de la línea H.

Qué es y por qué existe
-----------------------

La tanda 46 midió el techo: al presupuesto del 10 %, en T+1, **299 de los 641
inicios no los anticipa nadie**, y el 52 % de esos arranca con **cero casos** en
el mes de origen. Su mediana de casos sobre P75 es 0,00.

Un municipio en cero no tiene señal propia. Ni sus casos, ni sus rezagos, ni su
margen al umbral dicen nada, porque todos valen lo mismo. Lo único que puede
anunciar un brote ahí es lo que está pasando alrededor.

Dónde vive y por qué aquí
-------------------------

Igual que el bloque de margen: **no entra a la tabla canónica**. Son derivadas
deterministas de columnas que ya están en ella, y agregarlas allá cambiaría el
digest del artefacto y la certificación N=3. Se construyen en preparación.

De dónde sale cada una
----------------------

Con el departamento del municipio y el mes de origen, y **excluyendo siempre al
propio municipio** de los agregados:

    presion_exceso_t    = municipios del departamento en EXCESO / municipios con
                          zona conocida, ambos sin contar el propio
    presion_exceso_vel  = presion_exceso_t menos su valor del mes anterior
    presion_casos_t     = log1p de los casos de dengue de los demás municipios

La exclusión del propio municipio no es cosmética. Sin ella la columna reencodea
el `zona_canal_t` que el modelo ya tiene, y mediríamos la capacidad del modelo de
leerse a sí mismo en vez de la información del vecindario. Es el mismo error que
la tanda 13 encontró en el bloque G, anticipado.

Fuga
----

Las tres son del mes de origen, la misma disponibilidad que los casos propios.
Ninguna mira hacia adelante. La velocidad es una diferencia contra el mes
calendario anterior, buscado por su nombre y no por su posición, de modo que un
hueco de calendario produce una ausencia en vez de una resta contra el mes
equivocado.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .canonical import KEYS

REGIONAL_COLUMNS = [
    "presion_exceso_t",
    "presion_exceso_vel",
    "presion_casos_t",
]

CASES = "dengue_notifications_count"
NEEDED = [*KEYS, "department_code", "zona_canal_t", CASES]


def _monthly_difference(frame: pd.DataFrame, column: str) -> pd.Series:
    """Diferencia contra el mes calendario anterior del mismo municipio."""
    level = pd.Series(
        frame[column].to_numpy(dtype=float),
        index=pd.MultiIndex.from_arrays([frame.municipality_code, frame.year_month]),
    )
    previous = [str(period - 1) for period in pd.PeriodIndex(frame.year_month, freq="M")]
    lagged = level.reindex(
        pd.MultiIndex.from_arrays([frame.municipality_code, previous])
    ).to_numpy()
    return pd.Series(frame[column].to_numpy(dtype=float) - lagged, index=frame.index)


def regional_features(history: pd.DataFrame) -> pd.DataFrame:
    """Construir las tres columnas del bloque sobre la historia ordenada.

    Args:
        history: Tabla canónica, con departamento, zona del canal y casos.

    Returns:
        Las tres columnas indexadas por `municipality_code` y `year_month`, en el
        orden fijo de `REGIONAL_COLUMNS`.

    Raises:
        ValueError: Si falta una columna de insumo.
    """
    missing = [column for column in NEEDED if column not in history]
    if missing:
        raise ValueError("Insumos del bloque regional ausentes: " + ", ".join(missing))

    frame = history.loc[:, NEEDED].sort_values(KEYS).reset_index(drop=True)
    zona = frame.zona_canal_t
    exceso = zona.eq("EXCESO").astype(float).where(zona.notna())
    conocida = zona.notna().astype(float)
    casos = frame[CASES].astype(float)

    # Agregados del departamento-mes, de los que luego se resta el propio
    # municipio: lo de los demás es el total menos lo de uno.
    frame["exceso"], frame["conocida"], frame["casos"] = exceso, conocida, casos
    grupo = frame.groupby(["department_code", "year_month"], sort=False)
    otros_exceso = grupo.exceso.transform("sum") - exceso.fillna(0.0)
    otros_conocidos = grupo.conocida.transform("sum") - conocida
    otros_casos = grupo.casos.transform("sum") - casos.fillna(0.0)

    frame["presion_exceso_t"] = np.where(
        otros_conocidos > 0, otros_exceso / otros_conocidos.replace(0, np.nan), np.nan
    )
    # Sin zona propia conocida el agregado de los demás sigue siendo válido, pero
    # la fila no es evaluable de todos modos; se deja ausente por coherencia.
    frame.loc[zona.isna(), "presion_exceso_t"] = np.nan
    frame["presion_casos_t"] = np.log1p(otros_casos.clip(lower=0)).where(casos.notna())
    frame["presion_exceso_vel"] = _monthly_difference(frame, "presion_exceso_t")
    return frame.set_index(KEYS).loc[:, REGIONAL_COLUMNS]
