"""Bloque de margen al umbral del canal: las seis variables de la línea G.

Qué es y por qué existe
-----------------------

El canal endémico decide con una línea: el municipio está en exceso o no lo
está. El modelo recibía esa decisión ya tomada —`zona_canal_t`— pero no sabía
**a qué distancia** del umbral estaba el municipio. Un municipio al 99 % del
P75 y otro al 10 % entran como el mismo "no exceso".

Darle esa distancia es la línea G de la bitácora, confirmada en la tanda 5
**sobre XGBoost**, donde al mismo presupuesto de alertas lleva al modelo de 388
a 467 inicios anticipados de 647 en T+1.

**No se reproduce sobre una logística.** La tanda 11 la midió sobre la base
común contra la receta `logistica_sin_clima`, con el mismo panel, los mismos
folds y las mismas filas: el bloque mueve las detecciones entre 0 y 5 inicios
sobre 641, dentro de lo que la regla 9 prohíbe reportar sin cinco semillas. La
razón está medida y no es un defecto del bloque: esa receta aplica `log1p` a
conteos y umbrales, así que el modelo ya forma el margen como una resta de
logaritmos, y la correlación de rangos entre `margen_objetivo` y
`log1p(casos) − log1p(p75_objetivo)` es de 0,999. Un árbol tiene que aproximar
ese cociente con cortes sucesivos; un modelo log-lineal lo obtiene con dos
coeficientes.

Es decir: el bloque sigue siendo útil donde se confirmó, y queda aquí para
poder medirlo en cualquier receta, no como una mejora que valga para todas.

Dónde vive y por qué aquí
-------------------------

**Estas columnas NO entran a la tabla canónica.** Son derivadas deterministas
de columnas que ya existen en ella, y agregarlas allá cambiaría el digest del
artefacto, invalidando la certificación N=3 de la ventana completa y la
identidad histórica. Se construyen en preparación, que es donde el contrato ya
tenía previsto el interruptor `preparation.variables_g`.

De dónde sale cada una
----------------------

Con `casos` los casos del mes de origen, `p25/p75_canal_t` la banda del canal
en el mes en curso y `p75_h5_t{h}` el umbral del mes objetivo:

    margen_objetivo     = (casos - p75_objetivo) / (p75_objetivo + 1)
    margen_curso        = (casos - p75_curso)    / (p75_curso + 1)
    pos_banda           = (casos - p25_curso)    / (p75_curso - p25_curso + 1)
    margen_objetivo_vel = margen_objetivo - su valor del mes anterior
    margen_curso_vel    = margen_curso    - su valor del mes anterior
    margen_curso_acel   = margen_curso_vel - su valor del mes anterior

El `+1` de los denominadores no es cosmético: evita la división por cero en los
municipios cuyo percentil histórico es cero, que son 153 de 912 por año y que
ya nos costaron una degeneración en la tanda 9.

Fuga
----

Ninguna de las seis mira hacia adelante. `p75_h5_t{h}` es el percentil del mes
objetivo, pero se construye con el mismo mes calendario de los **cinco años
anteriores**, y el productor canónico aborta si algún periodo histórico es
posterior al origen; ya es predictor del contrato por esa razón. Las
velocidades y la aceleración son diferencias contra el mes calendario anterior
**del mismo municipio**, buscado por su nombre y no por su posición, de modo
que un recorte del futuro no cambia su valor en el mes `t` y un hueco de
calendario produce una ausencia en vez de una diferencia contra el mes
equivocado. La prueba `test_margin_block.py` fija ambas cosas midiéndolas, no
afirmándolas.

La fuente de casos, que es una decisión declarada
-------------------------------------------------

El bloque original se midió sobre `total_notifications_count` —dengue más
grave— mientras que el canal se construye sobre `dengue_notifications_count`.
Es decir, el margen compara casos totales contra un umbral de solo dengue.

Eso se conserva tal cual, y se declara, por una razón de método: **reproducir
primero, mejorar después.** Si al portar el bloque se cambiara la fuente, una
diferencia contra los 467 medidos no se podría atribuir: ¿el puerto o la
definición nueva? `source` existe para que la variante coherente
(`dengue_notifications_count` en los dos lados) se pueda medir como línea
preinscrita aparte, contra la misma base y con la atribución limpia.
"""

