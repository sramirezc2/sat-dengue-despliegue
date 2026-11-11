# Tanda 39, línea AU — Qué aprende la logística con clima

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **preinscrita, sin correr.** Se corre sobre la base común del
> retroanálisis: `canonical.mode=approved`, calendario y departamentos de
> `parameters_retroanalisis.yml` sin tocar, `conjunto.csv` reportado.

## Hipótesis

Ninguna que decida algo. El informe necesita explicar qué hace el modelo: qué
variables pesan más y con qué signo, y si las del clima tienen el signo que la
biología del vector espera (más lluvia y más temperatura, más riesgo).

## Qué se corre

La logística sin clima y con clima, reentrenadas en el último origen evaluable de
cada horizonte (2024-11 en T+1 y 2024-10 en T+2) con toda la historia desde
2012-01, igual que en el retroanálisis. Se leen los coeficientes estandarizados
(log-odds por una desviación estándar de cada columna).

## Qué no decide

Es descriptiva. Los coeficientes de una logística con variables correlacionadas no
se leen como efectos causales.
