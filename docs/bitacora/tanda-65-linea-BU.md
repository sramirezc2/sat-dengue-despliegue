# Tanda 65, línea BU — XGBoost simple con clima y aprendizaje lento

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **cerrada** el 11 de noviembre de 2026. Se corre sobre la base común del
> retroanálisis: `canonical.mode=approved`, calendario y departamentos de
> `parameters_retroanalisis.yml` sin tocar, `conjunto.csv` reportado.

## Origen

La tanda 54 mostró que el XGBoost de profundidad 2 sin clima casi no depende de la
semilla, y que con clima se dispersa (tanda 31, −10 a +4 en T+1). En la tanda 20,
eta 0,02 con 600 rondas se probó solo con profundidad 4.

## Hipótesis

Con aprendizaje más lento, el XGBoost de profundidad 2 con clima aprovecha el clima
sin la dispersión entre semillas, y se acerca a la logística con clima.

## Qué se corre

XGBoost de profundidad 2 con las 33 variables del contrato (con clima), eta 0,02 y
600 rondas, cinco semillas (53, 7, 13, 29 y 42). Referencias: la logística con clima y
el XGBoost de profundidad 2 con clima de la tanda 31 (eta 0,05, 300 rondas), semilla
por semilla.

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

## Resultado: aprender más lento no estabiliza al XGBoost con clima

Contra la logística con clima:

| T+1, 641 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| xgb_d2_lento_s53 | condicionado | 817 | 359 | 336 | -23 (-46 a -1) | -3.6 | 11.22 → 11.78 | 1+ / 6− |
| xgb_d2_lento_s53 | 5 % | 328 | 180 | 171 | -9 (-29 a 9) | -1.4 | 3.63 → 3.85 |  |
| xgb_d2_lento_s53 | 10 % | 656 | 308 | 297 | -11 (-31 a 9) | -1.7 | 8.53 → 8.79 |  |
| xgb_d2_lento_s53 | 20 % | 1230 | 441 | 439 | -2 (-21 a 16) | -0.3 | 19.33 → 19.38 |  |
| xgb_d2_lento_s7 | condicionado | 817 | 359 | 343 | -16 (-38 a 6) | -2.5 | 11.22 → 11.61 | 1+ / 6− |
| xgb_d2_lento_s7 | 5 % | 328 | 180 | 172 | -8 (-26 a 10) | -1.2 | 3.63 → 3.82 |  |
| xgb_d2_lento_s7 | 10 % | 656 | 308 | 292 | -16 (-37 a 4) | -2.5 | 8.53 → 8.92 |  |
| xgb_d2_lento_s7 | 20 % | 1230 | 441 | 439 | -2 (-21 a 16) | -0.3 | 19.33 → 19.38 |  |
| xgb_d2_lento_s13 | condicionado | 817 | 359 | 339 | -20 (-43 a 1) | -3.1 | 11.22 → 11.71 | 0+ / 6− |
| xgb_d2_lento_s13 | 5 % | 328 | 180 | 172 | -8 (-29 a 10) | -1.2 | 3.63 → 3.82 |  |
| xgb_d2_lento_s13 | 10 % | 656 | 308 | 292 | -16 (-35 a 2) | -2.5 | 8.53 → 8.92 |  |
| xgb_d2_lento_s13 | 20 % | 1230 | 441 | 438 | -3 (-24 a 15) | -0.5 | 19.33 → 19.40 |  |
| xgb_d2_lento_s29 | condicionado | 817 | 359 | 342 | -17 (-39 a 3) | -2.7 | 11.22 → 11.64 | 1+ / 6− |
| xgb_d2_lento_s29 | 5 % | 328 | 180 | 174 | -6 (-26 a 12) | -0.9 | 3.63 → 3.77 |  |
| xgb_d2_lento_s29 | 10 % | 656 | 308 | 299 | -9 (-29 a 13) | -1.4 | 8.53 → 8.75 |  |
| xgb_d2_lento_s29 | 20 % | 1230 | 441 | 442 | +1 (-18 a 20) | +0.2 | 19.33 → 19.30 |  |
| xgb_d2_lento_s42 | condicionado | 817 | 359 | 340 | -19 (-40 a 1) | -3.0 | 11.22 → 11.69 | 1+ / 5− |
| xgb_d2_lento_s42 | 5 % | 328 | 180 | 175 | -5 (-24 a 12) | -0.8 | 3.63 → 3.75 |  |
| xgb_d2_lento_s42 | 10 % | 656 | 308 | 298 | -10 (-27 a 9) | -1.6 | 8.53 → 8.77 |  |
| xgb_d2_lento_s42 | 20 % | 1230 | 441 | 437 | -4 (-23 a 15) | -0.6 | 19.33 → 19.43 |  |

