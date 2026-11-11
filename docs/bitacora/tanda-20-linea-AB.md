# Tanda 20, línea AB — Ajustes de XGBoost sobre la base común

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **cerrada** el 10 de noviembre de 2026 (las variantes que faltaban se corrieron después, de a una). Se corre sobre la base común del
> retroanálisis: `canonical.mode=approved`, calendario y departamentos de
> `parameters_retroanalisis.yml` sin tocar, `conjunto.csv` reportado.

## Hipótesis

En la tanda 12 la logística le ganó al XGBoost del banco en todos los
presupuestos. Antes de concluir que la familia de árboles es peor hay que
descartar que sea esa configuración: 300 rondas, profundidad 4 y eta 0,05,
heredadas de la tanda 7 sin búsqueda. Si alguna variante razonable alcanza a la
logística, la conclusión es sobre la configuración y no sobre la familia.

Una nota que se descubrió al preparar esta tanda: el XGBoost del banco usa las
33 variables del contrato, **con clima**, mientras que la logística de
referencia es sin clima. La comparación de la tanda 12 mezcla familia y clima.

## Qué se corre

Contra el XGBoost del banco (semilla 53), una diferencia a la vez:

- profundidad 2 y profundidad 6;
- eta 0,1, y eta 0,02 con 600 rondas;
- profundidad 3 con 150 rondas;
- **sin clima**, con las mismas variables de la logística de referencia.

Para esta tanda la referencia de la sección de mejora es el XGBoost del banco, y
se reporta además cada variante contra la logística sin clima. Una variante que
supere al banco por pocos inicios no se declara mejor sin cinco semillas
(regla 9); si alguna se acerca a la logística, se corre con cinco semillas
antes de cerrar.

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

## Resultado parcial (la corrida se interrumpió)

La corrida se detuvo por falta de memoria después de tres recetas; profundidad 6,
eta 0,1, eta 0,02 y profundidad 3 quedan sin correr. Contra la logística sin
clima, al presupuesto del canal condicionado, semilla 53:

| | T+1 (347) | T+2 (248) |
| --- | --- | --- |
| XGBoost del banco | 342, −5 (IC −29 a 16) | 247, −1 (IC −21 a 18) |
| XGBoost sin clima | 343, −4 (IC −23 a 14) | 245, −3 (IC −20 a 13) |
| XGBoost profundidad 2 | 351, +4 (IC −17 a 24) | 242, −6 (IC −25 a 13) |

Quitarle el clima a XGBoost no cambia nada, así que la comparación de la tanda 12
no estaba sesgada por el clima. Ninguna variante supera a la logística; con una
sola semilla, por la regla 9, ninguna diferencia de esta tabla es concluyente.

## Resultado completo

Contra la logística sin clima, al presupuesto del canal condicionado y con la
semilla 53:

- **Más profundidad empeora**: profundidad 6 pierde **−25 en T+1 (IC −52 a −2)**,
  seis años en contra.
- **Más eta empeora**: eta 0,1 queda en −17 y −11; eta 0,02 con 600 rondas en −10 y
  −5.
- **Árboles más simples se acercan**: profundidad 2 queda en +4 en T+1 y −6 en T+2;
  profundidad 3 con 150 rondas en −1 y −4.
- Sin clima, XGBoost no cambia (−4 y −3).

Ninguna variante supera a la logística. La tendencia es clara: **cuanto más
simple el árbol, más se parece a la logística**, que es la forma más simple de
todas. Como profundidad 2 quedó por encima de la logística en T+1 con una sola
semilla, se corre con cinco semillas en la tanda 31, como dice la regla 9.

