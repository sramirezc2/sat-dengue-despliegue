# Tanda 22, línea AD — Qué parte del clima aporta

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **cerrada** el 10 de noviembre de 2026. Se corre sobre la base común del
> retroanálisis: `canonical.mode=approved`, calendario y departamentos de
> `parameters_retroanalisis.yml` sin tocar, `conjunto.csv` reportado.

## Origen

Se escribe después de ver la tanda 15, y se declara así. En la tanda 15 el
clima sumó 12 inicios en T+1 (IC −4 a 28) y quedó a favor en los siete años, sin
llegar a la barra de mejora. Es la única señal consistente de la noche, y por eso
se prioriza esta tanda. Esa falta de ceguera se compensa con una regla fija: la
referencia de esta tanda es la **logística con clima** de la tanda 15, no la sin
clima, así que ninguna variante gana por repetir lo que el clima ya dio.

## Hipótesis

Si el clima aporta, debería aportar más con una forma mejor: menos variables
ruidosas, la lluvia en escala log, o sobre la versión mínima del modelo.

## Qué se corre

Contra la logística con clima, una diferencia a la vez:

- solo lluvia, temperatura y punto de rocío;
- todo el clima menos el viento;
- log1p en lluvia y escorrentía;
- C = 10;
- la logística mínima más las nueve variables de clima, contra la mínima sin clima.

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

## Resultado: la forma del clima no importa; el clima sí

Contra la logística con clima (359 y 253 inicios), ninguna variante cambia más de
4 inicios: solo lluvia, temperatura y punto de rocío (+3 y −4), sin viento (−2 y
+1), log1p en lluvia y escorrentía (−2 y +4, con cuatro años a favor y ninguno en
contra en T+2) y C = 10 (−2 y 0). Veredicto para las cuatro: **sin efecto**. El
clima completo de nueve variables, tal como está, es tan bueno como cualquier
recorte.

Sobre la logística mínima, **el clima vuelve a sumar en T+1: +15 (IC −5 a 34),
seis años a favor y uno en contra**, y nada en T+2 (+2). Es la tercera vez en la
noche que el clima suma en T+1 de forma consistente sin llegar a la barra de 5
puntos (tandas 15, 22 y, por departamento, la 25).

| T+1, 641 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| logc_lluvia_temp | condicionado | 817 | 359 | 362 | +3 (-8 a 16) | +0.5 | 11.22 → 11.15 | 3+ / 1− |
| logc_lluvia_temp | 5 % | 209 | 112 | 110 | -2 (-11 a 6) | -0.3 | 2.38 → 2.43 |  |
| logc_lluvia_temp | 10 % | 406 | 194 | 193 | -1 (-12 a 9) | -0.2 | 5.19 → 5.22 |  |
| logc_lluvia_temp | 20 % | 817 | 317 | 316 | -1 (-13 a 12) | -0.2 | 12.25 → 12.27 |  |
| logc_sin_viento | condicionado | 817 | 359 | 357 | -2 (-9 a 5) | -0.3 | 11.22 → 11.27 | 1+ / 2− |
| logc_sin_viento | 5 % | 209 | 112 | 111 | -1 (-5 a 3) | -0.2 | 2.38 → 2.40 |  |
| logc_sin_viento | 10 % | 406 | 194 | 194 | +0 (-8 a 9) | +0.0 | 5.19 → 5.19 |  |
| logc_sin_viento | 20 % | 817 | 317 | 318 | +1 (-8 a 10) | +0.2 | 12.25 → 12.22 |  |
| logc_log1p_lluvia | condicionado | 817 | 359 | 357 | -2 (-7 a 3) | -0.3 | 11.22 → 11.27 | 1+ / 2− |
| logc_log1p_lluvia | 5 % | 209 | 112 | 113 | +1 (-4 a 7) | +0.2 | 2.38 → 2.35 |  |
| logc_log1p_lluvia | 10 % | 406 | 194 | 197 | +3 (-1 a 7) | +0.5 | 5.19 → 5.12 |  |
| logc_log1p_lluvia | 20 % | 817 | 317 | 317 | +0 (-5 a 5) | +0.0 | 12.25 → 12.25 |  |
| logc_C10 | condicionado | 817 | 359 | 357 | -2 (-7 a 3) | -0.3 | 11.22 → 11.27 | 1+ / 3− |
| logc_C10 | 5 % | 209 | 112 | 111 | -1 (-3 a 0) | -0.2 | 2.38 → 2.40 |  |
| logc_C10 | 10 % | 406 | 194 | 193 | -1 (-4 a 2) | -0.2 | 5.19 → 5.22 |  |
| logc_C10 | 20 % | 817 | 317 | 316 | -1 (-5 a 2) | -0.2 | 12.25 → 12.27 |  |

