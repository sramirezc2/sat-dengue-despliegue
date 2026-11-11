# Tanda 56, línea BL — Otros síndromes febriles

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **cerrada** el 11 de noviembre de 2026. Se corre sobre la base común del
> retroanálisis: `canonical.mode=approved`, calendario y departamentos de
> `parameters_retroanalisis.yml` sin tocar, `conjunto.csv` reportado.

## Origen

La tanda 39 mostró que la logística usa la diferencia entre las notificaciones
totales y las de dengue. Ningún modelo pasa la barra en T+1.

## Hipótesis

Un aumento de síndromes febriles que todavía no se confirman como dengue adelanta
la señal de un brote. Dárselo hecho al modelo (proporción de dengue sobre el total,
notificaciones que no son dengue y su cambio mensual) debería mejorar T+1.

## Qué se corre

`log_conclima_febriles.yml`: la logística con clima más el bloque
`variables_febriles` (`domain/febriles.py`, PR a main). Referencia: la logística con
clima. Se reporta también el veredicto al 10 %.

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

## Resultado: sin efecto

Contra la logística con clima (tabla compartida con la tanda 57):

| T+1, 641 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| log_conclima_febriles | condicionado | 817 | 359 | 358 | -1 (-4 a 2) | -0.2 | 11.22 → 11.24 | 1+ / 2− |
| log_conclima_febriles | 5 % | 328 | 180 | 178 | -2 (-6 a 1) | -0.3 | 3.63 → 3.67 |  |
| log_conclima_febriles | 10 % | 656 | 308 | 309 | +1 (-2 a 4) | +0.2 | 8.53 → 8.50 |  |
| log_conclima_febriles | 20 % | 1230 | 441 | 441 | +0 (-6 a 5) | +0.0 | 19.33 → 19.33 |  |
| log_conclima_vecinos | condicionado | 817 | 359 | 354 | -5 (-18 a 7) | -0.8 | 11.22 → 11.34 | 3+ / 4− |
| log_conclima_vecinos | 5 % | 328 | 180 | 178 | -2 (-16 a 12) | -0.3 | 3.63 → 3.67 |  |
| log_conclima_vecinos | 10 % | 656 | 308 | 299 | -9 (-24 a 6) | -1.4 | 8.53 → 8.75 |  |
| log_conclima_vecinos | 20 % | 1230 | 441 | 432 | -9 (-23 a 3) | -1.4 | 19.33 → 19.55 |  |

| T+2, 459 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| log_conclima_febriles | condicionado | 1158 | 253 | 252 | -1 (-7 a 5) | -0.2 | 22.39 → 22.41 | 3+ / 3− |
| log_conclima_febriles | 5 % | 324 | 103 | 101 | -2 (-6 a 2) | -0.4 | 5.47 → 5.52 |  |
| log_conclima_febriles | 10 % | 648 | 192 | 189 | -3 (-9 a 3) | -0.7 | 11.28 → 11.36 |  |
| log_conclima_febriles | 20 % | 1215 | 291 | 291 | +0 (-8 a 8) | +0.0 | 22.86 → 22.86 |  |
| log_conclima_vecinos | condicionado | 1158 | 253 | 250 | -3 (-12 a 5) | -0.7 | 22.39 → 22.46 | 2+ / 3− |
| log_conclima_vecinos | 5 % | 324 | 103 | 105 | +2 (-10 a 13) | +0.4 | 5.47 → 5.42 |  |
| log_conclima_vecinos | 10 % | 648 | 192 | 192 | +0 (-9 a 8) | +0.0 | 11.28 → 11.28 |  |
| log_conclima_vecinos | 20 % | 1215 | 291 | 296 | +5 (-6 a 15) | +1.1 | 22.86 → 22.74 |  |

Al 10 % de la sección 0:

| Combinación | T+1 (pp, IC mes) | A T+1 | T+2 (pp, IC mes) | Barra T+2 |
| --- | --- | --- | --- | --- |
| log_conclima | +3.1 (0.3 a 5.9) | CUMPLE | +7.2 (3.1 a 11.3) | CUMPLE |
| log_conclima_febriles | +3.0 (0.3 a 5.8) | CUMPLE | +6.5 (2.6 a 10.5) | CUMPLE |
| log_conclima_vecinos | +2.7 (-0.2 a 5.5) | NO | +6.1 (2.2 a 10.0) | CUMPLE |

El bloque de febriles queda en −1 en los dos horizontes. La logística ya arma esa
diferencia por su cuenta con los conteos que tiene; dársela hecha no agrega nada.

Corrida del 11 de noviembre sobre la rama del PR #9 (`a3280a9`). Mismas filas que siempre (7 612 y 7 572 comunes, 76 municipios); la referencia sin los bloques da predicciones idénticas a las de la tanda 15 (diferencia máxima 0).
