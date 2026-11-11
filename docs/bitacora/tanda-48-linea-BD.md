# Tanda 48, línea BD — El clima de los meses anteriores

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **cerrada** el 11 de noviembre de 2026. Se corre sobre la base común del
> retroanálisis: `canonical.mode=approved`, calendario y departamentos de
> `parameters_retroanalisis.yml` sin tocar, `conjunto.csv` reportado.

## Origen

Se escribe después de ver las tandas 15, 22, 32 y 39: el clima del mes de origen
aporta poco y de forma consistente, sobre todo el punto de rocío. El panel no trae
rezagos del clima.

## Hipótesis

El mosquito tarda en responder al clima: la lluvia y la humedad de uno o dos meses
antes crean criaderos y aumentan la población del vector antes de que suban los
casos. Si es así, el clima rezagado debería aportar más que el del mes de origen,
sobre todo en T+1, donde ningún modelo llega a la barra.

## Qué se corre

Seis columnas derivadas (`clima_rezagos: true`): punto de rocío, lluvia y
temperatura de uno y dos meses antes del origen, calculadas por municipio sobre la
historia completa; todas conocidas en el mes de origen, sin fuga. Sobre la
logística sin clima, la logística con clima y la mínima con clima. Referencias: las
mismas recetas sin los rezagos. Requiere la opción, que va al PR #6.

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

## Resultado: el clima rezagado trae lo mismo que el del mes de origen

Mismas filas que la referencia en todas las recetas.

| T+1, 641 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| log_rezagos | condicionado | 817 | 347 | 361 | +14 (-5 a 36) | +2.2 | 11.51 → 11.17 | 6+ / 1− |
| log_rezagos | 5 % | 328 | 179 | 175 | -4 (-19 a 10) | -0.6 | 3.65 → 3.75 |  |
| log_rezagos | 10 % | 656 | 297 | 307 | +10 (-6 a 27) | +1.6 | 8.79 → 8.55 |  |
| log_rezagos | 20 % | 1230 | 426 | 440 | +14 (-4 a 32) | +2.2 | 19.70 → 19.35 |  |

| T+2, 459 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| log_rezagos | condicionado | 1158 | 248 | 253 | +5 (-12 a 22) | +1.1 | 22.51 → 22.39 | 3+ / 1− |
| log_rezagos | 5 % | 324 | 106 | 104 | -2 (-17 a 14) | -0.4 | 5.39 → 5.44 |  |
| log_rezagos | 10 % | 648 | 190 | 191 | +1 (-11 a 15) | +0.2 | 11.33 → 11.31 |  |
| log_rezagos | 20 % | 1215 | 276 | 289 | +13 (-5 a 30) | +2.8 | 23.23 → 22.91 |  |

| T+1, 641 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| logc_rezagos | condicionado | 817 | 359 | 362 | +3 (-6 a 12) | +0.5 | 11.22 → 11.15 | 4+ / 2− |
| logc_rezagos | 5 % | 328 | 180 | 178 | -2 (-11 a 8) | -0.3 | 3.63 → 3.67 |  |
| logc_rezagos | 10 % | 656 | 308 | 308 | +0 (-10 a 9) | +0.0 | 8.53 → 8.53 |  |
| logc_rezagos | 20 % | 1230 | 441 | 441 | +0 (-11 a 11) | +0.0 | 19.33 → 19.33 |  |
| logc_rocio_meta | condicionado | 817 | 359 | 355 | -4 (-14 a 7) | -0.6 | 11.22 → 11.32 | 2+ / 4− |
| logc_rocio_meta | 5 % | 328 | 180 | 179 | -1 (-9 a 7) | -0.2 | 3.63 → 3.65 |  |
| logc_rocio_meta | 10 % | 656 | 308 | 306 | -2 (-13 a 8) | -0.3 | 8.53 → 8.57 |  |
| logc_rocio_meta | 20 % | 1230 | 441 | 432 | -9 (-20 a 2) | -1.4 | 19.33 → 19.55 |  |

