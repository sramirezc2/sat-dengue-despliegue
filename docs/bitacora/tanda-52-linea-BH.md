# Tanda 52, línea BH — El clima sobre las variantes de la mínima

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **cerrada** el 11 de noviembre de 2026. Se corre sobre la base común del
> retroanálisis: `canonical.mode=approved`, calendario y departamentos de
> `parameters_retroanalisis.yml` sin tocar, `conjunto.csv` reportado.

## Origen

Se escribe después de las tandas 17 y 22 y se declara así: el clima sumó +15 en T+1
sobre la mínima (tanda 22), y la mínima con rezago 2 y la mínima con P25 quedaron
dentro de 5 puntos de la completa (tanda 17), pero nunca se probaron con clima.

## Hipótesis

Si una de esas variantes con clima rinde igual o mejor que la mínima con clima, el
modelo explicable puede ganar una variable útil sin perder la señal del clima.

## Qué se corre

La mínima + rezago 2 y la mínima + P25, cada una con las nueve variables de clima.
Referencias: la mínima con clima (tanda 22) y, como segunda lectura, la misma
variante sin clima (tanda 17).

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

## Resultado: el clima suma en las dos variantes, pero no supera a la mínima con clima

Contra la mínima con clima (tanda 22):

| T+1, 641 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| logc_minima_lag2 | condicionado | 817 | 354 | 355 | +1 (-12 a 14) | +0.2 | 11.34 → 11.32 | 4+ / 2− |
| logc_minima_lag2 | 5 % | 328 | 178 | 183 | +5 (-8 a 19) | +0.8 | 3.67 → 3.55 |  |
| logc_minima_lag2 | 10 % | 656 | 301 | 306 | +5 (-7 a 17) | +0.8 | 8.70 → 8.57 |  |
| logc_minima_lag2 | 20 % | 1230 | 444 | 437 | -7 (-18 a 3) | -1.1 | 19.26 → 19.43 |  |
| logc_minima_p25 | condicionado | 817 | 354 | 353 | -1 (-9 a 7) | -0.2 | 11.34 → 11.37 | 2+ / 3− |
| logc_minima_p25 | 5 % | 328 | 178 | 183 | +5 (-3 a 14) | +0.8 | 3.67 → 3.55 |  |
| logc_minima_p25 | 10 % | 656 | 301 | 307 | +6 (-4 a 16) | +0.9 | 8.70 → 8.55 |  |
| logc_minima_p25 | 20 % | 1230 | 444 | 444 | +0 (-8 a 8) | +0.0 | 19.26 → 19.26 |  |

| T+2, 459 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| logc_minima_lag2 | condicionado | 1158 | 247 | 253 | +6 (-5 a 17) | +1.3 | 22.54 → 22.39 | 5+ / 2− |
| logc_minima_lag2 | 5 % | 324 | 105 | 103 | -2 (-12 a 7) | -0.4 | 5.42 → 5.47 |  |
| logc_minima_lag2 | 10 % | 648 | 184 | 195 | +11 (-0 a 23) | +2.4 | 11.48 → 11.21 |  |
| logc_minima_lag2 | 20 % | 1215 | 288 | 289 | +1 (-9 a 11) | +0.2 | 22.93 → 22.91 |  |
| logc_minima_p25 | condicionado | 1158 | 247 | 249 | +2 (-2 a 6) | +0.4 | 22.54 → 22.49 | 2+ / 0− |
| logc_minima_p25 | 5 % | 324 | 105 | 103 | -2 (-8 a 3) | -0.4 | 5.42 → 5.47 |  |
| logc_minima_p25 | 10 % | 648 | 184 | 185 | +1 (-5 a 8) | +0.2 | 11.48 → 11.45 |  |
| logc_minima_p25 | 20 % | 1215 | 288 | 282 | -6 (-13 a 0) | -1.3 | 22.93 → 23.08 |  |

