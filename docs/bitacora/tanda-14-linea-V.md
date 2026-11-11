# Tanda 14, línea V — Ensamble de rangos entre la logística y el XGBoost del banco

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **preinscrita, sin correr.** Se corre sobre la base común del
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
