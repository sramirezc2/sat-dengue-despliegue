# Tanda 64, línea BT — Recalibrar con la frecuencia del año anterior

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **cerrada** el 11 de noviembre de 2026. Se corre sobre la base común del
> retroanálisis: `canonical.mode=approved`, calendario y departamentos de
> `parameters_retroanalisis.yml` sin tocar, `conjunto.csv` reportado.

## Origen

La tanda 63 mostró que en la reserva el modelo subestima el riesgo (0,23 predicho
frente a 0,27 observado en T+1) porque la frecuencia de inicios cambia entre años. La
tanda 10, con otro instrumento, había descartado recalibrar con años anteriores; aquí
se mide sobre la base común y con este diagnóstico.

## Hipótesis

Mover el intercepto del modelo, en escala logit, para que la probabilidad media de
cada año iguale la frecuencia de inicios **del año anterior** (conocida en enero)
corrige el nivel de la probabilidad sin cambiar el orden dentro del año.

## Qué se corre

Ningún modelo nuevo. Con las predicciones de la logística con clima: para cada año
objetivo de 2019 a 2024, un desplazamiento del logit tal que la media predicha sobre
las filas evaluadas del año anterior iguale la frecuencia observada en ese año
anterior, aplicado tal cual al año siguiente. Se compara la probabilidad media
predicha con la observada por año, el Brier y el decil alto, antes y después.

## Qué decide

La recalibración **sirve** si reduce el Brier en al menos cuatro de los seis años y
acerca la media predicha a la observada en la reserva 2023-2024. Como solo mueve el
nivel, no cambia el ranking dentro de cada mes ni el veredicto de la sección 0.

## Resultado: no sirve

| Horizonte | Año | Observada | Predicha antes | Predicha después | Brier antes | Brier después |
| --- | --- | --- | --- | --- | --- | --- |
| T+1 | 2019 | 0.314 | 0.204 | 0.212 | 0.1973 | 0.1955 |
| T+1 | 2020 | 0.104 | 0.175 | 0.273 | 0.0855 | 0.1160 |
| T+1 | 2021 | 0.061 | 0.102 | 0.056 | 0.0548 | 0.0520 |
| T+1 | 2022 | 0.128 | 0.144 | 0.091 | 0.0910 | 0.0934 |
| T+1 | 2023 | 0.305 | 0.214 | 0.193 | 0.1898 | 0.1948 |
| T+1 | 2024 | 0.239 | 0.236 | 0.330 | 0.1363 | 0.1441 |
| T+2 | 2019 | 0.201 | 0.127 | 0.134 | 0.1563 | 0.1554 |
| T+2 | 2020 | 0.087 | 0.124 | 0.196 | 0.0746 | 0.0884 |
| T+2 | 2021 | 0.058 | 0.088 | 0.061 | 0.0525 | 0.0508 |
| T+2 | 2022 | 0.095 | 0.105 | 0.069 | 0.0813 | 0.0817 |
| T+2 | 2023 | 0.191 | 0.125 | 0.113 | 0.1484 | 0.1504 |
| T+2 | 2024 | 0.160 | 0.132 | 0.200 | 0.1171 | 0.1168 |

- El Brier mejora en **2 de 6 años en T+1 y 3 de 6 en T+2**; el criterio pedía cuatro.
  En la reserva 2023-2024 no acerca la media a lo observado: en 2023 la empeora
  (0,193 frente a 0,305 observado en T+1) y en 2024 se pasa (0,330 frente a 0,239).
- La razón es que **la frecuencia de un año no anticipa la del siguiente**: 2020 llega
  después de un 2019 alto y es bajo, 2023 después de un 2022 bajo y es alto. Ajustar
  con el año anterior mueve el nivel en la dirección equivocada justo en los años que
  cambian.
- Se confirma lo de la tanda 63 con otra pregunta: el puntaje sirve como orden de
  riesgo, y su nivel no se puede fijar de antemano con la información de enero. Este
  ajuste no cambia el orden ni el veredicto de la sección 0.

Predicciones de la logística con clima (tanda 15); análisis sin modelos nuevos.
