# Tanda 62, línea BR — Qué tan grandes son los brotes que solo ve el modelo

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **preinscrita, sin correr.** Se corre sobre la base común del
> retroanálisis: `canonical.mode=approved`, calendario y departamentos de
> `parameters_retroanalisis.yml` sin tocar, `conjunto.csv` reportado.

## Hipótesis

El modelo gana donde el canal no puede ver: municipios poco endémicos e inicios con
pocos o cero casos (tandas 35 y 46). Si esos brotes son pequeños, la ganancia vale
menos de lo que dice el conteo de inicios; si algunos son grandes, vale más.

## Qué se corre

Ningún modelo nuevo. Al 10 %, logística con clima, T+1 y T+2: para los inicios que
detectan ambos, solo el canal, solo el modelo y ninguno, la mediana y el percentil 90
de los casos en el mes objetivo y de la razón casos / P75 del mes objetivo.

## Qué no decide

Es una lectura.
