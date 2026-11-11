"""Bloque de vecinos: lo que pasa en los municipios más cercanos.

Qué es y por qué existe
-----------------------

La tanda 46 midió que la mitad de los inicios que no anticipa nadie arranca con
cero casos en el municipio. Ahí la única señal posible es la de alrededor. La
tanda 51 midió la presión del departamento entero y no aportó; el departamento es
una escala gruesa. Este bloque mira solo a los k municipios más cercanos.

    vecinos_casos_t     log1p de la suma de casos de dengue de los k vecinos
    vecinos_exceso_t    fracción de los k vecinos en EXCESO, entre los de zona
                        conocida
    vecinos_casos_vel   vecinos_casos_t menos su valor del mes calendario anterior

De dónde salen los vecinos
--------------------------

De los centroides DIVIPOLA (`conf/geografia/divipola_coordenadas.csv`), por
distancia de gran círculo, **solo entre los municipios presentes en el panel** y
**excluyendo siempre al propio**. Con el panel de Tolima y Meta, un municipio de
borde no ve a sus vecinos de otros departamentos; con entrenamiento nacional sí.

Fuga
----

Las tres son del mes de origen. La velocidad se busca por mes calendario.
Como todas las derivadas, no entra a la tabla canónica ni cambia su digest.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .canonical import KEYS
from .regional import _monthly_difference

VECINOS_COLUMNS = ["vecinos_casos_t", "vecinos_exceso_t", "vecinos_casos_vel"]
K_VECINOS = 5
COORDENADAS = Path(__file__).resolve().parents[3] / "conf/geografia/divipola_coordenadas.csv"

CASES = "dengue_notifications_count"
NEEDED = [*KEYS, "zona_canal_t", CASES]


def leer_coordenadas(ruta: Path = COORDENADAS) -> pd.DataFrame:
    """Leer los centroides DIVIPOLA, que vienen con coma decimal.

    Args:
        ruta: Archivo de centroides.

    Returns:
        Tabla con `cod_mpio`, `latitud` y `longitud` numéricas.
    """
    co = pd.read_csv(ruta, dtype={"cod_mpio": str, "longitud": str, "latitud": str})
    for columna in ("longitud", "latitud"):
        co[columna] = co[columna].str.replace(",", ".", regex=False).astype(float)
    return co


def vecinos_mas_cercanos(
    municipios: list[str], coordenadas: pd.DataFrame, k: int = K_VECINOS
) -> dict[str, list[str]]:
    """Los k municipios más cercanos de cada uno, sin incluirse a sí mismo.

    Args:
        municipios: Códigos DANE presentes en el panel.
        coordenadas: Tabla con `cod_mpio`, `latitud` y `longitud`.
        k: Número de vecinos.

    Returns:
        Para cada municipio, la lista de sus k vecinos, del más cercano al más
        lejano. Si el panel tiene menos de k + 1 municipios, todos los demás.

    Raises:
        ValueError: Si algún municipio del panel no tiene coordenadas.
    """
    c = coordenadas.set_index("cod_mpio")
    faltan = sorted(set(municipios) - set(c.index))
    if faltan:
        raise ValueError("Municipios sin coordenadas DIVIPOLA: " + ", ".join(faltan[:5]))
    c = c.loc[sorted(municipios)]
    lat = np.radians(c.latitud.to_numpy(dtype=float))
    lon = np.radians(c.longitud.to_numpy(dtype=float))
    seno_lat = np.sin((lat[:, None] - lat[None, :]) / 2) ** 2
    seno_lon = np.sin((lon[:, None] - lon[None, :]) / 2) ** 2
    distancia = 2 * np.arcsin(np.sqrt(seno_lat + np.outer(np.cos(lat), np.cos(lat)) * seno_lon))
    np.fill_diagonal(distancia, np.inf)
    codigos = c.index.to_numpy()
    orden = np.argsort(distancia, axis=1, kind="stable")[:, : min(k, len(codigos) - 1)]
    return {codigos[i]: list(codigos[orden[i]]) for i in range(len(codigos))}


def vecinos_features(
    history: pd.DataFrame, coordenadas: pd.DataFrame | None = None, k: int = K_VECINOS
) -> pd.DataFrame:
    """Construir las tres columnas del bloque sobre la historia ordenada.

    Args:
        history: Tabla canónica con zona del canal y casos.
        coordenadas: Centroides DIVIPOLA; por defecto los versionados.
        k: Número de vecinos.

    Returns:
        Las tres columnas indexadas por `municipality_code` y `year_month`, en el
        orden fijo de `VECINOS_COLUMNS`. Todo ausente si el panel tiene un solo
        municipio o alguno sin coordenadas: el bloque no aplica y el filtro común
        lo excluye.

    Raises:
        ValueError: Si falta una columna de insumo.
    """
    missing = [column for column in NEEDED if column not in history]
    if missing:
        raise ValueError("Insumos del bloque de vecinos ausentes: " + ", ".join(missing))
    frame = history.loc[:, NEEDED].sort_values(KEYS).reset_index(drop=True)
    indice = pd.MultiIndex.from_frame(frame.loc[:, KEYS])
    municipios = sorted(frame.municipality_code.unique())
    coordenadas = leer_coordenadas() if coordenadas is None else coordenadas
    sin_coordenadas = set(municipios) - set(coordenadas.cod_mpio)
    if len(municipios) < 2 or sin_coordenadas:
        # Sin vecinos para todos, el bloque no aplica a este panel: queda ausente y
        # el filtro común lo excluye; una receta que lo declare falla con su nombre.
        return pd.DataFrame(np.nan, index=indice, columns=VECINOS_COLUMNS)
    vecinos = vecinos_mas_cercanos(municipios, coordenadas, k)
    zona = frame.zona_canal_t
    casos = pd.Series(frame[CASES].to_numpy(dtype=float), index=indice)
    exceso = pd.Series(zona.eq("EXCESO").astype(float).where(zona.notna()).to_numpy(), index=indice)
    meses = frame.year_month.unique()
    propios = [m for m, vs in vecinos.items() for _ in vs]
    ajenos = [v for vs in vecinos.values() for v in vs]
    buscado = pd.MultiIndex.from_arrays(
        [np.repeat(ajenos, len(meses)), np.tile(meses, len(ajenos))], names=KEYS
    )
    clave = pd.MultiIndex.from_arrays(
        [np.repeat(propios, len(meses)), np.tile(meses, len(propios))], names=KEYS
    )
    tabla = pd.DataFrame(
        {
            "casos": casos.reindex(buscado).to_numpy(),
            "exceso": exceso.reindex(buscado).to_numpy(),
        },
        index=clave,
    )
    grupo = tabla.groupby(level=[0, 1], sort=False)
    agregado = pd.DataFrame(
        {
            "casos": grupo.casos.sum(min_count=1),
            "exceso": grupo.exceso.mean(),
        }
    ).reindex(indice)
    frame["vecinos_casos_t"] = np.log1p(agregado.casos.to_numpy())
    frame["vecinos_exceso_t"] = agregado.exceso.to_numpy()
    frame["vecinos_casos_vel"] = _monthly_difference(frame, "vecinos_casos_t")
    return frame.set_index(KEYS).loc[:, VECINOS_COLUMNS]