| T+2, 459 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| xgb_d2_lento_s53 | condicionado | 1158 | 253 | 249 | -4 (-21 a 12) | -0.9 | 22.39 → 22.49 | 4+ / 3− |
| xgb_d2_lento_s53 | 5 % | 324 | 103 | 109 | +6 (-8 a 21) | +1.3 | 5.47 → 5.32 |  |
| xgb_d2_lento_s53 | 10 % | 648 | 192 | 185 | -7 (-24 a 9) | -1.5 | 11.28 → 11.45 |  |
| xgb_d2_lento_s53 | 20 % | 1215 | 291 | 276 | -15 (-36 a 5) | -3.3 | 22.86 → 23.23 |  |
| xgb_d2_lento_s7 | condicionado | 1158 | 253 | 243 | -10 (-26 a 6) | -2.2 | 22.39 → 22.64 | 3+ / 4− |
| xgb_d2_lento_s7 | 5 % | 324 | 103 | 107 | +4 (-11 a 19) | +0.9 | 5.47 → 5.37 |  |
| xgb_d2_lento_s7 | 10 % | 648 | 192 | 185 | -7 (-23 a 8) | -1.5 | 11.28 → 11.45 |  |
| xgb_d2_lento_s7 | 20 % | 1215 | 291 | 271 | -20 (-41 a 0) | -4.4 | 22.86 → 23.35 |  |
| xgb_d2_lento_s13 | condicionado | 1158 | 253 | 251 | -2 (-18 a 14) | -0.4 | 22.39 → 22.44 | 2+ / 3− |
| xgb_d2_lento_s13 | 5 % | 324 | 103 | 106 | +3 (-11 a 18) | +0.7 | 5.47 → 5.39 |  |
| xgb_d2_lento_s13 | 10 % | 648 | 192 | 188 | -4 (-20 a 12) | -0.9 | 11.28 → 11.38 |  |
| xgb_d2_lento_s13 | 20 % | 1215 | 291 | 275 | -16 (-37 a 5) | -3.5 | 22.86 → 23.26 |  |
| xgb_d2_lento_s29 | condicionado | 1158 | 253 | 244 | -9 (-26 a 6) | -2.0 | 22.39 → 22.61 | 2+ / 4− |
| xgb_d2_lento_s29 | 5 % | 324 | 103 | 109 | +6 (-8 a 20) | +1.3 | 5.47 → 5.32 |  |
| xgb_d2_lento_s29 | 10 % | 648 | 192 | 190 | -2 (-17 a 13) | -0.4 | 11.28 → 11.33 |  |
| xgb_d2_lento_s29 | 20 % | 1215 | 291 | 270 | -21 (-43 a -1) | -4.6 | 22.86 → 23.38 |  |
| xgb_d2_lento_s42 | condicionado | 1158 | 253 | 251 | -2 (-18 a 15) | -0.4 | 22.39 → 22.44 | 3+ / 2− |
| xgb_d2_lento_s42 | 5 % | 324 | 103 | 105 | +2 (-12 a 17) | +0.4 | 5.47 → 5.42 |  |
| xgb_d2_lento_s42 | 10 % | 648 | 192 | 187 | -5 (-21 a 10) | -1.1 | 11.28 → 11.41 |  |
| xgb_d2_lento_s42 | 20 % | 1215 | 291 | 272 | -19 (-38 a 0) | -4.1 | 22.86 → 23.33 |  |

