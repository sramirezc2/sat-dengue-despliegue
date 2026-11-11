# Tanda 47, línea BC — En qué meses del año gana el modelo

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **preinscrita, sin correr.** Se corre sobre la base común del
> retroanálisis: `canonical.mode=approved`, calendario y departamentos de
> `parameters_retroanalisis.yml` sin tocar, `conjunto.csv` reportado.

## Hipótesis

El canal endémico se construye mes a mes con los cinco años anteriores, así que su
umbral ya trae la estación. Si el modelo gana sobre todo en ciertos meses (por
ejemplo, al inicio de la temporada de lluvias), eso orienta cuándo usarlo.

## Qué se corre

Ningún modelo nuevo. Al 10 % de la sección 0, logística con clima, T+1 y T+2: los
inicios detectados por el canal y por el modelo según el mes objetivo, agrupado por
trimestre para tener celdas de 30 inicios o más.

## Qué no decide

Es una lectura.
