# Tanda 16, línea X — Regularización y escala de la logística

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **cerrada** el 10 de noviembre de 2026. Se corre sobre la base común del
> retroanálisis: `canonical.mode=approved`, calendario y departamentos de
> `parameters_retroanalisis.yml` sin tocar, `conjunto.csv` reportado.

## Hipótesis

Dos preguntas sobre el mismo modelo. Primera: la regularización por defecto
(C = 1) no se eligió; si el resultado depende mucho de C, la logística está mal
afinada. Segunda: la tanda 11 midió que la escala log1p arma el margen G por
dentro del modelo. Si es así, quitar log1p debería empeorar la logística, y
agregar el bloque G sin log1p debería recuperar lo perdido.

## Qué se corre

- C = 0,01, 0,1, 10 y 100 (`log_C*.yml`).
- Sin log1p (`log_sin_log1p.yml`).
- Sin log1p y con el bloque G (`log_sin_log1p_g.yml`).

Para C, la mejora tiene que aparecer en un valor y no ser un pico aislado: se
reporta toda la grilla.

**Predicción del mecanismo, declarada antes:** sin log1p pierde inicios, y con G
los recupera en buena parte. Si sin log1p no pierde nada, el mecanismo de la
tanda 11 no explica por qué G no aporta.

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

## Resultado: Se confirma el mecanismo de la tanda 11

- **C**: de 1 en adelante no cambia nada (C = 10 y 100 quedan a ±4 inicios).
  Solo una regularización fuerte, C = 0,01, **empeora** (−26 en T+1, IC −45 a −8;
  −24 en T+2, IC −41 a −6). C = 1 no estaba mal elegido.
- **Sin log1p la logística empeora** de forma clara: −43 en T+1 (IC −66 a −20,
  siete de siete años en contra) y −27 en T+2 (IC −45 a −9).
- **Con el bloque G, sin log1p, recupera la mayor parte**: −11 en T+1 y −16 en
  T+2, ambos con IC que cruza el cero.

Es exactamente la predicción declarada: la escala log1p arma el margen por dentro
de la logística, y por eso G no le aporta nada a la logística con log1p. G es la
forma explícita de lo que log1p ya hace.

| T+1, 641 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| log_C0p01 | condicionado | 817 | 347 | 321 | -26 (-45 a -8) | -4.1 | 11.51 → 12.15 | 1+ / 6− |
| log_C0p01 | 5 % | 209 | 109 | 100 | -9 (-24 a 6) | -1.4 | 2.45 → 2.67 |  |
| log_C0p01 | 10 % | 406 | 189 | 174 | -15 (-32 a 0) | -2.3 | 5.32 → 5.68 |  |
| log_C0p01 | 20 % | 817 | 304 | 288 | -16 (-33 a 2) | -2.5 | 12.57 → 12.96 |  |
| log_C0p1 | condicionado | 817 | 347 | 345 | -2 (-12 a 8) | -0.3 | 11.51 → 11.56 | 1+ / 3− |
| log_C0p1 | 5 % | 209 | 109 | 111 | +2 (-4 a 7) | +0.3 | 2.45 → 2.40 |  |
| log_C0p1 | 10 % | 406 | 189 | 195 | +6 (-4 a 16) | +0.9 | 5.32 → 5.17 |  |
| log_C0p1 | 20 % | 817 | 304 | 302 | -2 (-11 a 7) | -0.3 | 12.57 → 12.62 |  |
| log_C10 | condicionado | 817 | 347 | 347 | +0 (-4 a 4) | +0.0 | 11.51 → 11.51 | 1+ / 1− |
| log_C10 | 5 % | 209 | 109 | 110 | +1 (-4 a 6) | +0.2 | 2.45 → 2.43 |  |
| log_C10 | 10 % | 406 | 189 | 188 | -1 (-6 a 4) | -0.2 | 5.32 → 5.34 |  |
| log_C10 | 20 % | 817 | 304 | 302 | -2 (-8 a 3) | -0.3 | 12.57 → 12.62 |  |
| log_C100 | condicionado | 817 | 347 | 348 | +1 (-3 a 6) | +0.2 | 11.51 → 11.49 | 2+ / 1− |
| log_C100 | 5 % | 209 | 109 | 110 | +1 (-4 a 6) | +0.2 | 2.45 → 2.43 |  |
| log_C100 | 10 % | 406 | 189 | 189 | +0 (-5 a 5) | +0.0 | 5.32 → 5.32 |  |
| log_C100 | 20 % | 817 | 304 | 303 | -1 (-8 a 5) | -0.2 | 12.57 → 12.59 |  |
| log_sin_log1p | condicionado | 817 | 347 | 304 | -43 (-66 a -20) | -6.7 | 11.51 → 12.57 | 0+ / 7− |
| log_sin_log1p | 5 % | 209 | 109 | 92 | -17 (-38 a 3) | -2.7 | 2.45 → 2.87 |  |
| log_sin_log1p | 10 % | 406 | 189 | 166 | -23 (-46 a 1) | -3.6 | 5.32 → 5.88 |  |
| log_sin_log1p | 20 % | 817 | 304 | 277 | -27 (-48 a -5) | -4.2 | 12.57 → 13.23 |  |
| log_sin_log1p_g | condicionado | 817 | 347 | 336 | -11 (-29 a 6) | -1.7 | 11.51 → 11.78 | 2+ / 5− |
| log_sin_log1p_g | 5 % | 209 | 109 | 108 | -1 (-15 a 13) | -0.2 | 2.45 → 2.47 |  |
| log_sin_log1p_g | 10 % | 406 | 189 | 192 | +3 (-14 a 19) | +0.5 | 5.32 → 5.24 |  |
| log_sin_log1p_g | 20 % | 817 | 304 | 304 | +0 (-18 a 18) | +0.0 | 12.57 → 12.57 |  |

