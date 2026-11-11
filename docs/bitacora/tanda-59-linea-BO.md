# Tanda 59, línea BO — Vecinos en un árbol simple

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **preinscrita, sin correr.** Se corre sobre la base común del
> retroanálisis: `canonical.mode=approved`, calendario y departamentos de
> `parameters_retroanalisis.yml` sin tocar, `conjunto.csv` reportado.

## Origen

Se escribe después de la tanda 57: con la logística, el bloque de vecinos anticipa
8 inicios más de los que arrancan con cero casos, pero pierde más en el resto. La
logística aplica los vecinos igual en todas las filas; para usarlos solo donde hay
cero casos haría falta una interacción, que es código nuevo. Un árbol de profundidad
2 puede hacer ese corte por sí mismo (primero «casos = 0», después los vecinos) y no
requiere cambiar nada.

## Hipótesis

El XGBoost de profundidad 2 sin clima, más el bloque de vecinos, conserva la ganancia
en los inicios desde cero casos sin perder en el resto.

## Qué se corre

`xgb_d2_sinclima` con `variables_vecinos: true`, cinco semillas (53, 7, 13, 29, 42;
regla 9). Referencia: el mismo XGBoost sin vecinos, semilla por semilla (tanda 54).
Se reporta además, al 10 %, cuántos inicios desde cero casos anticipa cada uno.

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
