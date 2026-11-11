# Tanda 27, línea AI — Un solo modelo con indicador de departamento

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **cerrada** el 11 de noviembre de 2026. Se corre sobre la base común del
> retroanálisis: `canonical.mode=approved`, calendario y departamentos de
> `parameters_retroanalisis.yml` sin tocar, `conjunto.csv` reportado.

## Origen

Se escribe después de ver las tandas 25 y 26 y se declara así: el clima gana en
Meta con un modelo único y pierde esa ganancia con un modelo por departamento.

## Hipótesis

Un modelo único con un indicador de Tolima conserva lo que se aprende juntando
los dos departamentos y deja que cada uno tenga su propio nivel base de riesgo.
Si la diferencia entre departamentos es solo de nivel, el indicador debería
ayudar; si no ayuda, la diferencia está en otra parte.

## Qué se corre

Una columna derivada `depto_73` (1 en Tolima, 0 en Meta), al final de la matriz
(`variable_depto: true`), sobre la logística sin clima y sobre la logística con
clima. Referencias: las mismas recetas sin el indicador. Requiere la opción, por
PR a main.

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

Mismas filas (4 082 y 4 042 evaluadas). El indicador de Tolima no mueve nada: sin
clima +1 y −2, con clima −2 y 0, siempre dentro de ±4 inicios. La diferencia entre
departamentos no es de nivel base: el modelo único ya la absorbe con el umbral del
canal de cada municipio.

| T+1, 641 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| log_depto | condicionado | 817 | 347 | 348 | +1 (-2 a 5) | +0.2 | 11.51 → 11.49 | 1+ / 0− |
| log_depto | 5 % | 328 | 179 | 179 | +0 (-4 a 4) | +0.0 | 3.65 → 3.65 |  |
| log_depto | 10 % | 656 | 297 | 298 | +1 (0 a 3) | +0.2 | 8.79 → 8.77 |  |
| log_depto | 20 % | 1230 | 426 | 425 | -1 (-7 a 5) | -0.2 | 19.70 → 19.72 |  |

| T+2, 459 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| log_depto | condicionado | 1158 | 248 | 246 | -2 (-9 a 3) | -0.4 | 22.51 → 22.56 | 2+ / 2− |
| log_depto | 5 % | 324 | 106 | 100 | -6 (-12 a 0) | -1.3 | 5.39 → 5.54 |  |
| log_depto | 10 % | 648 | 190 | 189 | -1 (-4 a 2) | -0.2 | 11.33 → 11.36 |  |
| log_depto | 20 % | 1215 | 276 | 277 | +1 (-6 a 8) | +0.2 | 23.23 → 23.21 |  |

Con clima:

| T+1, 641 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| logc_depto | condicionado | 817 | 359 | 357 | -2 (-11 a 7) | -0.3 | 11.22 → 11.27 | 2+ / 4− |
| logc_depto | 5 % | 328 | 180 | 178 | -2 (-10 a 6) | -0.3 | 3.63 → 3.67 |  |
| logc_depto | 10 % | 656 | 308 | 304 | -4 (-12 a 4) | -0.6 | 8.53 → 8.62 |  |
| logc_depto | 20 % | 1230 | 441 | 434 | -7 (-17 a 3) | -1.1 | 19.33 → 19.50 |  |

| T+2, 459 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| logc_depto | condicionado | 1158 | 253 | 253 | +0 (-5 a 4) | +0.0 | 22.39 → 22.39 | 1+ / 1− |
| logc_depto | 5 % | 324 | 103 | 105 | +2 (-2 a 6) | +0.4 | 5.47 → 5.42 |  |
| logc_depto | 10 % | 648 | 192 | 192 | +0 (-8 a 8) | +0.0 | 11.28 → 11.28 |  |
| logc_depto | 20 % | 1215 | 291 | 291 | +0 (-8 a 8) | +0.0 | 22.86 → 22.86 |  |
