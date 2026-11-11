# Tanda 15, línea W — El clima sobre la base común

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **cerrada** el 10 de noviembre de 2026. Se corre sobre la base común del
> retroanálisis: `canonical.mode=approved`, calendario y departamentos de
> `parameters_retroanalisis.yml` sin tocar, `conjunto.csv` reportado.

## Hipótesis

En la tanda 10, con el clima de enero de 2020 completo, la logística con clima
quedó apenas por encima de la versión sin clima. Si el clima aporta algo, debería
verse más en T+2, donde la lluvia y la temperatura tienen tiempo de actuar sobre
el vector.

## Qué se corre

`log_conclima.yml`: la misma logística de la referencia más las nueve variables
de clima del contrato, en el mes de origen. Una sola diferencia.

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

## Resultado: Sin efecto por la regla preinscrita, pero consistente

El clima suma **+12 inicios en T+1** (IC −4 a 28, +1,9 puntos) y **+5 en T+2**
(IC −9 a 17), y baja un poco la carga. No llega a la barra de mejora (32 y 23
inicios), así que el veredicto preinscrito es **sin efecto**. Pero en T+1 queda a
favor en **seis de los siete años y en contra en ninguno** (2021 empata), que es
la señal más consistente de la noche. Por eso se abre la tanda 22 para ver qué
parte del clima aporta, declarando que se escribe después de ver esto.

| T+1, 641 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| log_conclima | condicionado | 817 | 347 | 359 | +12 (-4 a 28) | +1.9 | 11.51 → 11.22 | 6+ / 0− |
| log_conclima | 5 % | 209 | 109 | 112 | +3 (-12 a 16) | +0.5 | 2.45 → 2.38 |  |
| log_conclima | 10 % | 406 | 189 | 194 | +5 (-8 a 18) | +0.8 | 5.32 → 5.19 |  |
| log_conclima | 20 % | 817 | 304 | 317 | +13 (-4 a 30) | +2.0 | 12.57 → 12.25 |  |

| T+2, 459 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| log_conclima | condicionado | 1158 | 248 | 253 | +5 (-9 a 17) | +1.1 | 22.51 → 22.39 | 3+ / 2− |
| log_conclima | 5 % | 207 | 67 | 65 | -2 (-12 a 9) | -0.4 | 3.46 → 3.51 |  |
| log_conclima | 10 % | 402 | 123 | 127 | +4 (-9 a 17) | +0.9 | 6.90 → 6.80 |  |
| log_conclima | 20 % | 809 | 204 | 211 | +7 (-6 a 21) | +1.5 | 14.97 → 14.79 |  |

Corrida del 10 de noviembre de 2026, sobre el panel certificado `de49b11b…` del
release `satd-raw-173d5856`, con el nodo del retroanálisis de main más la opción
`predicciones.csv` (PR #6). Filas comunes 7 612 en T+1 y 7 572 en T+2 en todas
las recetas; la referencia reproduce la tanda 11 (347 y 248 inicios al
presupuesto del canal condicionado). Comparación emparejada receta contra
referencia: mismas alertas por mes de origen, IC 95 % por bootstrap de
municipios (1 000 réplicas, semilla 42), como en `validar_candidato`.
«Años a favor» cuenta los años con más y con menos inicios que la referencia al
presupuesto del canal condicionado. Herramientas en `pipeline/tools/noche/`.
