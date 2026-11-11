# Tanda 14, línea V — Ensamble de rangos entre la logística y el XGBoost del banco

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **cerrada** el 10 de noviembre de 2026. Se corre sobre la base común del
> retroanálisis: `canonical.mode=approved`, calendario y departamentos de
> `parameters_retroanalisis.yml` sin tocar, `conjunto.csv` reportado.

## Hipótesis

La logística y el XGBoost del banco ordenan el riesgo con mecanismos distintos
(una suma de efectos en escala log contra cortes sucesivos), así que sus errores
no deberían coincidir del todo. Promediar sus rangos dentro de cada mes de
origen podría detectar más inicios que cualquiera de los dos solos, al mismo
presupuesto.

## Qué se corre

Sobre la base común y en una sola corrida: la logística sin clima y el XGBoost
del banco (`xgboost_banco.yml`, tanda 12) con **cinco semillas** (53, 7, 13, 29,
42), por la regla 9. El ensamble se arma después, fila a fila, con el puntaje que
el retroanálisis deja en `predicciones.csv`: promedio de rangos percentiles
dentro de cada mes de origen, sin pesos ni nada elegido sobre los resultados.
Para cada semilla se evalúa un ensamble, y se reporta la media y el rango de las
cinco. Se evalúan igual que cualquier receta, con `validar_candidato`.

Requiere que el retroanálisis guarde el puntaje por fila; ese cambio va por PR a
main y no cambia ningún otro resultado.

La comparación decisiva es el ensamble contra el **mejor** de sus dos
componentes, no contra el peor.

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

## Resultado: el ensamble no supera a la logística sola

Al presupuesto del canal condicionado, contra la logística sin clima y con las
cinco semillas de XGBoost:

| | T+1: media (mín. a máx.) | T+2: media (mín. a máx.) |
| --- | --- | --- |
| XGBoost del banco solo | −14,0 (−22 a −5) | −6,8 (−14 a −1) |
| Ensamble logística + XGBoost | +2,8 (0 a +7) | 0,0 (−3 a +2) |

El ensamble **no supera al mejor de sus componentes**, que es la logística: suma
entre 0 y 7 inicios en T+1 y entre −3 y +2 en T+2, siempre con IC que cruza el
cero. Veredicto: **sin efecto**.

Dos hallazgos de paso:

- **La logística le gana a XGBoost en las cinco semillas** y en los dos
  horizontes, lo que confirma la tanda 12 con la regla 9 cumplida.
- **La semilla 53, la de la tanda 12, es la más favorable a XGBoost de las
  cinco** (−5 en T+1 frente a una media de −14). La distancia real entre las dos
  familias es mayor que la que mostró la tanda 12. La variación entre semillas de
  XGBoost (17 inicios en T+1) es del mismo orden que los efectos que se están
  buscando, así que ninguna comparación de XGBoost con una sola semilla es
  concluyente.

Nota de método: el XGBoost del banco usa las 33 variables del contrato **con
clima**, y la logística de referencia es sin clima.

