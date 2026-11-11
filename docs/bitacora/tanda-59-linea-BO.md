# Tanda 59, línea BO — Vecinos en un árbol simple

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **cerrada** el 11 de noviembre de 2026. Se corre sobre la base común del
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

## Resultado: el árbol tampoco aprovecha a los vecinos

Contra el mismo XGBoost sin vecinos, semilla por semilla, al presupuesto del canal
condicionado:

| T+1, 641 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| xgb_d2_sinclima_vecinos_s53 | condicionado | 817 | 344 | 342 | -2 (-16 a 11) | -0.3 | 11.59 → 11.64 | 3+ / 3− |
| xgb_d2_sinclima_vecinos_s53 | 5 % | 328 | 171 | 158 | -13 (-26 a 1) | -2.0 | 3.85 → 4.16 |  |
| xgb_d2_sinclima_vecinos_s53 | 10 % | 656 | 290 | 284 | -6 (-22 a 10) | -0.9 | 8.97 → 9.11 |  |
| xgb_d2_sinclima_vecinos_s53 | 20 % | 1230 | 443 | 431 | -12 (-25 a 1) | -1.9 | 19.28 → 19.57 |  |

| T+2, 459 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| xgb_d2_sinclima_vecinos_s53 | condicionado | 1158 | 244 | 250 | +6 (-6 a 19) | +1.3 | 22.61 → 22.46 | 4+ / 2− |
| xgb_d2_sinclima_vecinos_s53 | 5 % | 324 | 114 | 110 | -4 (-16 a 8) | -0.9 | 5.20 → 5.29 |  |
| xgb_d2_sinclima_vecinos_s53 | 10 % | 648 | 187 | 193 | +6 (-9 a 21) | +1.3 | 11.41 → 11.26 |  |
| xgb_d2_sinclima_vecinos_s53 | 20 % | 1215 | 280 | 277 | -3 (-20 a 14) | -0.7 | 23.13 → 23.21 |  |

| T+1, 641 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| xgb_d2_sinclima_vecinos_s7 | condicionado | 817 | 346 | 344 | -2 (-14 a 12) | -0.3 | 11.54 → 11.59 | 2+ / 4− |
| xgb_d2_sinclima_vecinos_s7 | 5 % | 328 | 169 | 160 | -9 (-23 a 4) | -1.4 | 3.90 → 4.12 |  |
| xgb_d2_sinclima_vecinos_s7 | 10 % | 656 | 292 | 281 | -11 (-28 a 6) | -1.7 | 8.92 → 9.19 |  |
| xgb_d2_sinclima_vecinos_s7 | 20 % | 1230 | 443 | 440 | -3 (-17 a 11) | -0.5 | 19.28 → 19.35 |  |

| T+2, 459 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| xgb_d2_sinclima_vecinos_s7 | condicionado | 1158 | 247 | 242 | -5 (-16 a 8) | -1.1 | 22.54 → 22.66 | 2+ / 4− |
| xgb_d2_sinclima_vecinos_s7 | 5 % | 324 | 107 | 113 | +6 (-8 a 20) | +1.3 | 5.37 → 5.22 |  |
| xgb_d2_sinclima_vecinos_s7 | 10 % | 648 | 194 | 197 | +3 (-12 a 17) | +0.7 | 11.23 → 11.16 |  |
| xgb_d2_sinclima_vecinos_s7 | 20 % | 1215 | 275 | 273 | -2 (-18 a 14) | -0.4 | 23.26 → 23.31 |  |

| T+1, 641 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| xgb_d2_sinclima_vecinos_s13 | condicionado | 817 | 345 | 339 | -6 (-21 a 11) | -0.9 | 11.56 → 11.71 | 3+ / 4− |
| xgb_d2_sinclima_vecinos_s13 | 5 % | 328 | 171 | 159 | -12 (-29 a 5) | -1.9 | 3.85 → 4.14 |  |
| xgb_d2_sinclima_vecinos_s13 | 10 % | 656 | 290 | 285 | -5 (-19 a 10) | -0.8 | 8.97 → 9.09 |  |
| xgb_d2_sinclima_vecinos_s13 | 20 % | 1230 | 447 | 430 | -17 (-32 a -3) | -2.7 | 19.18 → 19.60 |  |

| T+2, 459 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| xgb_d2_sinclima_vecinos_s13 | condicionado | 1158 | 247 | 246 | -1 (-13 a 12) | -0.2 | 22.54 → 22.56 | 2+ / 4− |
| xgb_d2_sinclima_vecinos_s13 | 5 % | 324 | 112 | 108 | -4 (-19 a 10) | -0.9 | 5.24 → 5.34 |  |
| xgb_d2_sinclima_vecinos_s13 | 10 % | 648 | 189 | 190 | +1 (-15 a 18) | +0.2 | 11.36 → 11.33 |  |
| xgb_d2_sinclima_vecinos_s13 | 20 % | 1215 | 279 | 272 | -7 (-21 a 7) | -1.5 | 23.16 → 23.33 |  |

