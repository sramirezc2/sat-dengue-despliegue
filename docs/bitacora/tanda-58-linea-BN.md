# Tanda 58, línea BN — Las combinaciones, confirmadas en la reserva 2023-2024

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **preinscrita, sin correr.** Se corre sobre la base común del
> retroanálisis: `canonical.mode=approved`, calendario y departamentos de
> `parameters_retroanalisis.yml` sin tocar, `conjunto.csv` reportado.

## Origen

Las tandas 14 a 57 eligieron y midieron sobre los mismos siete años. La búsqueda de
Stevan (tandas 94 a 132) fijó un protocolo con reserva: buscar en 2018-2022 y
confirmar en 2023-2024. Él lo aplicó a sus reglas (DG, DH y DJ); esta tanda lo aplica
a las **combinaciones sin regla** de las tandas 14 a 57, que no estaban confirmadas.
No toca DJ ni ninguna regla de reparto.

## Regla de selección, escrita antes de mirar la reserva

1. **Búsqueda.** Para cada combinación logística o XGBoost de las tandas 14 a 57 con
   predicciones guardadas, el veredicto de la sección 0 al 10 % (fracción de 76
   municipios por mes, `veredicto.py` con semilla por celda) **solo con los años
   objetivo 2018-2022**. La f del canal se elige igual que en la tanda 33, pero sobre
   esos años.
2. **Selección.** Pasan a la reserva las **tres** combinaciones con mayor ganancia en
   T+2 en la búsqueda, más la logística con clima como referencia si no está entre
   ellas. Empates por la ganancia en T+1.
3. **Confirmación.** El mismo veredicto **solo con 2023-2024**, sin cambiar nada.

## Qué decide

Una combinación **confirma** en T+2 si en la reserva pasa la barra de la sección 0.3
(al menos 5 puntos con la cota inferior del IC por bloques de mes sobre cero). En T+1
se reporta si cumple A. Con dos años de reserva (unos 150 inicios en T+2) la potencia
es baja; un «no confirma» con el punto estimado sobre 5 se lee como falta de
potencia, no como refutación, y se declara así.

## Qué no decide

No compara familias ni elige campeón. No usa 2025.