| T+2, 459 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| log_C0p01 | condicionado | 1158 | 248 | 224 | -24 (-41 a -6) | -5.2 | 22.51 → 23.11 | 1+ / 6− |
| log_C0p01 | 5 % | 207 | 67 | 58 | -9 (-23 a 4) | -2.0 | 3.46 → 3.69 |  |
| log_C0p01 | 10 % | 402 | 123 | 104 | -19 (-36 a -2) | -4.1 | 6.90 → 7.37 |  |
| log_C0p01 | 20 % | 809 | 204 | 179 | -25 (-42 a -9) | -5.4 | 14.97 → 15.59 |  |
| log_C0p1 | condicionado | 1158 | 248 | 244 | -4 (-10 a 1) | -0.9 | 22.51 → 22.61 | 1+ / 4− |
| log_C0p1 | 5 % | 207 | 67 | 63 | -4 (-10 a 2) | -0.9 | 3.46 → 3.56 |  |
| log_C0p1 | 10 % | 402 | 123 | 127 | +4 (-4 a 12) | +0.9 | 6.90 → 6.80 |  |
| log_C0p1 | 20 % | 809 | 204 | 202 | -2 (-15 a 9) | -0.4 | 14.97 → 15.02 |  |
| log_C10 | condicionado | 1158 | 248 | 251 | +3 (-2 a 8) | +0.7 | 22.51 → 22.44 | 3+ / 1− |
| log_C10 | 5 % | 207 | 67 | 66 | -1 (-5 a 3) | -0.2 | 3.46 → 3.49 |  |
| log_C10 | 10 % | 402 | 123 | 122 | -1 (-5 a 2) | -0.2 | 6.90 → 6.93 |  |
| log_C10 | 20 % | 809 | 204 | 205 | +1 (-5 a 7) | +0.2 | 14.97 → 14.94 |  |
| log_C100 | condicionado | 1158 | 248 | 252 | +4 (0 a 9) | +0.9 | 22.51 → 22.41 | 3+ / 0− |
| log_C100 | 5 % | 207 | 67 | 66 | -1 (-5 a 3) | -0.2 | 3.46 → 3.49 |  |
| log_C100 | 10 % | 402 | 123 | 120 | -3 (-8 a 3) | -0.7 | 6.90 → 6.98 |  |
| log_C100 | 20 % | 809 | 204 | 206 | +2 (-6 a 9) | +0.4 | 14.97 → 14.92 |  |
| log_sin_log1p | condicionado | 1158 | 248 | 221 | -27 (-45 a -9) | -5.9 | 22.51 → 23.18 | 0+ / 6− |
| log_sin_log1p | 5 % | 207 | 67 | 56 | -11 (-31 a 10) | -2.4 | 3.46 → 3.74 |  |
| log_sin_log1p | 10 % | 402 | 123 | 95 | -28 (-52 a -3) | -6.1 | 6.90 → 7.60 |  |
| log_sin_log1p | 20 % | 809 | 204 | 169 | -35 (-56 a -14) | -7.6 | 14.97 → 15.83 |  |
| log_sin_log1p_g | condicionado | 1158 | 248 | 232 | -16 (-35 a 3) | -3.5 | 22.51 → 22.91 | 1+ / 5− |
| log_sin_log1p_g | 5 % | 207 | 67 | 58 | -9 (-25 a 6) | -2.0 | 3.46 → 3.69 |  |
| log_sin_log1p_g | 10 % | 402 | 123 | 106 | -17 (-33 a 1) | -3.7 | 6.90 → 7.32 |  |
| log_sin_log1p_g | 20 % | 809 | 204 | 180 | -24 (-41 a -7) | -5.2 | 14.97 → 15.56 |  |

Corrida del 10 de noviembre de 2026, sobre el panel certificado `de49b11b…` del
release `satd-raw-173d5856`, con el nodo del retroanálisis de main más la opción
`predicciones.csv` (PR #6). Filas comunes 7 612 en T+1 y 7 572 en T+2 en todas
las recetas; la referencia reproduce la tanda 11 (347 y 248 inicios al
presupuesto del canal condicionado). Comparación emparejada receta contra
referencia: mismas alertas por mes de origen, IC 95 % por bootstrap de
municipios (1 000 réplicas, semilla 42), como en `validar_candidato`.
«Años a favor» cuenta los años con más y con menos inicios que la referencia al
presupuesto del canal condicionado. Herramientas en `pipeline/tools/noche/`.
