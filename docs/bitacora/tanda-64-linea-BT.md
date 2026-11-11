# Tanda 64, línea BT — Recalibrar con la frecuencia del año anterior

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **preinscrita, sin correr.** Se corre sobre la base común del
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