from __future__ import annotations

import pandas as pd

from .canonical import KEYS

MARGIN_COLUMNS = [
    "margen_objetivo",
    "margen_curso",
    "pos_banda",
    "margen_objetivo_vel",
    "margen_curso_vel",
    "margen_curso_acel",
]

# Fuentes admitidas para los casos del margen. La primera es la que se midió.
MARGIN_SOURCES = ("total_notifications_count", "dengue_notifications_count")


def _relative(cases: pd.Series, threshold: pd.Series) -> pd.Series:
    """Margen relativo al umbral; positivo significa por encima de él."""
    return (cases - threshold) / (threshold + 1.0)


def _monthly_difference(frame: pd.DataFrame, column: str) -> pd.Series:
    """Diferencia contra el mes calendario anterior del mismo municipio.

    No se usa `shift(1)`: con un hueco de calendario, la fila anterior puede ser
    de dos meses atrás y la diferencia saldría silenciosamente mal. Aquí el mes
    anterior se busca por su nombre, y si no existe el resultado es ausente.

    Args:
        frame: Historia ordenada con las claves y la columna de nivel.
        column: Nombre de la columna de nivel.

    Returns:
        Serie alineada con `frame`, ausente donde no hay mes anterior.
    """
    level = pd.Series(
        frame[column].to_numpy(dtype=float),
        index=pd.MultiIndex.from_arrays([frame.municipality_code, frame.year_month]),
    )
    previous = [str(period - 1) for period in pd.PeriodIndex(frame.year_month, freq="M")]
    lagged = level.reindex(
        pd.MultiIndex.from_arrays([frame.municipality_code, previous])
    ).to_numpy()
    return pd.Series(frame[column].to_numpy(dtype=float) - lagged, index=frame.index)


def margin_features(
    history: pd.DataFrame,
    horizon: int,
    source: str = MARGIN_SOURCES[0],
) -> pd.DataFrame:
    """Construir las seis columnas del bloque sobre la historia ordenada.

    Se calcula sobre la historia completa del municipio y no sobre las filas
    seleccionadas, porque las velocidades necesitan el mes inmediatamente
    anterior aunque ese mes no sea un origen evaluable.

    Args:
        history: Tabla canónica, con sus claves y la banda del canal.
        horizon: 1 o 2; elige el `p75_h5_t{h}` del mes objetivo.
        source: Columna de casos del margen; ver el encabezado del módulo.

    Returns:
        Las seis columnas indexadas por `municipality_code` y `year_month`,
        en el orden fijo de `MARGIN_COLUMNS`.

    Raises:
        ValueError: Si falta una columna de insumo o la fuente no es admitida.
    """
    if source not in MARGIN_SOURCES:
        raise ValueError("Fuente de casos del margen no declarada")
    target_threshold = f"p75_h5_t{horizon}"
    needed = [*KEYS, source, target_threshold, "p25_canal_t", "p75_canal_t"]
    missing = [column for column in needed if column not in history]
    if missing:
        raise ValueError("Insumos del bloque de margen ausentes: " + ", ".join(missing))

    frame = history.loc[:, needed].sort_values(KEYS).reset_index(drop=True)
    cases = frame[source].astype(float)
    current = frame.p75_canal_t.astype(float)
    band = frame.p25_canal_t.astype(float)

    frame["margen_objetivo"] = _relative(cases, frame[target_threshold].astype(float))
    frame["margen_curso"] = _relative(cases, current)
    frame["pos_banda"] = (cases - band) / (current - band + 1.0)

    frame["margen_objetivo_vel"] = _monthly_difference(frame, "margen_objetivo")
    frame["margen_curso_vel"] = _monthly_difference(frame, "margen_curso")
    frame["margen_curso_acel"] = _monthly_difference(frame, "margen_curso_vel")

    return frame.set_index(KEYS).loc[:, MARGIN_COLUMNS]