| T+1, 641 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| xgb_banco_s13 | condicionado | 817 | 347 | 331 | -16 (-39 a 7) | -2.5 | 11.51 → 11.91 | 0+ / 7− |
| xgb_banco_s13 | 5 % | 209 | 109 | 95 | -14 (-31 a 3) | -2.2 | 2.45 → 2.79 |  |
| xgb_banco_s13 | 10 % | 406 | 189 | 177 | -12 (-31 a 8) | -1.9 | 5.32 → 5.61 |  |
| xgb_banco_s13 | 20 % | 817 | 304 | 313 | +9 (-10 a 29) | +1.4 | 12.57 → 12.35 |  |
| xgb_banco_s29 | condicionado | 817 | 347 | 339 | -8 (-29 a 13) | -1.2 | 11.51 → 11.71 | 1+ / 6− |
| xgb_banco_s29 | 5 % | 209 | 109 | 95 | -14 (-36 a 4) | -2.2 | 2.45 → 2.79 |  |
| xgb_banco_s29 | 10 % | 406 | 189 | 173 | -16 (-36 a 3) | -2.5 | 5.32 → 5.71 |  |
| xgb_banco_s29 | 20 % | 817 | 304 | 308 | +4 (-16 a 26) | +0.6 | 12.57 → 12.47 |  |
| xgb_banco_s42 | condicionado | 817 | 347 | 325 | -22 (-43 a -3) | -3.4 | 11.51 → 12.05 | 1+ / 6− |
| xgb_banco_s42 | 5 % | 209 | 109 | 96 | -13 (-35 a 6) | -2.0 | 2.45 → 2.77 |  |
| xgb_banco_s42 | 10 % | 406 | 189 | 172 | -17 (-36 a 1) | -2.7 | 5.32 → 5.73 |  |
| xgb_banco_s42 | 20 % | 817 | 304 | 307 | +3 (-18 a 25) | +0.5 | 12.57 → 12.49 |  |
| xgb_banco_s53 | condicionado | 817 | 347 | 342 | -5 (-29 a 16) | -0.8 | 11.51 → 11.64 | 2+ / 4− |
| xgb_banco_s53 | 5 % | 209 | 109 | 101 | -8 (-31 a 12) | -1.2 | 2.45 → 2.65 |  |
| xgb_banco_s53 | 10 % | 406 | 189 | 183 | -6 (-28 a 12) | -0.9 | 5.32 → 5.46 |  |
| xgb_banco_s53 | 20 % | 817 | 304 | 312 | +8 (-14 a 29) | +1.2 | 12.57 → 12.37 |  |
| xgb_banco_s7 | condicionado | 817 | 347 | 328 | -19 (-40 a 1) | -3.0 | 11.51 → 11.98 | 1+ / 6− |
| xgb_banco_s7 | 5 % | 209 | 109 | 95 | -14 (-33 a 3) | -2.2 | 2.45 → 2.79 |  |
| xgb_banco_s7 | 10 % | 406 | 189 | 170 | -19 (-39 a 0) | -3.0 | 5.32 → 5.78 |  |
| xgb_banco_s7 | 20 % | 817 | 304 | 308 | +4 (-15 a 24) | +0.6 | 12.57 → 12.47 |  |
| ens_logistica_sin_clima+xgb_banco_s13 | condicionado | 817 | 347 | 354 | +7 (-6 a 21) | +1.1 | 11.51 → 11.34 | 4+ / 2− |
| ens_logistica_sin_clima+xgb_banco_s13 | 5 % | 209 | 109 | 106 | -3 (-18 a 12) | -0.5 | 2.45 → 2.52 |  |
| ens_logistica_sin_clima+xgb_banco_s13 | 10 % | 406 | 189 | 191 | +2 (-12 a 17) | +0.3 | 5.32 → 5.27 |  |
| ens_logistica_sin_clima+xgb_banco_s13 | 20 % | 817 | 304 | 315 | +11 (-3 a 26) | +1.7 | 12.57 → 12.30 |  |
| ens_logistica_sin_clima+xgb_banco_s29 | condicionado | 817 | 347 | 350 | +3 (-11 a 16) | +0.5 | 11.51 → 11.44 | 2+ / 4− |
| ens_logistica_sin_clima+xgb_banco_s29 | 5 % | 209 | 109 | 106 | -3 (-18 a 11) | -0.5 | 2.45 → 2.52 |  |
| ens_logistica_sin_clima+xgb_banco_s29 | 10 % | 406 | 189 | 185 | -4 (-19 a 10) | -0.6 | 5.32 → 5.41 |  |
| ens_logistica_sin_clima+xgb_banco_s29 | 20 % | 817 | 304 | 315 | +11 (-5 a 26) | +1.7 | 12.57 → 12.30 |  |
| ens_logistica_sin_clima+xgb_banco_s42 | condicionado | 817 | 347 | 348 | +1 (-13 a 15) | +0.2 | 11.51 → 11.49 | 3+ / 4− |
| ens_logistica_sin_clima+xgb_banco_s42 | 5 % | 209 | 109 | 105 | -4 (-19 a 10) | -0.6 | 2.45 → 2.55 |  |
| ens_logistica_sin_clima+xgb_banco_s42 | 10 % | 406 | 189 | 187 | -2 (-14 a 12) | -0.3 | 5.32 → 5.37 |  |
| ens_logistica_sin_clima+xgb_banco_s42 | 20 % | 817 | 304 | 312 | +8 (-8 a 23) | +1.2 | 12.57 → 12.37 |  |
| ens_logistica_sin_clima+xgb_banco_s53 | condicionado | 817 | 347 | 350 | +3 (-12 a 18) | +0.5 | 11.51 → 11.44 | 3+ / 3− |
| ens_logistica_sin_clima+xgb_banco_s53 | 5 % | 209 | 109 | 112 | +3 (-12 a 17) | +0.5 | 2.45 → 2.38 |  |
| ens_logistica_sin_clima+xgb_banco_s53 | 10 % | 406 | 189 | 185 | -4 (-19 a 12) | -0.6 | 5.32 → 5.41 |  |
| ens_logistica_sin_clima+xgb_banco_s53 | 20 % | 817 | 304 | 310 | +6 (-10 a 22) | +0.9 | 12.57 → 12.42 |  |
| ens_logistica_sin_clima+xgb_banco_s7 | condicionado | 817 | 347 | 347 | +0 (-13 a 14) | +0.0 | 11.51 → 11.51 | 2+ / 4− |
| ens_logistica_sin_clima+xgb_banco_s7 | 5 % | 209 | 109 | 103 | -6 (-22 a 9) | -0.9 | 2.45 → 2.60 |  |
| ens_logistica_sin_clima+xgb_banco_s7 | 10 % | 406 | 189 | 189 | +0 (-13 a 14) | +0.0 | 5.32 → 5.32 |  |
| ens_logistica_sin_clima+xgb_banco_s7 | 20 % | 817 | 304 | 313 | +9 (-5 a 23) | +1.4 | 12.57 → 12.35 |  |

