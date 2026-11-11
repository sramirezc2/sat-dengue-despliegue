"""Bloque de otros síndromes febriles: dengue frente al total de notificaciones.

Qué es y por qué existe
-----------------------

La tanda 39 mostró que la logística usa la diferencia entre las notificaciones
totales y las de dengue: los conteos totales entran con signo positivo y algunos
de dengue con signo negativo. El modelo tiene que armar esa diferencia a partir de
varias columnas. Este bloque se la da hecha, porque un aumento de síndromes
febriles que todavía no se confirman como dengue podría adelantar la señal de un
brote.

    prop_dengue_t       casos de dengue / notificaciones totales del mes de
                        origen (0 si no hubo notificaciones)
    otros_febriles_t    log1p de las notificaciones que no son dengue
    otros_febriles_vel  otros_febriles_t menos su valor del mes calendario anterior

Fuga
----

Las tres son del mes de origen, con la misma disponibilidad que los casos propios.
La velocidad se busca por mes calendario, no por posición.

Como todas las derivadas, no entra a la tabla canónica ni cambia su digest.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .canonical import KEYS
from .regional import _monthly_difference

FEBRILES_COLUMNS = ["prop_dengue_t", "otros_febriles_t", "otros_febriles_vel"]

DENGUE = "dengue_notifications_count"
TOTAL = "total_notifications_count"
NEEDED = [*KEYS, DENGUE, TOTAL]


def febriles_features(history: pd.DataFrame) -> pd.DataFrame:
    """Construir las tres columnas del bloque sobre la historia ordenada.

    Args:
        history: Tabla canónica con los conteos de dengue y totales.

    Returns:
        Las tres columnas indexadas por `municipality_code` y `year_month`, en el
        orden fijo de `FEBRILES_COLUMNS`.

    Raises:
        ValueError: Si falta una columna de insumo.
    """
    missing = [column for column in NEEDED if column not in history]
    if missing:
        raise ValueError("Insumos del bloque de febriles ausentes: " + ", ".join(missing))
    frame = history.loc[:, NEEDED].sort_values(KEYS).reset_index(drop=True)
    dengue = frame[DENGUE].astype(float)
    total = frame[TOTAL].astype(float)
    proporcion = (dengue / total.where(total > 0)).fillna(0.0)
    frame["prop_dengue_t"] = proporcion.where(dengue.notna() & total.notna())
    frame["otros_febriles_t"] = np.log1p((total - dengue).clip(lower=0))
    frame["otros_febriles_vel"] = _monthly_difference(frame, "otros_febriles_t")
    return frame.set_index(KEYS).loc[:, FEBRILES_COLUMNS]