Contra el XGBoost de profundidad 2 con clima rápido de la tanda 31, semilla por
semilla, al presupuesto del canal condicionado:

| Combinación | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| xgb_d2_lento_s53 | condicionado | 817 | 351 | 336 | -15 (-25 a -5) | -2.3 | 11.42 → 11.78 | 0+ / 6− |
| xgb_d2_lento_s53 | condicionado | 1158 | 242 | 249 | +7 (-3 a 17) | +1.5 | 22.66 → 22.49 | 4+ / 2− |
| xgb_d2_lento_s7 | condicionado | 817 | 337 | 343 | +6 (-3 a 14) | +0.9 | 11.76 → 11.61 | 4+ / 1− |
| xgb_d2_lento_s7 | condicionado | 1158 | 244 | 243 | -1 (-8 a 5) | -0.2 | 22.61 → 22.64 | 2+ / 1− |
| xgb_d2_lento_s13 | condicionado | 817 | 343 | 339 | -4 (-13 a 5) | -0.6 | 11.61 → 11.71 | 3+ / 3− |
| xgb_d2_lento_s13 | condicionado | 1158 | 245 | 251 | +6 (-3 a 16) | +1.3 | 22.59 → 22.44 | 4+ / 2− |
| xgb_d2_lento_s29 | condicionado | 817 | 338 | 342 | +4 (-5 a 13) | +0.6 | 11.73 → 11.64 | 3+ / 1− |
| xgb_d2_lento_s29 | condicionado | 1158 | 248 | 244 | -4 (-15 a 6) | -0.9 | 22.51 → 22.61 | 2+ / 4− |
| xgb_d2_lento_s42 | condicionado | 817 | 341 | 340 | -1 (-11 a 8) | -0.2 | 11.66 → 11.69 | 1+ / 3− |
| xgb_d2_lento_s42 | condicionado | 1158 | 244 | 251 | +7 (-1 a 16) | +1.5 | 22.61 → 22.44 | 3+ / 1− |

Al 10 % de la sección 0, contra el canal condicionado:

| Semilla | T+1 (pp, IC mes) | T+2 (pp, IC mes) | Barra T+2 |
| --- | --- | --- | --- |
| 53 | +2.0 (-0.3 a 4.4) | +5.7 (1.7 a 9.8) | CUMPLE |
| 7 | +1.4 (-0.9 a 3.7) | +6.1 (1.7 a 10.2) | CUMPLE |
| 13 | +1.9 (-0.6 a 4.4) | +6.8 (2.6 a 10.9) | CUMPLE |
| 29 | +2.7 (0.3 a 5.1) | +6.1 (2.2 a 10.0) | CUMPLE |
| 42 | +3.0 (0.3 a 5.6) | +6.1 (2.0 a 10.5) | CUMPLE |

- **Frente a la logística con clima empeora en T+1** en las cinco semillas (−16 a −23,
  cinco o seis años en contra) y queda entre −10 y −2 en T+2.
- **No se estabiliza**: frente al XGBoost rápido, en T+1 va de −15 a +6 según la
  semilla, la misma dispersión que tenía. El clima sigue siendo donde XGBoost se
  dispersa, aprenda rápido o lento.
- Al 10 % pasa la barra en T+2 con las cinco semillas (+5,7 a +6,8), por debajo de la
  logística con clima (+7,2).

Corrida del 11 de noviembre sobre main, combinaciones solo en YAML; mismas 8 124
filas.
