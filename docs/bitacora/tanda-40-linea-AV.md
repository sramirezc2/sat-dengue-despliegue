# Tanda 40, línea AV — El punto de rocío como único clima

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **cerrada** el 11 de noviembre de 2026. Se corre sobre la base común del
> retroanálisis: `canonical.mode=approved`, calendario y departamentos de
> `parameters_retroanalisis.yml` sin tocar, `conjunto.csv` reportado.

## Origen

Se escribe después de ver la tanda 39 y se declara así: el punto de rocío es la
variable de clima con mayor coeficiente. Elegir una variable por su coeficiente y
luego medirla sobre los mismos años es selección después de mirar; por eso esta
tanda **no puede declarar mejora sobre el clima completo**, solo si la versión de
una variable es equivalente.

## Hipótesis

Si casi todo el aporte del clima pasa por la humedad, una logística con solo el
punto de rocío rinde igual que con las nueve variables, y es más fácil de explicar
y de mantener.

## Qué se corre

La logística con clima y la mínima con clima, cada una con el punto de rocío como
única variable de clima. Referencias: las mismas recetas con las nueve variables.

## Qué métrica decide

Inicios detectados al presupuesto de alertas de cada línea base (canal P75,
condicionado y ajustado), sobre la base común y las mismas filas, igual que las
tandas 11 y 12. El brazo de referencia es `logistica_sin_clima.yml` corrido **en
la misma corrida**. Se publican también el resumen por año y la curva.

## Qué contaría como mejora, declarado antes de mirar

Al presupuesto del canal condicionado, por horizonte:

- **Equivalente** si queda dentro de ±5 puntos de la referencia; no se declara
  mejora aunque la supere, por la selección después de mirar.
- (Criterio general, que aquí no se aplica para mejora:) **Mejora** si el brazo suma al menos 5 puntos de inicios sobre la referencia
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

## Resultado: equivalente por la regla, pero no conserva todo el clima

Contra la logística con clima:

| T+1, 641 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| logc_rocio | condicionado | 817 | 359 | 352 | -7 (-18 a 4) | -1.1 | 11.22 → 11.39 | 1+ / 4− |
| logc_rocio | 5 % | 328 | 180 | 174 | -6 (-19 a 5) | -0.9 | 3.63 → 3.77 |  |
| logc_rocio | 10 % | 656 | 308 | 300 | -8 (-22 a 5) | -1.2 | 8.53 → 8.72 |  |
| logc_rocio | 20 % | 1230 | 441 | 433 | -8 (-23 a 7) | -1.2 | 19.33 → 19.52 |  |

| T+2, 459 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| logc_rocio | condicionado | 1158 | 253 | 250 | -3 (-13 a 8) | -0.7 | 22.39 → 22.46 | 3+ / 3− |
| logc_rocio | 5 % | 324 | 103 | 111 | +8 (-5 a 21) | +1.7 | 5.47 → 5.27 |  |
| logc_rocio | 10 % | 648 | 192 | 189 | -3 (-11 a 5) | -0.7 | 11.28 → 11.36 |  |
| logc_rocio | 20 % | 1215 | 291 | 287 | -4 (-18 a 10) | -0.9 | 22.86 → 22.96 |  |

Contra la mínima con clima:

| T+1, 641 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| logc_minima_rocio | condicionado | 817 | 354 | 349 | -5 (-21 a 12) | -0.8 | 11.34 → 11.46 | 3+ / 4− |
| logc_minima_rocio | 5 % | 328 | 178 | 182 | +4 (-9 a 18) | +0.6 | 3.67 → 3.58 |  |
| logc_minima_rocio | 10 % | 656 | 301 | 294 | -7 (-23 a 9) | -1.1 | 8.70 → 8.87 |  |
| logc_minima_rocio | 20 % | 1230 | 444 | 430 | -14 (-30 a 2) | -2.2 | 19.26 → 19.60 |  |

| T+2, 459 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| logc_minima_rocio | condicionado | 1158 | 247 | 249 | +2 (-10 a 13) | +0.4 | 22.54 → 22.49 | 4+ / 2− |
| logc_minima_rocio | 5 % | 324 | 105 | 109 | +4 (-8 a 14) | +0.9 | 5.42 → 5.32 |  |
| logc_minima_rocio | 10 % | 648 | 184 | 194 | +10 (-2 a 23) | +2.2 | 11.48 → 11.23 |  |
| logc_minima_rocio | 20 % | 1215 | 288 | 277 | -11 (-23 a 2) | -2.4 | 22.93 → 23.21 |  |

- Por el criterio preinscrito, las dos versiones con solo punto de rocío son
  **equivalentes** a las de clima completo: quedan dentro de ±5 puntos (−7 y −5
  inicios en T+1, −3 y +2 en T+2).
- Pero en T+1, que es donde el clima aporta, **la logística con solo punto de rocío
  pierde 7 de los 12 inicios** que el clima completo sumaba (tanda 15), con cuatro
  años en contra. El punto de rocío es la variable de clima que más pesa (tanda
  39), pero el resto del clima también aporta algo. Se mantiene el clima completo.
