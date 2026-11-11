# Tanda 32, línea AN — El clima con otro remuestreo

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **preinscrita, sin correr.** Se corre sobre la base común del
> retroanálisis: `canonical.mode=approved`, calendario y departamentos de
> `parameters_retroanalisis.yml` sin tocar, `conjunto.csv` reportado.

## Origen

Se escribe después de ver las tandas 15, 22 y 25 y se declara así: el clima sumó
entre 12 y 15 inicios en T+1, a favor en seis de siete años, con un IC por
municipio que siempre cruzó el cero.

## Hipótesis

El IC de la comparación entre recetas remuestrea municipios. El contrato
remuestrea bloques de mes de origen. Si la ganancia del clima es real y pareja
entre municipios pero concentrada en ciertos meses, los dos IC pueden decir cosas
distintas. Esta tanda no busca que el clima pase: mide si la conclusión depende
del remuestreo.

## Qué se corre

Nada nuevo. Las comparaciones logística con clima contra sin clima, y mínima con
clima contra mínima, con los dos IC: por municipio y por bloques de mes de origen
(2 000 réplicas, semilla 42).

## Qué decide

Si con el IC por bloques de mes la ganancia del clima excluye el cero, se reporta
que la conclusión depende del remuestreo y se usa el del contrato como el que
manda. Si los dos cruzan el cero, el clima queda como **sin efecto** con los dos.
