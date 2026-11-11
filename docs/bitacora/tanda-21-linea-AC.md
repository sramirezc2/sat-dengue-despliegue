# Tanda 21, línea AC — Ventana de entrenamiento móvil

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **cerrada** el 10 de noviembre de 2026. Se corre sobre la base común del
> retroanálisis: `canonical.mode=approved`, calendario y departamentos de
> `parameters_retroanalisis.yml` sin tocar, `conjunto.csv` reportado.

## Hipótesis

La frecuencia de inicios cambia mucho entre años (regla 5). Un modelo que
entrena solo con los últimos años podría seguir mejor esos cambios que uno que
acumula toda la historia desde 2012, a costa de menos ejemplos. En una
exploración anterior, con otro instrumento, las ventanas de 3 y 5 años no
mejoraron; esta tanda lo mide sobre la base común.

## Qué se corre

La logística sin clima y la mínima, con ventana móvil de **3, 5 y 8 años**
(`ventana_anios`): en cada origen se entrena solo con los objetivos de los
últimos N años, sin bajar del piso de 2012-01. Las filas evaluadas son las mismas;
la referencia es la misma receta con ventana expansiva.

Requiere la opción `ventana_anios` en el retroanálisis, por PR a main; sin
declararla, nada cambia.

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

## Resultado: Sin efecto

Ninguna ventana mejora a la expansiva. La de **3 años empeora** algo (−8 en T+1
y −11 en T+2, IC −24 a 0, cinco años en contra); la de 5 y la de 8 empatan con la
expansiva (entre −4 y +2). Se cierra la línea: entrenar con toda la historia
desde 2012 es lo mejor de lo probado.

| T+1, 641 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| logistica_sin_clima_ven3 | condicionado | 817 | 347 | 339 | -8 (-21 a 5) | -1.2 | 11.51 → 11.71 | 1+ / 5− |
| logistica_sin_clima_ven3 | 5 % | 209 | 109 | 108 | -1 (-12 a 10) | -0.2 | 2.45 → 2.47 |  |
| logistica_sin_clima_ven3 | 10 % | 406 | 189 | 189 | +0 (-14 a 13) | +0.0 | 5.32 → 5.32 |  |
| logistica_sin_clima_ven3 | 20 % | 817 | 304 | 291 | -13 (-27 a 2) | -2.0 | 12.57 → 12.89 |  |
| logistica_sin_clima_ven5 | condicionado | 817 | 347 | 343 | -4 (-15 a 7) | -0.6 | 11.51 → 11.61 | 0+ / 2− |
| logistica_sin_clima_ven5 | 5 % | 209 | 109 | 109 | +0 (-10 a 10) | +0.0 | 2.45 → 2.45 |  |
| logistica_sin_clima_ven5 | 10 % | 406 | 189 | 196 | +7 (-5 a 19) | +1.1 | 5.32 → 5.14 |  |
| logistica_sin_clima_ven5 | 20 % | 817 | 304 | 306 | +2 (-11 a 16) | +0.3 | 12.57 → 12.52 |  |
| logistica_sin_clima_ven8 | condicionado | 817 | 347 | 349 | +2 (-6 a 9) | +0.3 | 11.51 → 11.46 | 2+ / 1− |
| logistica_sin_clima_ven8 | 5 % | 209 | 109 | 111 | +2 (-3 a 7) | +0.3 | 2.45 → 2.40 |  |
| logistica_sin_clima_ven8 | 10 % | 406 | 189 | 190 | +1 (-6 a 9) | +0.2 | 5.32 → 5.29 |  |
| logistica_sin_clima_ven8 | 20 % | 817 | 304 | 306 | +2 (-5 a 9) | +0.3 | 12.57 → 12.52 |  |

| T+2, 459 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| logistica_sin_clima_ven3 | condicionado | 1158 | 248 | 237 | -11 (-24 a 0) | -2.4 | 22.51 → 22.79 | 0+ / 5− |
| logistica_sin_clima_ven3 | 5 % | 207 | 67 | 67 | +0 (-10 a 9) | +0.0 | 3.46 → 3.46 |  |
| logistica_sin_clima_ven3 | 10 % | 402 | 123 | 113 | -10 (-23 a 3) | -2.2 | 6.90 → 7.15 |  |
| logistica_sin_clima_ven3 | 20 % | 809 | 204 | 196 | -8 (-21 a 5) | -1.7 | 14.97 → 15.17 |  |
| logistica_sin_clima_ven5 | condicionado | 1158 | 248 | 248 | +0 (-9 a 8) | +0.0 | 22.51 → 22.51 | 2+ / 2− |
| logistica_sin_clima_ven5 | 5 % | 207 | 67 | 67 | +0 (-11 a 9) | +0.0 | 3.46 → 3.46 |  |
| logistica_sin_clima_ven5 | 10 % | 402 | 123 | 121 | -2 (-13 a 9) | -0.4 | 6.90 → 6.95 |  |
| logistica_sin_clima_ven5 | 20 % | 809 | 204 | 199 | -5 (-18 a 8) | -1.1 | 14.97 → 15.09 |  |
| logistica_sin_clima_ven8 | condicionado | 1158 | 248 | 246 | -2 (-8 a 3) | -0.4 | 22.51 → 22.56 | 1+ / 1− |
| logistica_sin_clima_ven8 | 5 % | 207 | 67 | 62 | -5 (-12 a 1) | -1.1 | 3.46 → 3.59 |  |
| logistica_sin_clima_ven8 | 10 % | 402 | 123 | 122 | -1 (-5 a 3) | -0.2 | 6.90 → 6.93 |  |
| logistica_sin_clima_ven8 | 20 % | 809 | 204 | 199 | -5 (-13 a 2) | -1.1 | 14.97 → 15.09 |  |

Corrida del 10 de noviembre de 2026, sobre el panel certificado `de49b11b…` del
release `satd-raw-173d5856`, con el nodo del retroanálisis de main más la opción
`predicciones.csv` (PR #6). Filas comunes 7 612 en T+1 y 7 572 en T+2 en todas
las recetas; la referencia reproduce la tanda 11 (347 y 248 inicios al
presupuesto del canal condicionado). Comparación emparejada receta contra
referencia: mismas alertas por mes de origen, IC 95 % por bootstrap de
municipios (1 000 réplicas, semilla 42), como en `validar_candidato`.
«Años a favor» cuenta los años con más y con menos inicios que la referencia al
presupuesto del canal condicionado. Herramientas en `pipeline/tools/noche/`.
