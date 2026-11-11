# Tanda 26, línea AH — Un modelo por departamento, con y sin clima

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **cerrada** el 10 de noviembre de 2026. Se corre sobre la base común del
> retroanálisis: `canonical.mode=approved`, calendario y departamentos de
> `parameters_retroanalisis.yml` sin tocar, `conjunto.csv` reportado.

## Origen

Se escribe después de ver la tanda 25 y se declara así: con un solo modelo, el
clima gana en Meta y no en Tolima. Un modelo por departamento ya se había
descartado en la tanda 10 con otro instrumento.

## Hipótesis

Si el clima importa distinto en cada departamento, un modelo propio por
departamento podría darle a cada uno el peso que necesita, sobre todo con clima.

## Qué se corre

La logística sin clima y la logística con clima entrenadas **por separado** en Meta
(29 municipios) y en Tolima (47). Las predicciones de los dos departamentos se
juntan y se evalúan sobre las mismas filas de siempre, con el mismo presupuesto
por mes. Referencias: el modelo único sin clima y el modelo único con clima.

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

## Resultado: un modelo por departamento empeora, y pierde el clima de Meta

Contra el modelo único, sobre las mismas filas (4 082 y 4 042 filas evaluadas de
los dos departamentos juntas):

- **Sin clima**, el modelo por departamento queda en −6 en T+1 (IC −19 a 6) y −8
  en T+2 (cinco años en contra y ninguno a favor).
- **Con clima** es peor: contra el modelo único con clima pierde **−13 en T+1**
  (IC −27 a 0) y **−18 en T+2 (IC −31 a −5)**, en contra en cinco y seis años.
  Veredicto: **empeora**.
- **Por departamento**, con su propio modelo, Meta con clima queda en −4 frente al
  canal en T+1, cuando con el modelo único era +16. Tolima apenas cambia (+27
  frente a +20).

Lo que se aprende: **la señal del clima en Meta sale de entrenar con los dos
departamentos juntos**, no de un modelo propio de Meta. Con 29 municipios el
modelo no tiene ejemplos suficientes para aprender el efecto del clima. Eso hace
más relevante la tanda 18 (entrenar con todo el país), que se corre a
continuación.

| T+1, 641 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dep_sin_clima | condicionado | 817 | 347 | 341 | -6 (-19 a 6) | -0.9 | 11.51 → 11.66 | 2+ / 4− |
| dep_sin_clima | 5 % | 209 | 109 | 108 | -1 (-10 a 9) | -0.2 | 2.45 → 2.47 |  |
| dep_sin_clima | 10 % | 406 | 189 | 187 | -2 (-13 a 10) | -0.3 | 5.32 → 5.37 |  |
| dep_sin_clima | 20 % | 817 | 304 | 290 | -14 (-25 a -3) | -2.2 | 12.57 → 12.91 |  |
| dep_con_clima | condicionado | 817 | 347 | 346 | -1 (-19 a 17) | -0.2 | 11.51 → 11.54 | 3+ / 2− |
| dep_con_clima | 5 % | 209 | 109 | 101 | -8 (-25 a 7) | -1.2 | 2.45 → 2.65 |  |
| dep_con_clima | 10 % | 406 | 189 | 183 | -6 (-22 a 10) | -0.9 | 5.32 → 5.46 |  |
| dep_con_clima | 20 % | 817 | 304 | 306 | +2 (-18 a 23) | +0.3 | 12.57 → 12.52 |  |

| T+2, 459 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dep_sin_clima | condicionado | 1158 | 248 | 240 | -8 (-21 a 5) | -1.7 | 22.51 → 22.71 | 0+ / 5− |
| dep_sin_clima | 5 % | 207 | 67 | 62 | -5 (-14 a 5) | -1.1 | 3.46 → 3.59 |  |
| dep_sin_clima | 10 % | 402 | 123 | 115 | -8 (-20 a 4) | -1.7 | 6.90 → 7.10 |  |
| dep_sin_clima | 20 % | 809 | 204 | 199 | -5 (-17 a 7) | -1.1 | 14.97 → 15.09 |  |
| dep_con_clima | condicionado | 1158 | 248 | 235 | -13 (-28 a 1) | -2.8 | 22.51 → 22.84 | 0+ / 5− |
| dep_con_clima | 5 % | 207 | 67 | 66 | -1 (-16 a 15) | -0.2 | 3.46 → 3.49 |  |
| dep_con_clima | 10 % | 402 | 123 | 116 | -7 (-21 a 7) | -1.5 | 6.90 → 7.08 |  |
| dep_con_clima | 20 % | 809 | 204 | 203 | -1 (-15 a 13) | -0.2 | 14.97 → 14.99 |  |

Contra la logística con clima de un solo modelo:

| T+1, 641 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dep_con_clima | condicionado | 817 | 359 | 346 | -13 (-27 a 0) | -2.0 | 11.22 → 11.54 | 0+ / 5− |
| dep_con_clima | 5 % | 209 | 112 | 101 | -11 (-23 a 0) | -1.7 | 2.38 → 2.65 |  |
| dep_con_clima | 10 % | 406 | 194 | 183 | -11 (-25 a 2) | -1.7 | 5.19 → 5.46 |  |
| dep_con_clima | 20 % | 817 | 317 | 306 | -11 (-28 a 6) | -1.7 | 12.25 → 12.52 |  |

| T+2, 459 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dep_con_clima | condicionado | 1158 | 253 | 235 | -18 (-31 a -5) | -3.9 | 22.39 → 22.84 | 0+ / 6− |
| dep_con_clima | 5 % | 207 | 65 | 66 | +1 (-10 a 13) | +0.2 | 3.51 → 3.49 |  |
| dep_con_clima | 10 % | 402 | 127 | 116 | -11 (-23 a 2) | -2.4 | 6.80 → 7.08 |  |
| dep_con_clima | 20 % | 809 | 211 | 203 | -8 (-21 a 4) | -1.7 | 14.79 → 14.99 |  |
