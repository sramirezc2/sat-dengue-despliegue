# Tanda 54, línea BJ — XGBoost de profundidad 2 sin clima, con cinco semillas

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **cerrada** el 11 de noviembre de 2026. Se corre sobre la base común del
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

## Resultado: sin clima, el XGBoost simple empata con la logística y casi no depende de la semilla

Contra la logística sin clima, al presupuesto del canal condicionado:

| T+1, 641 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| xgb_d2_sinclima_s53 | condicionado | 817 | 347 | 344 | -3 (-22 a 16) | -0.5 | 11.51 → 11.59 | 2+ / 4− |
| xgb_d2_sinclima_s53 | 5 % | 328 | 179 | 171 | -8 (-28 a 11) | -1.2 | 3.65 → 3.85 |  |
| xgb_d2_sinclima_s53 | 10 % | 656 | 297 | 290 | -7 (-26 a 15) | -1.1 | 8.79 → 8.97 |  |
| xgb_d2_sinclima_s53 | 20 % | 1230 | 426 | 443 | +17 (-4 a 39) | +2.7 | 19.70 → 19.28 |  |
| xgb_d2_sinclima_s7 | condicionado | 817 | 347 | 346 | -1 (-21 a 19) | -0.2 | 11.51 → 11.54 | 3+ / 4− |
| xgb_d2_sinclima_s7 | 5 % | 328 | 179 | 169 | -10 (-29 a 10) | -1.6 | 3.65 → 3.90 |  |
| xgb_d2_sinclima_s7 | 10 % | 656 | 297 | 292 | -5 (-25 a 17) | -0.8 | 8.79 → 8.92 |  |
| xgb_d2_sinclima_s7 | 20 % | 1230 | 426 | 443 | +17 (-6 a 39) | +2.7 | 19.70 → 19.28 |  |
| xgb_d2_sinclima_s13 | condicionado | 817 | 347 | 345 | -2 (-21 a 17) | -0.3 | 11.51 → 11.56 | 3+ / 3− |
| xgb_d2_sinclima_s13 | 5 % | 328 | 179 | 171 | -8 (-30 a 13) | -1.2 | 3.65 → 3.85 |  |
| xgb_d2_sinclima_s13 | 10 % | 656 | 297 | 290 | -7 (-28 a 14) | -1.1 | 8.79 → 8.97 |  |
| xgb_d2_sinclima_s13 | 20 % | 1230 | 426 | 447 | +21 (-3 a 43) | +3.3 | 19.70 → 19.18 |  |
| xgb_d2_sinclima_s29 | condicionado | 817 | 347 | 344 | -3 (-23 a 16) | -0.5 | 11.51 → 11.59 | 3+ / 3− |
| xgb_d2_sinclima_s29 | 5 % | 328 | 179 | 172 | -7 (-27 a 13) | -1.1 | 3.65 → 3.82 |  |
| xgb_d2_sinclima_s29 | 10 % | 656 | 297 | 289 | -8 (-29 a 13) | -1.2 | 8.79 → 8.99 |  |
| xgb_d2_sinclima_s29 | 20 % | 1230 | 426 | 446 | +20 (-5 a 44) | +3.1 | 19.70 → 19.21 |  |
| xgb_d2_sinclima_s42 | condicionado | 817 | 347 | 344 | -3 (-23 a 18) | -0.5 | 11.51 → 11.59 | 3+ / 4− |
| xgb_d2_sinclima_s42 | 5 % | 328 | 179 | 172 | -7 (-29 a 14) | -1.1 | 3.65 → 3.82 |  |
| xgb_d2_sinclima_s42 | 10 % | 656 | 297 | 285 | -12 (-33 a 9) | -1.9 | 8.79 → 9.09 |  |
| xgb_d2_sinclima_s42 | 20 % | 1230 | 426 | 440 | +14 (-8 a 36) | +2.2 | 19.70 → 19.35 |  |

