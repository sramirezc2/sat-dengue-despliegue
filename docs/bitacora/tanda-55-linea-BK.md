# Tanda 55, línea BK — Ensamble de dos modelos buenos y distintos

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **cerrada** el 11 de noviembre de 2026. Se corre sobre la base común del
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

## Resultado: el ensamble queda por debajo de la logística con clima sola

Contra la logística con clima, al presupuesto del canal condicionado:

| T+1, 641 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ens_log_conclima+xgb_d2_sinclima_s53 | condicionado | 817 | 359 | 353 | -6 (-20 a 8) | -0.9 | 11.22 → 11.37 | 0+ / 2− |
| ens_log_conclima+xgb_d2_sinclima_s53 | 5 % | 328 | 180 | 178 | -2 (-15 a 10) | -0.3 | 3.63 → 3.67 |  |
| ens_log_conclima+xgb_d2_sinclima_s53 | 10 % | 656 | 308 | 299 | -9 (-24 a 7) | -1.4 | 8.53 → 8.75 |  |
| ens_log_conclima+xgb_d2_sinclima_s53 | 20 % | 1230 | 441 | 454 | +13 (-1 a 26) | +2.0 | 19.33 → 19.01 |  |
| ens_log_conclima+xgb_d2_sinclima_s7 | condicionado | 817 | 359 | 355 | -4 (-18 a 11) | -0.6 | 11.22 → 11.32 | 1+ / 2− |
| ens_log_conclima+xgb_d2_sinclima_s7 | 5 % | 328 | 180 | 179 | -1 (-14 a 11) | -0.2 | 3.63 → 3.65 |  |
| ens_log_conclima+xgb_d2_sinclima_s7 | 10 % | 656 | 308 | 304 | -4 (-17 a 10) | -0.6 | 8.53 → 8.62 |  |
| ens_log_conclima+xgb_d2_sinclima_s7 | 20 % | 1230 | 441 | 456 | +15 (0 a 29) | +2.3 | 19.33 → 18.96 |  |
| ens_log_conclima+xgb_d2_sinclima_s13 | condicionado | 817 | 359 | 356 | -3 (-17 a 12) | -0.5 | 11.22 → 11.29 | 1+ / 3− |
| ens_log_conclima+xgb_d2_sinclima_s13 | 5 % | 328 | 180 | 179 | -1 (-14 a 11) | -0.2 | 3.63 → 3.65 |  |
| ens_log_conclima+xgb_d2_sinclima_s13 | 10 % | 656 | 308 | 307 | -1 (-15 a 13) | -0.2 | 8.53 → 8.55 |  |
| ens_log_conclima+xgb_d2_sinclima_s13 | 20 % | 1230 | 441 | 449 | +8 (-8 a 22) | +1.2 | 19.33 → 19.13 |  |
| ens_log_conclima+xgb_d2_sinclima_s29 | condicionado | 817 | 359 | 353 | -6 (-21 a 9) | -0.9 | 11.22 → 11.37 | 0+ / 3− |
| ens_log_conclima+xgb_d2_sinclima_s29 | 5 % | 328 | 180 | 181 | +1 (-13 a 13) | +0.2 | 3.63 → 3.60 |  |
| ens_log_conclima+xgb_d2_sinclima_s29 | 10 % | 656 | 308 | 302 | -6 (-21 a 9) | -0.9 | 8.53 → 8.67 |  |
| ens_log_conclima+xgb_d2_sinclima_s29 | 20 % | 1230 | 441 | 452 | +11 (-4 a 25) | +1.7 | 19.33 → 19.06 |  |
| ens_log_conclima+xgb_d2_sinclima_s42 | condicionado | 817 | 359 | 353 | -6 (-21 a 9) | -0.9 | 11.22 → 11.37 | 0+ / 3− |
| ens_log_conclima+xgb_d2_sinclima_s42 | 5 % | 328 | 180 | 177 | -3 (-16 a 10) | -0.5 | 3.63 → 3.70 |  |
| ens_log_conclima+xgb_d2_sinclima_s42 | 10 % | 656 | 308 | 297 | -11 (-27 a 5) | -1.7 | 8.53 → 8.79 |  |
| ens_log_conclima+xgb_d2_sinclima_s42 | 20 % | 1230 | 441 | 449 | +8 (-7 a 21) | +1.2 | 19.33 → 19.13 |  |

