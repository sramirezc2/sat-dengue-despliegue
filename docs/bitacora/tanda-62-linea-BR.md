# Tanda 62, línea BR — Qué tan grandes son los brotes que solo ve el modelo

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **cerrada** el 11 de noviembre de 2026. Se corre sobre la base común del
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

## Resultado: los brotes que solo ve el modelo son chicos

- T+1 ambos: n=236 casos objetivo mediana 7 p90 20; casos/P75 mediana 1.67 p90 3.50
- T+1 solo canal: n=43 casos objetivo mediana 5 p90 41; casos/P75 mediana 1.38 p90 2.50
- T+1 solo modelo: n=63 casos objetivo mediana 5 p90 14; casos/P75 mediana 1.33 p90 3.80
- T+1 ninguno: n=299 casos objetivo mediana 5 p90 24; casos/P75 mediana 1.14 p90 2.02
- T+2 ambos: n=110 casos objetivo mediana 6 p90 17; casos/P75 mediana 1.40 p90 3.00
- T+2 solo canal: n=42 casos objetivo mediana 5 p90 33; casos/P75 mediana 1.50 p90 2.00
- T+2 solo modelo: n=75 casos objetivo mediana 4 p90 16; casos/P75 mediana 1.17 p90 2.50
- T+2 ninguno: n=232 casos objetivo mediana 6 p90 30; casos/P75 mediana 1.20 p90 2.42

- Los inicios que **solo detecta el modelo** son los de menos casos en el mes
  objetivo (mediana 5 en T+1 y 4 en T+2) y su percentil 90 es bajo (14 y 16).
- Los que **solo detecta el canal** tienen colas más grandes (percentil 90 de 41 y 33
  casos): el canal se queda con algunos brotes grandes que el modelo deja pasar.
- Medidos contra su propio umbral (casos / P75) los grupos se parecen (medianas entre
  1,2 y 1,7): son excesos reales, pero en municipios chicos.
- Para el informe: **la ventaja del modelo está en brotes pequeños de municipios poco
  endémicos**; en número de inicios gana, en casos involucrados la ganancia es menor
  que la que sugiere el conteo.

Logística con clima y canal condicionado al 10 % de la sección 0, 2018-2024 salvo que se diga otra cosa; predicciones de la tanda 15, sin modelos nuevos.
