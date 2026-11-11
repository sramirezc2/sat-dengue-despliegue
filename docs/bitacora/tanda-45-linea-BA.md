# Tanda 45, línea BA — La curva de presupuesto completa

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **preinscrita, sin correr.** Se corre sobre la base común del
> retroanálisis: `canonical.mode=approved`, calendario y departamentos de
> `parameters_retroanalisis.yml` sin tocar, `conjunto.csv` reportado.

## Hipótesis

Ninguna. La sección 0.1 pide publicar siempre la curva además del punto de
operación. Esta tanda la da completa, con el presupuesto definido como en la
tanda 33, para saber desde qué volumen de alertas el modelo empieza a aportar en
cada horizonte.

## Qué se corre

`veredicto.py` con presupuestos de 2,5, 5, 7,5, 10, 12,5, 15, 20, 25 y 30 % de los
76 municipios por mes, para la logística sin clima y con clima.

## Qué no decide

El veredicto sigue siendo el del 10 % (tanda 33).