| T+2, 459 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| xgb_banco_s13 | condicionado | 1158 | 248 | 240 | -8 (-28 a 12) | -1.7 | 22.51 → 22.71 | 2+ / 5− |
| xgb_banco_s13 | 5 % | 207 | 67 | 66 | -1 (-16 a 15) | -0.2 | 3.46 → 3.49 |  |
| xgb_banco_s13 | 10 % | 402 | 123 | 121 | -2 (-22 a 18) | -0.4 | 6.90 → 6.95 |  |
| xgb_banco_s13 | 20 % | 809 | 204 | 194 | -10 (-33 a 12) | -2.2 | 14.97 → 15.22 |  |
| xgb_banco_s29 | condicionado | 1158 | 248 | 242 | -6 (-27 a 14) | -1.3 | 22.51 → 22.66 | 3+ / 4− |
| xgb_banco_s29 | 5 % | 207 | 67 | 69 | +2 (-15 a 20) | +0.4 | 3.46 → 3.41 |  |
| xgb_banco_s29 | 10 % | 402 | 123 | 115 | -8 (-25 a 11) | -1.7 | 6.90 → 7.10 |  |
| xgb_banco_s29 | 20 % | 809 | 204 | 190 | -14 (-35 a 6) | -3.1 | 14.97 → 15.31 |  |
| xgb_banco_s42 | condicionado | 1158 | 248 | 234 | -14 (-35 a 6) | -3.1 | 22.51 → 22.86 | 2+ / 5− |
| xgb_banco_s42 | 5 % | 207 | 67 | 62 | -5 (-23 a 13) | -1.1 | 3.46 → 3.59 |  |
| xgb_banco_s42 | 10 % | 402 | 123 | 113 | -10 (-28 a 7) | -2.2 | 6.90 → 7.15 |  |
| xgb_banco_s42 | 20 % | 809 | 204 | 191 | -13 (-36 a 10) | -2.8 | 14.97 → 15.29 |  |
| xgb_banco_s53 | condicionado | 1158 | 248 | 247 | -1 (-21 a 18) | -0.2 | 22.51 → 22.54 | 2+ / 4− |
| xgb_banco_s53 | 5 % | 207 | 67 | 63 | -4 (-19 a 12) | -0.9 | 3.46 → 3.56 |  |
| xgb_banco_s53 | 10 % | 402 | 123 | 110 | -13 (-30 a 4) | -2.8 | 6.90 → 7.22 |  |
| xgb_banco_s53 | 20 % | 809 | 204 | 195 | -9 (-32 a 13) | -2.0 | 14.97 → 15.19 |  |
| xgb_banco_s7 | condicionado | 1158 | 248 | 243 | -5 (-22 a 12) | -1.1 | 22.51 → 22.64 | 2+ / 4− |
| xgb_banco_s7 | 5 % | 207 | 67 | 63 | -4 (-21 a 12) | -0.9 | 3.46 → 3.56 |  |
| xgb_banco_s7 | 10 % | 402 | 123 | 120 | -3 (-22 a 15) | -0.7 | 6.90 → 6.98 |  |
| xgb_banco_s7 | 20 % | 809 | 204 | 191 | -13 (-36 a 9) | -2.8 | 14.97 → 15.29 |  |
| ens_logistica_sin_clima+xgb_banco_s13 | condicionado | 1158 | 248 | 248 | +0 (-14 a 14) | +0.0 | 22.51 → 22.51 | 3+ / 2− |
| ens_logistica_sin_clima+xgb_banco_s13 | 5 % | 207 | 67 | 74 | +7 (-6 a 20) | +1.5 | 3.46 → 3.29 |  |
| ens_logistica_sin_clima+xgb_banco_s13 | 10 % | 402 | 123 | 126 | +3 (-8 a 14) | +0.7 | 6.90 → 6.83 |  |
| ens_logistica_sin_clima+xgb_banco_s13 | 20 % | 809 | 204 | 207 | +3 (-10 a 16) | +0.7 | 14.97 → 14.89 |  |
| ens_logistica_sin_clima+xgb_banco_s29 | condicionado | 1158 | 248 | 249 | +1 (-16 a 17) | +0.2 | 22.51 → 22.49 | 3+ / 3− |
| ens_logistica_sin_clima+xgb_banco_s29 | 5 % | 207 | 67 | 71 | +4 (-9 a 18) | +0.9 | 3.46 → 3.36 |  |
| ens_logistica_sin_clima+xgb_banco_s29 | 10 % | 402 | 123 | 126 | +3 (-10 a 16) | +0.7 | 6.90 → 6.83 |  |
| ens_logistica_sin_clima+xgb_banco_s29 | 20 % | 809 | 204 | 206 | +2 (-12 a 16) | +0.4 | 14.97 → 14.92 |  |
| ens_logistica_sin_clima+xgb_banco_s42 | condicionado | 1158 | 248 | 250 | +2 (-13 a 16) | +0.4 | 22.51 → 22.46 | 3+ / 4− |
| ens_logistica_sin_clima+xgb_banco_s42 | 5 % | 207 | 67 | 67 | +0 (-12 a 14) | +0.0 | 3.46 → 3.46 |  |
| ens_logistica_sin_clima+xgb_banco_s42 | 10 % | 402 | 123 | 122 | -1 (-12 a 11) | -0.2 | 6.90 → 6.93 |  |
| ens_logistica_sin_clima+xgb_banco_s42 | 20 % | 809 | 204 | 206 | +2 (-10 a 14) | +0.4 | 14.97 → 14.92 |  |
| ens_logistica_sin_clima+xgb_banco_s53 | condicionado | 1158 | 248 | 248 | +0 (-14 a 13) | +0.0 | 22.51 → 22.51 | 3+ / 2− |
| ens_logistica_sin_clima+xgb_banco_s53 | 5 % | 207 | 67 | 73 | +6 (-5 a 19) | +1.3 | 3.46 → 3.32 |  |
| ens_logistica_sin_clima+xgb_banco_s53 | 10 % | 402 | 123 | 127 | +4 (-6 a 14) | +0.9 | 6.90 → 6.80 |  |
| ens_logistica_sin_clima+xgb_banco_s53 | 20 % | 809 | 204 | 206 | +2 (-12 a 17) | +0.4 | 14.97 → 14.92 |  |
| ens_logistica_sin_clima+xgb_banco_s7 | condicionado | 1158 | 248 | 245 | -3 (-17 a 10) | -0.7 | 22.51 → 22.59 | 3+ / 3− |
| ens_logistica_sin_clima+xgb_banco_s7 | 5 % | 207 | 67 | 73 | +6 (-6 a 18) | +1.3 | 3.46 → 3.32 |  |
| ens_logistica_sin_clima+xgb_banco_s7 | 10 % | 402 | 123 | 130 | +7 (-5 a 19) | +1.5 | 6.90 → 6.73 |  |
| ens_logistica_sin_clima+xgb_banco_s7 | 20 % | 809 | 204 | 205 | +1 (-13 a 15) | +0.2 | 14.97 → 14.94 |  |

Mismas filas en todas las recetas (7 612 y 7 572). Ensamble con
`pipeline/tools/noche/ensamble.py`; comparación con `comparar.py`.