| T+1, 641 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| xgb_banco_s53 | condicionado | 817 | 347 | 342 | -5 (-29 a 16) | -0.8 | 11.51 → 11.64 | 2+ / 4− |
| xgb_banco_s53 | 5 % | 328 | 179 | 165 | -14 (-35 a 5) | -2.2 | 3.65 → 3.99 |  |
| xgb_banco_s53 | 10 % | 656 | 297 | 286 | -11 (-35 a 12) | -1.7 | 8.79 → 9.06 |  |
| xgb_banco_s53 | 20 % | 1230 | 426 | 441 | +15 (-10 a 40) | +2.3 | 19.70 → 19.33 |  |
| xgb_d2 | condicionado | 817 | 347 | 351 | +4 (-17 a 24) | +0.6 | 11.51 → 11.42 | 2+ / 2− |
| xgb_d2 | 5 % | 328 | 179 | 168 | -11 (-29 a 5) | -1.7 | 3.65 → 3.92 |  |
| xgb_d2 | 10 % | 656 | 297 | 293 | -4 (-27 a 17) | -0.6 | 8.79 → 8.89 |  |
| xgb_d2 | 20 % | 1230 | 426 | 445 | +19 (-8 a 45) | +3.0 | 19.70 → 19.23 |  |
| xgb_d3_r150 | condicionado | 817 | 347 | 346 | -1 (-25 a 23) | -0.2 | 11.51 → 11.54 | 2+ / 4− |
| xgb_d3_r150 | 5 % | 328 | 179 | 172 | -7 (-30 a 14) | -1.1 | 3.65 → 3.82 |  |
| xgb_d3_r150 | 10 % | 656 | 297 | 293 | -4 (-26 a 18) | -0.6 | 8.79 → 8.89 |  |
| xgb_d3_r150 | 20 % | 1230 | 426 | 445 | +19 (-6 a 44) | +3.0 | 19.70 → 19.23 |  |
| xgb_d6 | condicionado | 817 | 347 | 322 | -25 (-52 a -2) | -3.9 | 11.51 → 12.13 | 1+ / 6− |
| xgb_d6 | 5 % | 328 | 179 | 154 | -25 (-49 a -1) | -3.9 | 3.65 → 4.26 |  |
| xgb_d6 | 10 % | 656 | 297 | 271 | -26 (-51 a -2) | -4.1 | 8.79 → 9.43 |  |
| xgb_d6 | 20 % | 1230 | 426 | 427 | +1 (-27 a 29) | +0.2 | 19.70 → 19.67 |  |
| xgb_eta002_r600 | condicionado | 817 | 347 | 337 | -10 (-30 a 9) | -1.6 | 11.51 → 11.76 | 1+ / 6− |
| xgb_eta002_r600 | 5 % | 328 | 179 | 163 | -16 (-37 a 5) | -2.5 | 3.65 → 4.04 |  |
| xgb_eta002_r600 | 10 % | 656 | 297 | 281 | -16 (-35 a 4) | -2.5 | 8.79 → 9.19 |  |
| xgb_eta002_r600 | 20 % | 1230 | 426 | 438 | +12 (-12 a 37) | +1.9 | 19.70 → 19.40 |  |
| xgb_eta01 | condicionado | 817 | 347 | 330 | -17 (-43 a 7) | -2.7 | 11.51 → 11.93 | 2+ / 5− |
| xgb_eta01 | 5 % | 328 | 179 | 152 | -27 (-51 a -6) | -4.2 | 3.65 → 4.31 |  |
| xgb_eta01 | 10 % | 656 | 297 | 270 | -27 (-49 a -5) | -4.2 | 8.79 → 9.46 |  |
| xgb_eta01 | 20 % | 1230 | 426 | 416 | -10 (-33 a 14) | -1.6 | 19.70 → 19.94 |  |
| xgb_sinclima | condicionado | 817 | 347 | 343 | -4 (-23 a 14) | -0.6 | 11.51 → 11.61 | 1+ / 5− |
| xgb_sinclima | 5 % | 328 | 179 | 169 | -10 (-31 a 13) | -1.6 | 3.65 → 3.90 |  |
| xgb_sinclima | 10 % | 656 | 297 | 297 | +0 (-18 a 18) | +0.0 | 8.79 → 8.79 |  |
| xgb_sinclima | 20 % | 1230 | 426 | 445 | +19 (-3 a 43) | +3.0 | 19.70 → 19.23 |  |