| T+2, 459 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| xgb_d2_sinclima_s53 | condicionado | 1158 | 248 | 244 | -4 (-22 a 15) | -0.9 | 22.51 → 22.61 | 2+ / 4− |
| xgb_d2_sinclima_s53 | 5 % | 324 | 106 | 114 | +8 (-5 a 21) | +1.7 | 5.39 → 5.20 |  |
| xgb_d2_sinclima_s53 | 10 % | 648 | 190 | 187 | -3 (-17 a 12) | -0.7 | 11.33 → 11.41 |  |
| xgb_d2_sinclima_s53 | 20 % | 1215 | 276 | 280 | +4 (-17 a 25) | +0.9 | 23.23 → 23.13 |  |
| xgb_d2_sinclima_s7 | condicionado | 1158 | 248 | 247 | -1 (-20 a 17) | -0.2 | 22.51 → 22.54 | 2+ / 2− |
| xgb_d2_sinclima_s7 | 5 % | 324 | 106 | 107 | +1 (-10 a 13) | +0.2 | 5.39 → 5.37 |  |
| xgb_d2_sinclima_s7 | 10 % | 648 | 190 | 194 | +4 (-12 a 20) | +0.9 | 11.33 → 11.23 |  |
| xgb_d2_sinclima_s7 | 20 % | 1215 | 276 | 275 | -1 (-22 a 21) | -0.2 | 23.23 → 23.26 |  |
| xgb_d2_sinclima_s13 | condicionado | 1158 | 248 | 247 | -1 (-20 a 17) | -0.2 | 22.51 → 22.54 | 2+ / 3− |
| xgb_d2_sinclima_s13 | 5 % | 324 | 106 | 112 | +6 (-7 a 20) | +1.3 | 5.39 → 5.24 |  |
| xgb_d2_sinclima_s13 | 10 % | 648 | 190 | 189 | -1 (-16 a 14) | -0.2 | 11.33 → 11.36 |  |
| xgb_d2_sinclima_s13 | 20 % | 1215 | 276 | 279 | +3 (-17 a 23) | +0.7 | 23.23 → 23.16 |  |
| xgb_d2_sinclima_s29 | condicionado | 1158 | 248 | 250 | +2 (-17 a 22) | +0.4 | 22.51 → 22.46 | 2+ / 3− |
| xgb_d2_sinclima_s29 | 5 % | 324 | 106 | 113 | +7 (-5 a 21) | +1.5 | 5.39 → 5.22 |  |
| xgb_d2_sinclima_s29 | 10 % | 648 | 190 | 185 | -5 (-21 a 12) | -1.1 | 11.33 → 11.45 |  |
| xgb_d2_sinclima_s29 | 20 % | 1215 | 276 | 277 | +1 (-20 a 21) | +0.2 | 23.23 → 23.21 |  |
| xgb_d2_sinclima_s42 | condicionado | 1158 | 248 | 244 | -4 (-22 a 13) | -0.9 | 22.51 → 22.61 | 3+ / 4− |
| xgb_d2_sinclima_s42 | 5 % | 324 | 106 | 111 | +5 (-8 a 20) | +1.1 | 5.39 → 5.27 |  |
| xgb_d2_sinclima_s42 | 10 % | 648 | 190 | 192 | +2 (-12 a 16) | +0.4 | 11.33 → 11.28 |  |
| xgb_d2_sinclima_s42 | 20 % | 1215 | 276 | 274 | -2 (-24 a 18) | -0.4 | 23.23 → 23.28 |  |

- **Las cinco semillas quedan entre −3 y −1 en T+1 y entre −4 y +2 en T+2**: empate
  con la logística sin clima. Con clima (tanda 31) la profundidad 2 quedaba entre
  −10 y +4, así que **quitarle el clima le quitó casi toda la variación entre
  semillas**: el clima es donde XGBoost se dispersa.
- Al 10 % de la sección 0 las cinco semillas pasan la barra en T+2:

| Combinación | T+1 (pp, IC mes) | T+2 (pp, IC mes) | Barra T+2 |
| --- | --- | --- | --- |
| xgb_d2_sinclima_s53 | +0.9 (-1.2 a 3.1) | +5.9 (1.7 a 9.8) | CUMPLE |
| xgb_d2_sinclima_s7 | +1.2 (-1.1 a 3.4) | +7.2 (3.3 a 11.1) | CUMPLE |
| xgb_d2_sinclima_s13 | +1.1 (-1.2 a 3.3) | +6.8 (2.8 a 10.7) | CUMPLE |
| xgb_d2_sinclima_s29 | +1.1 (-1.1 a 3.3) | +6.8 (2.6 a 10.7) | CUMPLE |
| xgb_d2_sinclima_s42 | +1.4 (-0.8 a 3.6) | +6.5 (2.4 a 10.5) | CUMPLE |

Lectura: sin clima, un XGBoost de árboles de profundidad 2 es prácticamente
equivalente a la logística (las dos son casi aditivas). La logística sigue siendo
preferible por determinista y explicable, pero el resultado de T+2 no depende de la
familia mientras el modelo sea simple.

Corrida del 11 de noviembre sobre main (`3011db9`), mismo panel y mismas filas (8 124 predicciones por combinación).
