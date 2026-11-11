# Tanda 61, línea BQ — Cómo se reparten las alertas entre municipios y meses

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **preinscrita, sin correr.** Se corre sobre la base común del
> retroanálisis: `canonical.mode=approved`, calendario y departamentos de
> `parameters_retroanalisis.yml` sin tocar, `conjunto.csv` reportado.

## Hipótesis

Ninguna que decida. Una secretaría no recibe un porcentaje: recibe una lista de
municipios cada mes. Si las falsas alertas se concentran en pocos municipios, o un
mismo municipio queda alertado muchos meses seguidos, el costo operativo y el
cansancio de alertas son distintos de lo que dice el promedio.

## Qué se corre

Ningún modelo nuevo. Al 10 % de la sección 0, logística con clima y canal
condicionado, T+1 y T+2, 2018-2024: cuántos municipios distintos reciben alertas,
qué parte de las falsas alertas se lleva el 10 % de municipios con más falsas, y la
racha máxima y mediana de meses consecutivos alertados por municipio.

## Qué no decide

Es una lectura operativa.