| T+2, 459 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| xgb_banco_s53 | condicionado | 1158 | 248 | 247 | -1 (-21 a 18) | -0.2 | 22.51 → 22.54 | 2+ / 4− |
| xgb_banco_s53 | 5 % | 324 | 106 | 100 | -6 (-22 a 12) | -1.3 | 5.39 → 5.54 |  |
| xgb_banco_s53 | 10 % | 648 | 190 | 175 | -15 (-35 a 6) | -3.3 | 11.33 → 11.70 |  |
| xgb_banco_s53 | 20 % | 1215 | 276 | 272 | -4 (-26 a 17) | -0.9 | 23.23 → 23.33 |  |
| xgb_d2 | condicionado | 1158 | 248 | 242 | -6 (-25 a 13) | -1.3 | 22.51 → 22.66 | 3+ / 4− |
| xgb_d2 | 5 % | 324 | 106 | 108 | +2 (-14 a 19) | +0.4 | 5.39 → 5.34 |  |
| xgb_d2 | 10 % | 648 | 190 | 188 | -2 (-20 a 17) | -0.4 | 11.33 → 11.38 |  |
| xgb_d2 | 20 % | 1215 | 276 | 269 | -7 (-31 a 15) | -1.5 | 23.23 → 23.40 |  |
| xgb_d3_r150 | condicionado | 1158 | 248 | 244 | -4 (-24 a 16) | -0.9 | 22.51 → 22.61 | 3+ / 3− |
| xgb_d3_r150 | 5 % | 324 | 106 | 107 | +1 (-15 a 18) | +0.2 | 5.39 → 5.37 |  |
| xgb_d3_r150 | 10 % | 648 | 190 | 185 | -5 (-24 a 13) | -1.1 | 11.33 → 11.45 |  |
| xgb_d3_r150 | 20 % | 1215 | 276 | 265 | -11 (-35 a 10) | -2.4 | 23.23 → 23.50 |  |
| xgb_d6 | condicionado | 1158 | 248 | 242 | -6 (-28 a 15) | -1.3 | 22.51 → 22.66 | 3+ / 3− |
| xgb_d6 | 5 % | 324 | 106 | 101 | -5 (-24 a 16) | -1.1 | 5.39 → 5.52 |  |
| xgb_d6 | 10 % | 648 | 190 | 168 | -22 (-44 a 1) | -4.8 | 11.33 → 11.88 |  |
| xgb_d6 | 20 % | 1215 | 276 | 266 | -10 (-32 a 10) | -2.2 | 23.23 → 23.48 |  |
| xgb_eta002_r600 | condicionado | 1158 | 248 | 243 | -5 (-24 a 13) | -1.1 | 22.51 → 22.64 | 2+ / 3− |
| xgb_eta002_r600 | 5 % | 324 | 106 | 102 | -4 (-21 a 13) | -0.9 | 5.39 → 5.49 |  |
| xgb_eta002_r600 | 10 % | 648 | 190 | 176 | -14 (-32 a 5) | -3.1 | 11.33 → 11.68 |  |
| xgb_eta002_r600 | 20 % | 1215 | 276 | 269 | -7 (-27 a 13) | -1.5 | 23.23 → 23.40 |  |
| xgb_eta01 | condicionado | 1158 | 248 | 237 | -11 (-34 a 11) | -2.4 | 22.51 → 22.79 | 2+ / 5− |
| xgb_eta01 | 5 % | 324 | 106 | 100 | -6 (-26 a 14) | -1.3 | 5.39 → 5.54 |  |
| xgb_eta01 | 10 % | 648 | 190 | 171 | -19 (-42 a 3) | -4.1 | 11.33 → 11.80 |  |
| xgb_eta01 | 20 % | 1215 | 276 | 265 | -11 (-37 a 14) | -2.4 | 23.23 → 23.50 |  |
| xgb_sinclima | condicionado | 1158 | 248 | 245 | -3 (-20 a 13) | -0.7 | 22.51 → 22.59 | 2+ / 4− |
| xgb_sinclima | 5 % | 324 | 106 | 109 | +3 (-16 a 23) | +0.7 | 5.39 → 5.32 |  |
| xgb_sinclima | 10 % | 648 | 190 | 183 | -7 (-27 a 12) | -1.5 | 11.33 → 11.50 |  |
| xgb_sinclima | 20 % | 1215 | 276 | 279 | +3 (-18 a 24) | +0.7 | 23.23 → 23.16 |  |
