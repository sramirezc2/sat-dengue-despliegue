# Tanda 23, línea AE — Ensambles entre logísticas

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **cerrada** el 10 de noviembre de 2026. Se corre sobre la base común del
> retroanálisis: `canonical.mode=approved`, calendario y departamentos de
> `parameters_retroanalisis.yml` sin tocar, `conjunto.csv` reportado.

## Origen

Se escribe después de ver la tanda 15 y se declara así: la logística con clima
quedó a favor en seis de siete años sin llegar a la barra. Un ensamble con la sin
clima podría conservar lo mejor de cada una.

## Hipótesis

Promediar los rangos de dos logísticas que difieren solo en el clima no debería
aportar casi nada, porque ordenan casi igual. Esta tanda sirve de **control** para
la tanda 14: si un ensamble de dos modelos casi idénticos ya «mejora», la mejora
de un ensamble con XGBoost habría que leerla con cuidado.

## Qué se corre

Con `tools/noche/ensamble.py` sobre las predicciones ya guardadas de la tanda 15:
promedio de rangos percentiles dentro de cada mes de origen entre la logística
sin clima y la logística con clima, y entre la sin clima y la mínima. La
referencia es la logística sin clima; el ensamble se compara también contra la
logística con clima.

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

## Resultado: el ensamble queda entre sus componentes

El ensamble sin clima + con clima suma +10 en T+1 (IC −2 a 21) y +3 en T+2, por
debajo de la logística con clima sola (+12 y +5). El ensamble sin clima + mínima
queda en −3 y +3. Ninguno pasa la barra ni supera al mejor de sus dos
componentes: **sin efecto**. Como control para la tanda 14, muestra que promediar
rangos de modelos parecidos da un punto intermedio, no una ganancia.

| T+1, 641 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ens_logistica_sin_clima+log_conclima | condicionado | 817 | 347 | 357 | +10 (-2 a 21) | +1.6 | 11.51 → 11.27 | 5+ / 0− |
| ens_logistica_sin_clima+log_conclima | 5 % | 209 | 109 | 110 | +1 (-9 a 11) | +0.2 | 2.45 → 2.43 |  |
| ens_logistica_sin_clima+log_conclima | 10 % | 406 | 189 | 190 | +1 (-9 a 12) | +0.2 | 5.32 → 5.29 |  |
| ens_logistica_sin_clima+log_conclima | 20 % | 817 | 304 | 310 | +6 (-5 a 18) | +0.9 | 12.57 → 12.42 |  |
| ens_logistica_sin_clima+log_minima | condicionado | 817 | 347 | 344 | -3 (-15 a 9) | -0.5 | 11.51 → 11.59 | 3+ / 4− |
| ens_logistica_sin_clima+log_minima | 5 % | 209 | 109 | 115 | +6 (-5 a 19) | +0.9 | 2.45 → 2.30 |  |
| ens_logistica_sin_clima+log_minima | 10 % | 406 | 189 | 193 | +4 (-8 a 16) | +0.6 | 5.32 → 5.22 |  |
| ens_logistica_sin_clima+log_minima | 20 % | 817 | 304 | 303 | -1 (-15 a 14) | -0.2 | 12.57 → 12.59 |  |
| log_conclima | condicionado | 817 | 347 | 359 | +12 (-4 a 28) | +1.9 | 11.51 → 11.22 | 6+ / 0− |
| log_conclima | 5 % | 209 | 109 | 112 | +3 (-12 a 16) | +0.5 | 2.45 → 2.38 |  |
| log_conclima | 10 % | 406 | 189 | 194 | +5 (-8 a 18) | +0.8 | 5.32 → 5.19 |  |
| log_conclima | 20 % | 817 | 304 | 317 | +13 (-4 a 30) | +2.0 | 12.57 → 12.25 |  |

| T+2, 459 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ens_logistica_sin_clima+log_conclima | condicionado | 1158 | 248 | 251 | +3 (-6 a 11) | +0.7 | 22.51 → 22.44 | 3+ / 1− |
| ens_logistica_sin_clima+log_conclima | 5 % | 207 | 67 | 65 | -2 (-10 a 6) | -0.4 | 3.46 → 3.51 |  |
| ens_logistica_sin_clima+log_conclima | 10 % | 402 | 123 | 128 | +5 (-2 a 12) | +1.1 | 6.90 → 6.78 |  |
| ens_logistica_sin_clima+log_conclima | 20 % | 809 | 204 | 209 | +5 (-4 a 14) | +1.1 | 14.97 → 14.84 |  |
| ens_logistica_sin_clima+log_minima | condicionado | 1158 | 248 | 251 | +3 (-5 a 11) | +0.7 | 22.51 → 22.44 | 2+ / 2− |
| ens_logistica_sin_clima+log_minima | 5 % | 207 | 67 | 66 | -1 (-9 a 8) | -0.2 | 3.46 → 3.49 |  |
| ens_logistica_sin_clima+log_minima | 10 % | 402 | 123 | 121 | -2 (-12 a 7) | -0.4 | 6.90 → 6.95 |  |
| ens_logistica_sin_clima+log_minima | 20 % | 809 | 204 | 210 | +6 (-5 a 17) | +1.3 | 14.97 → 14.82 |  |
| log_conclima | condicionado | 1158 | 248 | 253 | +5 (-9 a 17) | +1.1 | 22.51 → 22.39 | 3+ / 2− |
| log_conclima | 5 % | 207 | 67 | 65 | -2 (-12 a 9) | -0.4 | 3.46 → 3.51 |  |
| log_conclima | 10 % | 402 | 123 | 127 | +4 (-9 a 17) | +0.9 | 6.90 → 6.80 |  |
| log_conclima | 20 % | 809 | 204 | 211 | +7 (-6 a 21) | +1.5 | 14.97 → 14.79 |  |

Mismo instrumento y mismas filas que la tanda 15 (7 612 y 7 572); comparación
emparejada contra la logística sin clima con `pipeline/tools/noche/comparar.py`.
