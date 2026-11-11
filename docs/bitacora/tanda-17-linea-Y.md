# Tanda 17, línea Y — Versiones reducidas de la logística

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **cerrada** el 10 de noviembre de 2026. Se corre sobre la base común del
> retroanálisis: `canonical.mode=approved`, calendario y departamentos de
> `parameters_retroanalisis.yml` sin tocar, `conjunto.csv` reportado.

## Hipótesis

En la tanda 10 una logística de cinco variables rindió casi igual que la
completa. Si eso se sostiene sobre la base común, el modelo que se propone puede
ser mucho más simple y explicable.

## Qué se corre

- `log_minima.yml`: las cinco variables de la tanda 10.
- `log_minima_lag2.yml`, `log_minima_p25.yml`, `log_minima_total.yml`: la mínima
  con una variable más cada una.
- `log_canal_dengue.yml`: solo las variables del canal y de dengue.

Aquí la pregunta es la inversa: **se acepta la versión reducida** si no pierde
más de 5 puntos frente a la completa en ningún horizonte.

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

## Resultado: Se acepta la versión reducida

Ninguna versión reducida pierde más de 5 puntos frente a la completa en ningún
horizonte. La **mínima de cinco variables** queda en −8 en T+1 (IC −25 a 10) y −3
en T+2 (IC −15 a 8); las variantes con una variable más quedan entre −9 y −3.
Por el criterio preinscrito **se acepta la mínima** como versión explicable,
sabiendo que en T+1 tiende a quedar unos pocos inicios abajo (3 años a favor y 4
en contra).

| T+1, 641 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| log_canal_dengue | condicionado | 817 | 347 | 342 | -5 (-16 a 6) | -0.8 | 11.51 → 11.64 | 2+ / 3− |
| log_canal_dengue | 5 % | 209 | 109 | 106 | -3 (-10 a 4) | -0.5 | 2.45 → 2.52 |  |
| log_canal_dengue | 10 % | 406 | 189 | 195 | +6 (-3 a 16) | +0.9 | 5.32 → 5.17 |  |
| log_canal_dengue | 20 % | 817 | 304 | 307 | +3 (-9 a 15) | +0.5 | 12.57 → 12.49 |  |
| log_minima | condicionado | 817 | 347 | 339 | -8 (-25 a 10) | -1.2 | 11.51 → 11.71 | 3+ / 4− |
| log_minima | 5 % | 209 | 109 | 115 | +6 (-9 a 20) | +0.9 | 2.45 → 2.30 |  |
| log_minima | 10 % | 406 | 189 | 184 | -5 (-21 a 11) | -0.8 | 5.32 → 5.44 |  |
| log_minima | 20 % | 817 | 304 | 301 | -3 (-23 a 17) | -0.5 | 12.57 → 12.64 |  |
| log_minima_lag2 | condicionado | 817 | 347 | 338 | -9 (-23 a 5) | -1.4 | 11.51 → 11.73 | 1+ / 4− |
| log_minima_lag2 | 5 % | 209 | 109 | 111 | +2 (-7 a 11) | +0.3 | 2.45 → 2.40 |  |
| log_minima_lag2 | 10 % | 406 | 189 | 191 | +2 (-11 a 16) | +0.3 | 5.32 → 5.27 |  |
| log_minima_lag2 | 20 % | 817 | 304 | 299 | -5 (-21 a 11) | -0.8 | 12.57 → 12.69 |  |
| log_minima_p25 | condicionado | 817 | 347 | 342 | -5 (-20 a 11) | -0.8 | 11.51 → 11.64 | 2+ / 4− |
| log_minima_p25 | 5 % | 209 | 109 | 111 | +2 (-11 a 16) | +0.3 | 2.45 → 2.40 |  |
| log_minima_p25 | 10 % | 406 | 189 | 191 | +2 (-13 a 18) | +0.3 | 5.32 → 5.27 |  |
| log_minima_p25 | 20 % | 817 | 304 | 303 | -1 (-16 a 15) | -0.2 | 12.57 → 12.59 |  |
| log_minima_total | condicionado | 817 | 347 | 344 | -3 (-19 a 13) | -0.5 | 11.51 → 11.59 | 3+ / 4− |
| log_minima_total | 5 % | 209 | 109 | 114 | +5 (-10 a 20) | +0.8 | 2.45 → 2.33 |  |
| log_minima_total | 10 % | 406 | 189 | 183 | -6 (-22 a 10) | -0.9 | 5.32 → 5.46 |  |
| log_minima_total | 20 % | 817 | 304 | 305 | +1 (-19 a 20) | +0.2 | 12.57 → 12.54 |  |