| T+2, 459 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| logc_lluvia_temp | condicionado | 1158 | 253 | 249 | -4 (-13 a 5) | -0.9 | 22.39 → 22.49 | 2+ / 4− |
| logc_lluvia_temp | 5 % | 207 | 65 | 64 | -1 (-9 a 7) | -0.2 | 3.51 → 3.54 |  |
| logc_lluvia_temp | 10 % | 402 | 127 | 129 | +2 (-9 a 14) | +0.4 | 6.80 → 6.75 |  |
| logc_lluvia_temp | 20 % | 809 | 211 | 209 | -2 (-12 a 9) | -0.4 | 14.79 → 14.84 |  |
| logc_sin_viento | condicionado | 1158 | 253 | 254 | +1 (-6 a 8) | +0.2 | 22.39 → 22.37 | 3+ / 2− |
| logc_sin_viento | 5 % | 207 | 65 | 66 | +1 (-4 a 6) | +0.2 | 3.51 → 3.49 |  |
| logc_sin_viento | 10 % | 402 | 127 | 128 | +1 (-7 a 10) | +0.2 | 6.80 → 6.78 |  |
| logc_sin_viento | 20 % | 809 | 211 | 209 | -2 (-11 a 7) | -0.4 | 14.79 → 14.84 |  |
| logc_log1p_lluvia | condicionado | 1158 | 253 | 257 | +4 (0 a 9) | +0.9 | 22.39 → 22.29 | 4+ / 0− |
| logc_log1p_lluvia | 5 % | 207 | 65 | 66 | +1 (-2 a 4) | +0.2 | 3.51 → 3.49 |  |
| logc_log1p_lluvia | 10 % | 402 | 127 | 129 | +2 (-2 a 6) | +0.4 | 6.80 → 6.75 |  |
| logc_log1p_lluvia | 20 % | 809 | 211 | 211 | +0 (-7 a 7) | +0.0 | 14.79 → 14.79 |  |
| logc_C10 | condicionado | 1158 | 253 | 253 | +0 (-4 a 4) | +0.0 | 22.39 → 22.39 | 3+ / 3− |
| logc_C10 | 5 % | 207 | 65 | 66 | +1 (0 a 3) | +0.2 | 3.51 → 3.49 |  |
| logc_C10 | 10 % | 402 | 127 | 127 | +0 (-3 a 3) | +0.0 | 6.80 → 6.80 |  |
| logc_C10 | 20 % | 809 | 211 | 210 | -1 (-7 a 5) | -0.2 | 14.79 → 14.82 |  |

La mínima con clima contra la mínima sin clima:

| T+1, 641 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| logc_minima | condicionado | 817 | 339 | 354 | +15 (-5 a 34) | +2.3 | 11.71 → 11.34 | 6+ / 1− |
| logc_minima | 5 % | 209 | 115 | 108 | -7 (-23 a 7) | -1.1 | 2.30 → 2.47 |  |
| logc_minima | 10 % | 406 | 184 | 195 | +11 (-8 a 31) | +1.7 | 5.44 → 5.17 |  |
| logc_minima | 20 % | 817 | 301 | 319 | +18 (-4 a 40) | +2.8 | 12.64 → 12.20 |  |

| T+2, 459 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| logc_minima | condicionado | 1158 | 245 | 247 | +2 (-14 a 17) | +0.4 | 22.59 → 22.54 | 4+ / 2− |
| logc_minima | 5 % | 207 | 68 | 69 | +1 (-9 a 12) | +0.2 | 3.44 → 3.41 |  |
| logc_minima | 10 % | 402 | 126 | 123 | -3 (-16 a 9) | -0.7 | 6.83 → 6.90 |  |
| logc_minima | 20 % | 809 | 205 | 212 | +7 (-7 a 21) | +1.5 | 14.94 → 14.77 |  |
