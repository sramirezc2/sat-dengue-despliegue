# Tanda 42, línea AX — Se pueden leer las probabilidades como riesgo?

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **preinscrita, sin correr.** Se corre sobre la base común del
> retroanálisis: `canonical.mode=approved`, calendario y departamentos de
> `parameters_retroanalisis.yml` sin tocar, `conjunto.csv` reportado.

## Hipótesis

En la tanda 10, con otro instrumento, la probabilidad de T+1 se podía leer como
riesgo real y la de T+2 subestimaba. Si se repite sobre la base común, el informe
puede presentar el puntaje de T+1 como probabilidad y el de T+2 solo como orden.

## Qué se corre

Ningún modelo nuevo. Para la logística sin clima y con clima, por horizonte, sobre
las filas evaluadas: la frecuencia observada de inicios por decil de probabilidad
predicha, la media predicha en cada decil, la puntuación de Brier y la de una
predicción constante igual a la frecuencia de entrenamiento como referencia.

## Qué no decide

Es descriptiva; la decisión de la sección 0 usa el orden, no la probabilidad.
