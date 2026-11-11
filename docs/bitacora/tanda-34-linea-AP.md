# Tanda 34, línea AP — El veredicto de T+2 año por año

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **preinscrita, sin correr.** Se corre sobre la base común del
> retroanálisis: `canonical.mode=approved`, calendario y departamentos de
> `parameters_retroanalisis.yml` sin tocar, `conjunto.csv` reportado.

## Origen

Se escribe después de ver la tanda 33: al 10 %, las cuatro logísticas pasan la
barra en T+2 sobre los siete años juntos. La regla 3 pide consistencia entre
cortes, no el agregado.

## Hipótesis

Si la ventaja en T+2 es real, aparece en la mayoría de los años y no depende de
uno o dos.

## Qué se corre

El mismo cálculo de la tanda 33 (10 % de los 76 municipios por mes, canal
condicionado con la f más cercana), separado por año objetivo, para las cuatro
logísticas y para T+1 y T+2.

## Qué decide

Se declara **consistente** si el modelo detecta más inicios que el canal en al
menos cinco de los siete años del mismo horizonte, y ningún año con 30 inicios o
más pierde por más de 5 puntos. Si no, la ventaja agregada se reporta como
dependiente de pocos años.