| T+2, 459 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| logc_rezagos | condicionado | 1158 | 253 | 249 | -4 (-13 a 4) | -0.9 | 22.39 → 22.49 | 2+ / 4− |
| logc_rezagos | 5 % | 324 | 103 | 107 | +4 (-6 a 14) | +0.9 | 5.47 → 5.37 |  |
| logc_rezagos | 10 % | 648 | 192 | 189 | -3 (-12 a 5) | -0.7 | 11.28 → 11.36 |  |
| logc_rezagos | 20 % | 1215 | 291 | 290 | -1 (-10 a 8) | -0.2 | 22.86 → 22.88 |  |
| logc_rocio_meta | condicionado | 1158 | 253 | 252 | -1 (-6 a 4) | -0.2 | 22.39 → 22.41 | 1+ / 2− |
| logc_rocio_meta | 5 % | 324 | 103 | 104 | +1 (-2 a 4) | +0.2 | 5.47 → 5.44 |  |
| logc_rocio_meta | 10 % | 648 | 192 | 193 | +1 (-7 a 8) | +0.2 | 11.28 → 11.26 |  |
| logc_rocio_meta | 20 % | 1215 | 291 | 288 | -3 (-12 a 6) | -0.7 | 22.86 → 22.93 |  |

| T+1, 641 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| logc_minima_rezagos | condicionado | 817 | 354 | 355 | +1 (-8 a 10) | +0.2 | 11.34 → 11.32 | 3+ / 3− |
| logc_minima_rezagos | 5 % | 328 | 178 | 181 | +3 (-6 a 12) | +0.5 | 3.67 → 3.60 |  |
| logc_minima_rezagos | 10 % | 656 | 301 | 303 | +2 (-7 a 11) | +0.3 | 8.70 → 8.65 |  |
| logc_minima_rezagos | 20 % | 1230 | 444 | 451 | +7 (-2 a 16) | +1.1 | 19.26 → 19.08 |  |
| logc_minima_rocio_meta | condicionado | 817 | 354 | 352 | -2 (-14 a 9) | -0.3 | 11.34 → 11.39 | 2+ / 3− |
| logc_minima_rocio_meta | 5 % | 328 | 178 | 179 | +1 (-8 a 11) | +0.2 | 3.67 → 3.65 |  |
| logc_minima_rocio_meta | 10 % | 656 | 301 | 300 | -1 (-11 a 10) | -0.2 | 8.70 → 8.72 |  |
| logc_minima_rocio_meta | 20 % | 1230 | 444 | 444 | +0 (-12 a 10) | +0.0 | 19.26 → 19.26 |  |

| T+2, 459 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| logc_minima_rezagos | condicionado | 1158 | 247 | 250 | +3 (-5 a 11) | +0.7 | 22.54 → 22.46 | 3+ / 3− |
| logc_minima_rezagos | 5 % | 324 | 105 | 107 | +2 (-6 a 10) | +0.4 | 5.42 → 5.37 |  |
| logc_minima_rezagos | 10 % | 648 | 184 | 186 | +2 (-8 a 12) | +0.4 | 11.48 → 11.43 |  |
| logc_minima_rezagos | 20 % | 1215 | 288 | 283 | -5 (-16 a 6) | -1.1 | 22.93 → 23.06 |  |
| logc_minima_rocio_meta | condicionado | 1158 | 247 | 246 | -1 (-8 a 6) | -0.2 | 22.54 → 22.56 | 2+ / 1− |
| logc_minima_rocio_meta | 5 % | 324 | 105 | 106 | +1 (-3 a 5) | +0.2 | 5.42 → 5.39 |  |
| logc_minima_rocio_meta | 10 % | 648 | 184 | 184 | +0 (-7 a 7) | +0.0 | 11.48 → 11.48 |  |
| logc_minima_rocio_meta | 20 % | 1215 | 288 | 285 | -3 (-12 a 6) | -0.7 | 22.93 → 23.01 |  |

- **Sobre la logística sin clima, los rezagos suman +14 en T+1** (IC −5 a 36, seis
  años a favor y uno en contra) y +5 en T+2: casi lo mismo que el clima del mes de
  origen en la tanda 15 (+12 y +5). Sin llegar a la barra.
- **Sobre la logística con clima, no agregan nada** (+3 y −4), ni sobre la mínima con
  clima (+1 y +3).
- Lectura: el clima de uno y dos meses antes y el del mes de origen llevan la misma
  información para el modelo; el efecto del clima no está en el rezago.