| T+2, 459 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| log_canal_dengue | condicionado | 1158 | 248 | 248 | +0 (-5 a 5) | +0.0 | 22.51 → 22.51 | 2+ / 2− |
| log_canal_dengue | 5 % | 207 | 67 | 64 | -3 (-9 a 3) | -0.7 | 3.46 → 3.54 |  |
| log_canal_dengue | 10 % | 402 | 123 | 121 | -2 (-8 a 4) | -0.4 | 6.90 → 6.95 |  |
| log_canal_dengue | 20 % | 809 | 204 | 208 | +4 (-4 a 12) | +0.9 | 14.97 → 14.87 |  |
| log_minima | condicionado | 1158 | 248 | 245 | -3 (-15 a 8) | -0.7 | 22.51 → 22.59 | 1+ / 3− |
| log_minima | 5 % | 207 | 67 | 68 | +1 (-10 a 11) | +0.2 | 3.46 → 3.44 |  |
| log_minima | 10 % | 402 | 123 | 126 | +3 (-8 a 15) | +0.7 | 6.90 → 6.83 |  |
| log_minima | 20 % | 809 | 204 | 205 | +1 (-12 a 14) | +0.2 | 14.97 → 14.94 |  |
| log_minima_lag2 | condicionado | 1158 | 248 | 246 | -2 (-11 a 6) | -0.4 | 22.51 → 22.56 | 1+ / 3− |
| log_minima_lag2 | 5 % | 207 | 67 | 63 | -4 (-13 a 5) | -0.9 | 3.46 → 3.56 |  |
| log_minima_lag2 | 10 % | 402 | 123 | 121 | -2 (-12 a 7) | -0.4 | 6.90 → 6.95 |  |
| log_minima_lag2 | 20 % | 809 | 204 | 205 | +1 (-8 a 10) | +0.2 | 14.97 → 14.94 |  |
| log_minima_p25 | condicionado | 1158 | 248 | 244 | -4 (-15 a 6) | -0.9 | 22.51 → 22.61 | 2+ / 3− |
| log_minima_p25 | 5 % | 207 | 67 | 66 | -1 (-11 a 9) | -0.2 | 3.46 → 3.49 |  |
| log_minima_p25 | 10 % | 402 | 123 | 127 | +4 (-6 a 14) | +0.9 | 6.90 → 6.80 |  |
| log_minima_p25 | 20 % | 809 | 204 | 205 | +1 (-12 a 13) | +0.2 | 14.97 → 14.94 |  |
| log_minima_total | condicionado | 1158 | 248 | 245 | -3 (-14 a 8) | -0.7 | 22.51 → 22.59 | 1+ / 4− |
| log_minima_total | 5 % | 207 | 67 | 69 | +2 (-9 a 13) | +0.4 | 3.46 → 3.41 |  |
| log_minima_total | 10 % | 402 | 123 | 125 | +2 (-9 a 14) | +0.4 | 6.90 → 6.85 |  |
| log_minima_total | 20 % | 809 | 204 | 206 | +2 (-11 a 15) | +0.4 | 14.97 → 14.92 |  |

Corrida del 10 de noviembre de 2026, sobre el panel certificado `de49b11b…` del
release `satd-raw-173d5856`, con el nodo del retroanálisis de main más la opción
`predicciones.csv` (PR #6). Filas comunes 7 612 en T+1 y 7 572 en T+2 en todas
las recetas; la referencia reproduce la tanda 11 (347 y 248 inicios al
presupuesto del canal condicionado). Comparación emparejada receta contra
referencia: mismas alertas por mes de origen, IC 95 % por bootstrap de
municipios (1 000 réplicas, semilla 42), como en `validar_candidato`.
«Años a favor» cuenta los años con más y con menos inicios que la referencia al
presupuesto del canal condicionado. Herramientas en `pipeline/tools/noche/`.
