# Tanda 50, línea BF — Combinar lo que sumó

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **preinscrita, sin correr.** Se corre sobre la base común del
> retroanálisis: `canonical.mode=approved`, calendario y departamentos de
> `parameters_retroanalisis.yml` sin tocar, `conjunto.csv` reportado.

## Regla de selección, escrita antes de ver las tandas 18, 27, 28, 40, 48 y 49

Escrita a las 23:50 del 10 de noviembre, con esas seis tandas preinscritas y
todavía sin resultados (salvo la nacional sin clima de la tanda 18, que ya se vio:
−7 y 0).

Partiendo de la **logística con clima** (la referencia de la tanda 33), se agrega
cada opción de esas tandas que cumpla **las dos** condiciones, medidas contra su
propia referencia al presupuesto del canal condicionado:

1. diferencia positiva en T+1 y en T+2;
2. al menos cuatro de siete años a favor en T+1.

Si ninguna opción las cumple, la tanda no se corre y se cierra así. Si varias las
cumplen, se combinan todas a la vez, sin probar subconjuntos.

## Qué se corre

La logística con clima con las opciones que pasen la regla. Se evalúa con
`comparar.py` contra la logística con clima, y con `veredicto.py` al 10 %.

## Qué decide y qué no

Como la regla elige con los mismos años con que después se mide, **el resultado
es optimista** y no se puede declarar mejora. Sirve para saber si las ganancias
pequeñas se suman o se pisan. Si la combinación queda por debajo de la mejor
opción sola, se pisan.
