# Tanda 31, línea AM — XGBoost de profundidad 2 con cinco semillas

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **cerrada** el 11 de noviembre de 2026. Se corre sobre la base común del
> retroanálisis: `canonical.mode=approved`, calendario y departamentos de
> `parameters_retroanalisis.yml` sin tocar, `conjunto.csv` reportado.

## Origen

Preinscrita en la tanda 20: la única variante de XGBoost que quedó por encima de
la logística en T+1 (+4, IC −17 a 24) fue la de profundidad 2, con una sola
semilla.

## Hipótesis

Si esa ventaja es real, se mantiene con otras semillas. Si es ruido de semilla
(la tanda 14 midió una variación de 17 inicios entre semillas), desaparece.

## Qué se corre

XGBoost de profundidad 2 con las semillas 7, 13, 29 y 42, además de la 53 ya
corrida. Se reporta la media y el rango de las cinco contra la logística sin
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

## Resultado: la ventaja sobre la logística era de la semilla

Contra la logística sin clima, al presupuesto del canal condicionado:

| T+1, 641 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| xgb_d2 | condicionado | 817 | 347 | 351 | +4 (-17 a 24) | +0.6 | 11.51 → 11.42 | 2+ / 2− |
| xgb_d2 | 5 % | 328 | 179 | 168 | -11 (-29 a 5) | -1.7 | 3.65 → 3.92 |  |
| xgb_d2 | 10 % | 656 | 297 | 293 | -4 (-27 a 17) | -0.6 | 8.79 → 8.89 |  |
| xgb_d2 | 20 % | 1230 | 426 | 445 | +19 (-8 a 45) | +3.0 | 19.70 → 19.23 |  |
| xgb_d2_s13 | condicionado | 817 | 347 | 343 | -4 (-26 a 17) | -0.6 | 11.51 → 11.61 | 1+ / 4− |
| xgb_d2_s13 | 5 % | 328 | 179 | 169 | -10 (-29 a 8) | -1.6 | 3.65 → 3.90 |  |
| xgb_d2_s13 | 10 % | 656 | 297 | 293 | -4 (-25 a 16) | -0.6 | 8.79 → 8.89 |  |
| xgb_d2_s13 | 20 % | 1230 | 426 | 438 | +12 (-13 a 37) | +1.9 | 19.70 → 19.40 |  |
| xgb_d2_s29 | condicionado | 817 | 347 | 338 | -9 (-33 a 12) | -1.4 | 11.51 → 11.73 | 1+ / 5− |
| xgb_d2_s29 | 5 % | 328 | 179 | 170 | -9 (-30 a 10) | -1.4 | 3.65 → 3.87 |  |
| xgb_d2_s29 | 10 % | 656 | 297 | 293 | -4 (-27 a 20) | -0.6 | 8.79 → 8.89 |  |
| xgb_d2_s29 | 20 % | 1230 | 426 | 437 | +11 (-13 a 35) | +1.7 | 19.70 → 19.43 |  |
| xgb_d2_s42 | condicionado | 817 | 347 | 341 | -6 (-29 a 17) | -0.9 | 11.51 → 11.66 | 2+ / 5− |
| xgb_d2_s42 | 5 % | 328 | 179 | 170 | -9 (-30 a 9) | -1.4 | 3.65 → 3.87 |  |
| xgb_d2_s42 | 10 % | 656 | 297 | 289 | -8 (-28 a 11) | -1.2 | 8.79 → 8.99 |  |
| xgb_d2_s42 | 20 % | 1230 | 426 | 436 | +10 (-16 a 36) | +1.6 | 19.70 → 19.45 |  |
| xgb_d2_s7 | condicionado | 817 | 347 | 337 | -10 (-34 a 12) | -1.6 | 11.51 → 11.76 | 1+ / 6− |
| xgb_d2_s7 | 5 % | 328 | 179 | 171 | -8 (-30 a 11) | -1.2 | 3.65 → 3.85 |  |
| xgb_d2_s7 | 10 % | 656 | 297 | 294 | -3 (-25 a 19) | -0.5 | 8.79 → 8.87 |  |
| xgb_d2_s7 | 20 % | 1230 | 426 | 442 | +16 (-10 a 42) | +2.5 | 19.70 → 19.30 |  |

