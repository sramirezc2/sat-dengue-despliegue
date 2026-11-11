# Tanda 55, línea BK — Ensamble de dos modelos buenos y distintos

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **preinscrita, sin correr.** Se corre sobre la base común del
> retroanálisis: `canonical.mode=approved`, calendario y departamentos de
> `parameters_retroanalisis.yml` sin tocar, `conjunto.csv` reportado.

## Origen

Se escribe después de las tandas 14, 23 y 54 y se declara así. Los ensambles
anteriores no sumaron: el de la tanda 14 mezclaba la logística con un XGBoost peor
que ella, y el de la tanda 23 mezclaba dos logísticas casi iguales. La tanda 54
mostró un caso distinto: el XGBoost de profundidad 2 **sin clima** empata con la
logística sin clima y casi no depende de la semilla. Es un modelo igual de bueno y
con otra forma de ordenar.

## Hipótesis

Promediar los rangos de la logística con clima y del XGBoost de profundidad 2 sin
clima podría sumar las dos fuentes de ventaja (el clima de uno y los cortes del
otro) sin la dispersión del XGBoost con clima.

## Qué se corre

Sin modelos nuevos. Con `tools/noche/ensamble.py`, sobre las predicciones de las
tandas 15 y 54: promedio de rangos percentiles dentro de cada mes de origen entre la
logística con clima y el XGBoost de profundidad 2 sin clima, **una vez por cada una
de las cinco semillas**; se reporta la media y el rango (regla 9). Referencia: la
logística con clima. Se reporta además el veredicto al 10 % de la sección 0.

La comparación decisiva es contra el mejor de los dos componentes, la logística con
clima.

## Qué métrica decide

Inicios detectados al presupuesto de alertas de cada línea base (canal P75,
condicionado y ajustado), sobre la base común y las mismas filas, igual que las
tandas 11 y 12. El brazo de referencia es `logistica_sin_clima.yml` corrido **en
la misma corrida**. Se publican también el resumen por año y la curva.

## Qué contaría como mejora, declarado antes de mirar

Al presupuesto del canal condicionado, por horizonte:

- **Mejora** si el brazo suma al menos 5 puntos de inicios sobre la referencia
  (32 de 641 en T+1, 23 de 459 en T+2) y la cota inferior del intervalo
  emparejado queda por encima de cero.
- **Sin efecto** si la diferencia está dentro de ±5 puntos o el intervalo cruza
  el cero. Una diferencia de uno o dos inicios no se reporta como hallazgo
  (regla 9).
- **Empeora** si resta al menos 5 puntos con la cota superior por debajo de cero.

Se exige además consistencia entre años (regla 3) y se declara el número de
inicios por año; ningún año con menos de 30 inicios decide nada (regla 4).

## Qué no decide

No decide sobre la meta del contrato ni registra nada en la fábrica. Es
exploración sobre la base común; lo que sobreviva se propone como experimento
registrado.
