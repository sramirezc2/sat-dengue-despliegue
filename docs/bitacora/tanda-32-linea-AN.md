# Tanda 32, línea AN — El clima con otro remuestreo

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **cerrada** el 10 de noviembre de 2026. Se corre sobre la base común del
> retroanálisis: `canonical.mode=approved`, calendario y departamentos de
> `parameters_retroanalisis.yml` sin tocar, `conjunto.csv` reportado.

## Origen

Se escribe después de ver las tandas 15, 22 y 25 y se declara así: el clima sumó
entre 12 y 15 inicios en T+1, a favor en seis de siete años, con un IC por
municipio que siempre cruzó el cero.

## Hipótesis

El IC de la comparación entre recetas remuestrea municipios. El contrato
remuestrea bloques de mes de origen. Si la ganancia del clima es real y pareja
entre municipios pero concentrada en ciertos meses, los dos IC pueden decir cosas
distintas. Esta tanda no busca que el clima pase: mide si la conclusión depende
del remuestreo.

## Qué se corre

Nada nuevo. Las comparaciones logística con clima contra sin clima, y mínima con
clima contra mínima, con los dos IC: por municipio y por bloques de mes de origen
(2 000 réplicas, semilla 42).

## Qué decide

Si con el IC por bloques de mes la ganancia del clima excluye el cero, se reporta
que la conclusión depende del remuestreo y se usa el del contrato como el que
manda. Si los dos cruzan el cero, el clima queda como **sin efecto** con los dos.

## Resultado: con el remuestreo del contrato, el clima en T+1 queda por encima de cero

| Comparación | Horizonte | Presupuesto | Inicios | IC por municipio | IC por bloques de mes |
| --- | --- | --- | --- | --- | --- |
| Logística con clima contra sin clima | T+1 | condicionado | +12 | -4 a 28 | 0 a 26 |
| Logística con clima contra sin clima | T+1 | 5 % | +3 | -12 a 16 | -4 a 10 |
| Logística con clima contra sin clima | T+1 | 10 % | +5 | -8 a 18 | -4 a 15 |
| Logística con clima contra sin clima | T+1 | 20 % | +13 | -4 a 30 | 2 a 24 |
| Logística con clima contra sin clima | T+2 | condicionado | +5 | -9 a 17 | -7 a 16 |
| Logística con clima contra sin clima | T+2 | 5 % | -2 | -12 a 9 | -11 a 7 |
| Logística con clima contra sin clima | T+2 | 10 % | +4 | -9 a 17 | -7 a 14 |
| Logística con clima contra sin clima | T+2 | 20 % | +7 | -6 a 21 | -4 a 18 |
| Mínima con clima contra mínima | T+1 | condicionado | +15 | -5 a 34 | 1 a 30 |
| Mínima con clima contra mínima | T+1 | 5 % | -7 | -23 a 7 | -15 a 1 |
| Mínima con clima contra mínima | T+1 | 10 % | +11 | -8 a 31 | 0 a 22 |
| Mínima con clima contra mínima | T+1 | 20 % | +18 | -4 a 40 | 5 a 32 |
| Mínima con clima contra mínima | T+2 | condicionado | +2 | -14 a 17 | -9 a 13 |
| Mínima con clima contra mínima | T+2 | 5 % | +1 | -9 a 12 | -8 a 10 |
| Mínima con clima contra mínima | T+2 | 10 % | -3 | -16 a 9 | -13 a 6 |
| Mínima con clima contra mínima | T+2 | 20 % | +7 | -7 a 21 | -6 a 20 |

El IC por bloques de mes es más estrecho que el IC por municipio en todas las
celdas: la ganancia del clima es pareja entre meses y desigual entre municipios
(se concentra en Meta, tanda 25). Con el remuestreo del contrato, **la ganancia
del clima en T+1 excluye el cero** sobre la mínima (+15, IC 1 a 30) y al 20 %
sobre las dos (+13, IC 2 a 24; +18, IC 5 a 32); sobre la logística completa al
presupuesto del canal condicionado queda en el borde (+12, IC 0 a 26). En T+2
cruza el cero en todas las celdas.

Lectura, según lo preinscrito: **la conclusión sobre el clima en T+1 depende del
remuestreo**, y con el del contrato, que es el que manda, el clima aporta en T+1
con un efecto real pero chico, de unos 2 puntos, lejos de la barra de 5. En T+2
no aporta.
