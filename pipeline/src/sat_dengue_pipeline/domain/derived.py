"""Catálogo cerrado de las columnas derivadas de preparación.

Las derivadas no entran a la tabla canónica: son funciones deterministas de
columnas que ya están en ella, y agregarlas allá cambiaría el digest del
artefacto y la certificación N=3. Se construyen en preparación y cada bloque lo
enciende un interruptor de la receta.

Este módulo existe por dos razones. La primera es que haya **un solo** orden
canónico: cuando una receta enciende varios bloques, sus columnas van al final
de la matriz en el orden de `DERIVED_COLUMNS`, de modo que dos recetas que
declaren los mismos bloques producen la misma matriz interna y el adaptador
puede rechazar cualquier otro orden sin ambigüedad.

La segunda es que haya **una sola** forma de resolver qué declara una receta.
Antes cada adaptador repetía la cadena de interruptores, y esa duplicación ya
produjo una guarda vacua: en `logistic.py` se comparaba `self.derived` contra
una expresión construida igual tres líneas antes, así que la comprobación no
podía fallar nunca. Con `declared_derived` hay una definición y las guardas que
quedan son las que sí pueden saltar.
"""

from .febriles import FEBRILES_COLUMNS
from .margin import (
    CLIMA_LAG_COLUMNS,
    DEPTO_COLUMNS,
    MARGIN_COLUMNS,
    MES_COLUMNS,
    ROCIO_META_COLUMNS,
)
from .regional import REGIONAL_COLUMNS
from .vecinos import VECINOS_COLUMNS

#: Qué interruptor de la receta enciende cada bloque, en el orden en que sus
#: columnas van al final de la matriz. Añadir un bloque es añadirlo aquí.
DERIVED_BLOCKS = (
    ("variables_g", tuple(MARGIN_COLUMNS)),
    ("variables_mes", tuple(MES_COLUMNS)),
    ("variable_depto", tuple(DEPTO_COLUMNS)),
    ("clima_rezagos", tuple(CLIMA_LAG_COLUMNS)),
    ("rocio_meta", tuple(ROCIO_META_COLUMNS)),
    ("variables_h", tuple(REGIONAL_COLUMNS)),
    ("variables_febriles", tuple(FEBRILES_COLUMNS)),
    ("variables_vecinos", tuple(VECINOS_COLUMNS)),
)

#: Orden canónico de todas las derivadas conocidas.
DERIVED_COLUMNS = tuple(columna for _, bloque in DERIVED_BLOCKS for columna in bloque)


def declared_derived(preparation: dict) -> tuple[str, ...]:
    """Resolver qué derivadas declara una receta, en el orden canónico.

    Args:
        preparation: Bloque `preparation` de la receta.

    Returns:
        Las columnas de los bloques encendidos, en el orden de `DERIVED_COLUMNS`.
    """
    return tuple(
        columna
        for interruptor, bloque in DERIVED_BLOCKS
        if preparation.get(interruptor)
        for columna in bloque
    )
