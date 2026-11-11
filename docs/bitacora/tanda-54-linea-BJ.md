# Tanda 54, línea BJ — XGBoost de profundidad 2 sin clima, con cinco semillas

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **preinscrita, sin correr.** Se corre sobre la base común del
> retroanálisis: `canonical.mode=approved`, calendario y departamentos de
> `parameters_retroanalisis.yml` sin tocar, `conjunto.csv` reportado.

## Origen

En la tanda 31 el XGBoost de profundidad 2, que usa las 33 variables del contrato
con clima, pasó la barra en T+2 al 10 % con las cinco semillas. En la tanda 20
quitarle el clima al XGBoost del banco no cambió nada, pero no se probó con
profundidad 2.

## Hipótesis

Si la estabilidad de la profundidad 2 viene del árbol simple y no del clima, sin
clima debería seguir pasando la barra en T+2 y quedar cerca de la logística sin
clima, que es su comparación pareja.

## Qué se corre

XGBoost de profundidad 2 sin las nueve variables de clima, con las semillas 53, 7,
13, 29 y 42 (regla 9). Referencias: la logística sin clima y el XGBoost de
profundidad 2 con clima de la tanda 31. Se reporta también el veredicto al 10 %.

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