| T+2, 459 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| xgb_d2 | condicionado | 1158 | 248 | 242 | -6 (-25 a 13) | -1.3 | 22.51 → 22.66 | 3+ / 4− |
| xgb_d2 | 5 % | 324 | 106 | 108 | +2 (-14 a 19) | +0.4 | 5.39 → 5.34 |  |
| xgb_d2 | 10 % | 648 | 190 | 188 | -2 (-20 a 17) | -0.4 | 11.33 → 11.38 |  |
| xgb_d2 | 20 % | 1215 | 276 | 269 | -7 (-31 a 15) | -1.5 | 23.23 → 23.40 |  |
| xgb_d2_s13 | condicionado | 1158 | 248 | 245 | -3 (-23 a 16) | -0.7 | 22.51 → 22.59 | 3+ / 3− |
| xgb_d2_s13 | 5 % | 324 | 106 | 106 | +0 (-19 a 22) | +0.0 | 5.39 → 5.39 |  |
| xgb_d2_s13 | 10 % | 648 | 190 | 184 | -6 (-24 a 12) | -1.3 | 11.33 → 11.48 |  |
| xgb_d2_s13 | 20 % | 1215 | 276 | 276 | +0 (-24 a 22) | +0.0 | 23.23 → 23.23 |  |
| xgb_d2_s29 | condicionado | 1158 | 248 | 248 | +0 (-21 a 20) | +0.0 | 22.51 → 22.51 | 3+ / 4− |
| xgb_d2_s29 | 5 % | 324 | 106 | 101 | -5 (-23 a 14) | -1.1 | 5.39 → 5.52 |  |
| xgb_d2_s29 | 10 % | 648 | 190 | 189 | -1 (-20 a 18) | -0.2 | 11.33 → 11.36 |  |
| xgb_d2_s29 | 20 % | 1215 | 276 | 269 | -7 (-31 a 15) | -1.5 | 23.23 → 23.40 |  |
| xgb_d2_s42 | condicionado | 1158 | 248 | 244 | -4 (-24 a 15) | -0.9 | 22.51 → 22.61 | 2+ / 3− |
| xgb_d2_s42 | 5 % | 324 | 106 | 108 | +2 (-14 a 19) | +0.4 | 5.39 → 5.34 |  |
| xgb_d2_s42 | 10 % | 648 | 190 | 185 | -5 (-23 a 12) | -1.1 | 11.33 → 11.45 |  |
| xgb_d2_s42 | 20 % | 1215 | 276 | 271 | -5 (-27 a 15) | -1.1 | 23.23 → 23.35 |  |
| xgb_d2_s7 | condicionado | 1158 | 248 | 244 | -4 (-24 a 16) | -0.9 | 22.51 → 22.61 | 2+ / 4− |
| xgb_d2_s7 | 5 % | 324 | 106 | 108 | +2 (-15 a 20) | +0.4 | 5.39 → 5.34 |  |
| xgb_d2_s7 | 10 % | 648 | 190 | 194 | +4 (-17 a 25) | +0.9 | 11.33 → 11.23 |  |
| xgb_d2_s7 | 20 % | 1215 | 276 | 269 | -7 (-29 a 14) | -1.5 | 23.23 → 23.40 |  |

- La semilla 53 era la única por encima de la logística en T+1 (+4). **Con las otras
  cuatro, profundidad 2 queda entre −4 y −10 en T+1** y entre −4 y 0 en T+2.
  Veredicto: **sin efecto frente a la logística**, y la regla 9 evitó declarar una
  ventaja que no existía.

Al 10 % de la sección 0, contra el canal condicionado:

| Semilla | T+1 (pp, IC mes) | T+2 (pp, IC mes) | Barra T+2 |
| --- | --- | --- | --- |
| 53 | +2.3 (-0.2 a 4.8) | +5.7 (1.5 a 9.6) | CUMPLE |
| 7 | +2.2 (-0.3 a 4.7) | +7.2 (3.0 a 11.5) | CUMPLE |
| 13 | +1.7 (-0.8 a 4.1) | +6.5 (2.4 a 10.7) | CUMPLE |
| 29 | +1.6 (-0.8 a 4.1) | +5.7 (1.7 a 9.8) | CUMPLE |
| 42 | +2.3 (-0.2 a 5.0) | +5.4 (1.5 a 9.4) | CUMPLE |

- En cambio, **profundidad 2 es mucho más estable que el XGBoost del banco**: las
  cinco semillas pasan la barra en T+2 (+5,4 a +7,2, media +6,1), cuando el del
  banco solo la pasaba con una de cinco (tanda 33). Es un XGBoost casi lineal, y se
  comporta casi como la logística.