| T+1, 641 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| xgb_d2_sinclima_vecinos_s29 | condicionado | 817 | 344 | 340 | -4 (-20 a 12) | -0.6 | 11.59 → 11.69 | 3+ / 4− |
| xgb_d2_sinclima_vecinos_s29 | 5 % | 328 | 172 | 157 | -15 (-29 a 1) | -2.3 | 3.82 → 4.19 |  |
| xgb_d2_sinclima_vecinos_s29 | 10 % | 656 | 289 | 285 | -4 (-19 a 12) | -0.6 | 8.99 → 9.09 |  |
| xgb_d2_sinclima_vecinos_s29 | 20 % | 1230 | 446 | 432 | -14 (-27 a 0) | -2.2 | 19.21 → 19.55 |  |

| T+2, 459 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| xgb_d2_sinclima_vecinos_s29 | condicionado | 1158 | 250 | 252 | +2 (-11 a 16) | +0.4 | 22.46 → 22.41 | 2+ / 2− |
| xgb_d2_sinclima_vecinos_s29 | 5 % | 324 | 113 | 111 | -2 (-16 a 12) | -0.4 | 5.22 → 5.27 |  |
| xgb_d2_sinclima_vecinos_s29 | 10 % | 648 | 185 | 189 | +4 (-13 a 22) | +0.9 | 11.45 → 11.36 |  |
| xgb_d2_sinclima_vecinos_s29 | 20 % | 1215 | 277 | 272 | -5 (-20 a 11) | -1.1 | 23.21 → 23.33 |  |

| T+1, 641 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| xgb_d2_sinclima_vecinos_s42 | condicionado | 817 | 344 | 336 | -8 (-22 a 5) | -1.2 | 11.59 → 11.78 | 2+ / 4− |
| xgb_d2_sinclima_vecinos_s42 | 5 % | 328 | 172 | 165 | -7 (-24 a 11) | -1.1 | 3.82 → 3.99 |  |
| xgb_d2_sinclima_vecinos_s42 | 10 % | 656 | 285 | 281 | -4 (-18 a 9) | -0.6 | 9.09 → 9.19 |  |
| xgb_d2_sinclima_vecinos_s42 | 20 % | 1230 | 440 | 433 | -7 (-21 a 7) | -1.1 | 19.35 → 19.52 |  |

| T+2, 459 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| xgb_d2_sinclima_vecinos_s42 | condicionado | 1158 | 244 | 247 | +3 (-8 a 16) | +0.7 | 22.61 → 22.54 | 3+ / 2− |
| xgb_d2_sinclima_vecinos_s42 | 5 % | 324 | 111 | 106 | -5 (-21 a 10) | -1.1 | 5.27 → 5.39 |  |
| xgb_d2_sinclima_vecinos_s42 | 10 % | 648 | 192 | 189 | -3 (-19 a 14) | -0.7 | 11.28 → 11.36 |  |
| xgb_d2_sinclima_vecinos_s42 | 20 % | 1215 | 274 | 275 | +1 (-16 a 19) | +0.2 | 23.28 → 23.26 |  |

Inicios desde cero casos en el mes de origen, al 10 % de la sección 0 (185 en T+1 y
153 en T+2):

| Horizonte | Semilla | Desde cero casos: sin vecinos → con vecinos | Total al 10 %: sin → con |
| --- | --- | --- | --- |
| T+1 | 53 | 30 → 33 | 285 → 283 |
| T+1 | 7 | 34 → 31 | 287 → 282 |
| T+1 | 13 | 32 → 34 | 286 → 291 |
| T+1 | 29 | 33 → 32 | 286 → 285 |
| T+1 | 42 | 31 → 32 | 288 → 278 |
| T+2 | 53 | 47 → 52 | 179 → 181 |
| T+2 | 7 | 49 → 48 | 185 → 184 |
| T+2 | 13 | 52 → 50 | 183 → 183 |
| T+2 | 29 | 52 → 50 | 183 → 178 |
| T+2 | 42 | 49 → 47 | 182 → 183 |

- En T+1 el bloque **resta en las cinco semillas** (−2 a −8); en T+2 queda entre −5
  y +6. Veredicto: **sin efecto**.
- Los inicios desde cero casos tampoco suben de forma consistente (entre −3 y +5
  según la semilla). La hipótesis de que un árbol haría solo el corte «cero casos» y
  usaría a los vecinos ahí no se sostiene con profundidad 2 y estas tres columnas.
- Con las tandas 51, 57 y 59, la información de alrededor (departamento o cinco
  vecinos, lineal o con árboles) no mejora el total.

Corrida del 11 de noviembre sobre main (`a9c2c1a`), con el bloque de vecinos del PR
#9; combinaciones solo en YAML, sin cambios de código. Mismas 8 124 filas.
