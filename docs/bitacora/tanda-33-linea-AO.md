# Tanda 33, línea AO — Veredicto de la sección 0 para las mejores recetas

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **preinscrita, sin correr.** Se corre sobre la base común del
> retroanálisis: `canonical.mode=approved`, calendario y departamentos de
> `parameters_retroanalisis.yml` sin tocar, `conjunto.csv` reportado.

## Hipótesis

Ninguna. Es la aplicación del criterio de la sección 0 tal como está escrito, a
las recetas que mejor quedaron en la noche: la logística sin clima, la logística
con clima, la mínima y la mínima con clima.

## Qué se corre

Para cada receta y horizonte, contra el canal condicionado al presupuesto de
referencia del **10 %** y, como curva, al 5 y al 20 %: el canal usa la fracción
del P75 cuyo número de alertas queda más cerca del presupuesto, y el modelo emite
las mismas alertas por mes. Se reportan A (IC por bloques de mes que excluye el
cero), la barra de 5 puntos con la cota inferior sobre cero, C (carga de falsas
alertas por 100 municipio-mes con su cota superior) y, como apoyo, el IC por
municipio. B queda NO_EVALUABLE en la cohorte primaria, como dice la sección 0.

## Qué decide

El veredicto se emite **al 10 %**. Lo demás es curva.