Contra la misma variante sin clima:

| T+1, 641 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| logc_minima_lag2 | condicionado | 817 | 338 | 355 | +17 (-2 a 36) | +2.7 | 11.73 → 11.32 | 5+ / 0− |
| logc_minima_lag2 | 5 % | 328 | 179 | 183 | +4 (-12 a 22) | +0.6 | 3.65 → 3.55 |  |
| logc_minima_lag2 | 10 % | 656 | 288 | 306 | +18 (-1 a 38) | +2.8 | 9.02 → 8.57 |  |
| logc_minima_lag2 | 20 % | 1230 | 421 | 437 | +16 (-6 a 39) | +2.5 | 19.82 → 19.43 |  |

| T+2, 459 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| logc_minima_lag2 | condicionado | 1158 | 246 | 253 | +7 (-5 a 19) | +1.5 | 22.56 → 22.39 | 4+ / 3− |
| logc_minima_lag2 | 5 % | 324 | 105 | 103 | -2 (-16 a 11) | -0.4 | 5.42 → 5.47 |  |
| logc_minima_lag2 | 10 % | 648 | 194 | 195 | +1 (-12 a 14) | +0.2 | 11.23 → 11.21 |  |
| logc_minima_lag2 | 20 % | 1215 | 274 | 289 | +15 (1 a 29) | +3.3 | 23.28 → 22.91 |  |

| T+1, 641 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| logc_minima_p25 | condicionado | 817 | 342 | 353 | +11 (-9 a 32) | +1.7 | 11.64 → 11.37 | 4+ / 1− |
| logc_minima_p25 | 5 % | 328 | 185 | 183 | -2 (-19 a 15) | -0.3 | 3.50 → 3.55 |  |
| logc_minima_p25 | 10 % | 656 | 292 | 307 | +15 (-4 a 36) | +2.3 | 8.92 → 8.55 |  |
| logc_minima_p25 | 20 % | 1230 | 427 | 444 | +17 (-4 a 38) | +2.7 | 19.67 → 19.26 |  |

| T+2, 459 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| logc_minima_p25 | condicionado | 1158 | 244 | 249 | +5 (-9 a 19) | +1.1 | 22.61 → 22.49 | 5+ / 2− |
| logc_minima_p25 | 5 % | 324 | 105 | 103 | -2 (-13 a 8) | -0.4 | 5.42 → 5.47 |  |
| logc_minima_p25 | 10 % | 648 | 190 | 185 | -5 (-20 a 10) | -1.1 | 11.33 → 11.45 |  |
| logc_minima_p25 | 20 % | 1215 | 277 | 282 | +5 (-11 a 19) | +1.1 | 23.21 → 23.08 |  |

- Sobre cada variante, **el clima vuelve a sumar en T+1**: +17 sobre la mínima con
  rezago 2 (cinco años a favor y ninguno en contra) y +11 sobre la mínima con P25.
  Es la cuarta vez que se ve (tandas 15, 22, 48 y esta).
- Pero ninguna variante con clima supera a la mínima con clima: quedan a +1 y −1 en
  T+1 y a +6 y +2 en T+2. **Sin efecto** frente a la referencia principal.

Al 10 % de la sección 0:

| Combinación | T+1 (pp, IC mes) | T+2 (pp, IC mes) | Barra T+2 |
| --- | --- | --- | --- |
| logc_minima_lag2 | +3.3 (0.6 a 5.8) | +7.4 (3.3 a 11.3) | CUMPLE |
| logc_minima_p25 | +3.1 (0.8 a 5.6) | +7.4 (3.5 a 11.5) | CUMPLE |

Las dos pasan la barra en T+2 (+7,4 pp), igual que la mínima con clima (+7,2), y en
T+1 cumplen A sin llegar a la barra.

Corrida del 11 de noviembre sobre main (`3011db9`), mismo panel y mismas filas (8 124 predicciones por combinación).