| T+2, 459 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ens_log_conclima+xgb_d2_sinclima_s53 | condicionado | 1158 | 253 | 243 | -10 (-21 a 2) | -2.2 | 22.39 → 22.64 | 1+ / 5− |
| ens_log_conclima+xgb_d2_sinclima_s53 | 5 % | 324 | 103 | 108 | +5 (-6 a 15) | +1.1 | 5.47 → 5.34 |  |
| ens_log_conclima+xgb_d2_sinclima_s53 | 10 % | 648 | 192 | 198 | +6 (-5 a 18) | +1.3 | 11.28 → 11.13 |  |
| ens_log_conclima+xgb_d2_sinclima_s53 | 20 % | 1215 | 291 | 284 | -7 (-21 a 7) | -1.5 | 22.86 → 23.03 |  |
| ens_log_conclima+xgb_d2_sinclima_s7 | condicionado | 1158 | 253 | 249 | -4 (-15 a 8) | -0.9 | 22.39 → 22.49 | 3+ / 3− |
| ens_log_conclima+xgb_d2_sinclima_s7 | 5 % | 324 | 103 | 109 | +6 (-4 a 16) | +1.3 | 5.47 → 5.32 |  |
| ens_log_conclima+xgb_d2_sinclima_s7 | 10 % | 648 | 192 | 201 | +9 (-2 a 21) | +2.0 | 11.28 → 11.06 |  |
| ens_log_conclima+xgb_d2_sinclima_s7 | 20 % | 1215 | 291 | 278 | -13 (-25 a -2) | -2.8 | 22.86 → 23.18 |  |
| ens_log_conclima+xgb_d2_sinclima_s13 | condicionado | 1158 | 253 | 245 | -8 (-20 a 4) | -1.7 | 22.39 → 22.59 | 1+ / 5− |
| ens_log_conclima+xgb_d2_sinclima_s13 | 5 % | 324 | 103 | 112 | +9 (-1 a 20) | +2.0 | 5.47 → 5.24 |  |
| ens_log_conclima+xgb_d2_sinclima_s13 | 10 % | 648 | 192 | 192 | +0 (-12 a 11) | +0.0 | 11.28 → 11.28 |  |
| ens_log_conclima+xgb_d2_sinclima_s13 | 20 % | 1215 | 291 | 282 | -9 (-23 a 5) | -2.0 | 22.86 → 23.08 |  |
| ens_log_conclima+xgb_d2_sinclima_s29 | condicionado | 1158 | 253 | 245 | -8 (-19 a 2) | -1.7 | 22.39 → 22.59 | 1+ / 4− |
| ens_log_conclima+xgb_d2_sinclima_s29 | 5 % | 324 | 103 | 114 | +11 (0 a 21) | +2.4 | 5.47 → 5.20 |  |
| ens_log_conclima+xgb_d2_sinclima_s29 | 10 % | 648 | 192 | 187 | -5 (-18 a 8) | -1.1 | 11.28 → 11.41 |  |
| ens_log_conclima+xgb_d2_sinclima_s29 | 20 % | 1215 | 291 | 285 | -6 (-20 a 9) | -1.3 | 22.86 → 23.01 |  |
| ens_log_conclima+xgb_d2_sinclima_s42 | condicionado | 1158 | 253 | 248 | -5 (-16 a 7) | -1.1 | 22.39 → 22.51 | 2+ / 4− |
| ens_log_conclima+xgb_d2_sinclima_s42 | 5 % | 324 | 103 | 112 | +9 (-1 a 19) | +2.0 | 5.47 → 5.24 |  |
| ens_log_conclima+xgb_d2_sinclima_s42 | 10 % | 648 | 192 | 192 | +0 (-11 a 11) | +0.0 | 11.28 → 11.28 |  |
| ens_log_conclima+xgb_d2_sinclima_s42 | 20 % | 1215 | 291 | 283 | -8 (-22 a 6) | -1.7 | 22.86 → 23.06 |  |

Al 10 % de la sección 0, contra el canal condicionado:

| Semilla | T+1 (pp, IC mes) | T+2 (pp, IC mes) | Barra T+2 |
| --- | --- | --- | --- |
| 53 | +2.7 (0.3 a 5.1) | +5.9 (2.0 a 9.6) | CUMPLE |
| 7 | +3.0 (0.3 a 5.6) | +6.5 (2.8 a 10.2) | CUMPLE |
| 13 | +3.1 (0.6 a 5.5) | +6.5 (2.4 a 10.5) | CUMPLE |
| 29 | +2.5 (0.2 a 4.8) | +6.3 (2.4 a 10.2) | CUMPLE |
| 42 | +3.3 (0.8 a 5.8) | +6.3 (2.2 a 10.5) | CUMPLE |

- El ensamble **resta** frente a la logística con clima en las cinco semillas:
  entre −3 y −6 en T+1 y entre −4 y −10 en T+2, con más años en contra que a favor.
  Veredicto: **sin efecto, tirando a peor**.
- Al 10 % sigue pasando la barra en T+2 (+6,3 pp de media), pero por debajo del +7,2
  de la logística con clima.
- Lectura: el XGBoost sin clima no trae información que la logística con clima no
  tenga; promediar con él diluye el aporte del clima. Con esta tanda son tres
  ensambles distintos (14, 23 y 55) y ninguno supera al mejor de sus componentes.

Corrida del 11 de noviembre con `tools/noche/ensamble.py` sobre las predicciones de
las tandas 15 y 54; mismas 8 124 filas.
