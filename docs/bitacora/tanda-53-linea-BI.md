# Tanda 53, línea BI — El clima con regularización más fuerte

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **cerrada** el 11 de noviembre de 2026. Se corre sobre la base común del
> retroanálisis: `canonical.mode=approved`, calendario y departamentos de
> `parameters_retroanalisis.yml` sin tocar, `conjunto.csv` reportado.

## Origen

Sin clima, C de 0,1 a 100 dio lo mismo (tanda 16); con clima solo se probó C = 10
(tanda 22). Con nueve variables de clima correlacionadas, una regularización más
fuerte podría quitar ruido.

## Hipótesis

Con C = 0,1, la logística con clima conserva o mejora su ganancia en T+1.

## Qué se corre

La logística con clima con C = 0,1. Referencia: la logística con clima (C = 1).

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

| T+1, 641 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| logc_C0p1 | condicionado | 817 | 359 | 356 | -3 (-11 a 4) | -0.5 | 11.22 → 11.29 | 2+ / 3− |
| logc_C0p1 | 5 % | 328 | 180 | 178 | -2 (-11 a 6) | -0.3 | 3.63 → 3.67 |  |
| logc_C0p1 | 10 % | 656 | 308 | 305 | -3 (-12 a 6) | -0.5 | 8.53 → 8.60 |  |
| logc_C0p1 | 20 % | 1230 | 441 | 438 | -3 (-11 a 5) | -0.5 | 19.33 → 19.40 |  |

| T+2, 459 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| logc_C0p1 | condicionado | 1158 | 253 | 249 | -4 (-13 a 4) | -0.9 | 22.39 → 22.49 | 1+ / 3− |
| logc_C0p1 | 5 % | 324 | 103 | 104 | +1 (-7 a 8) | +0.2 | 5.47 → 5.44 |  |
| logc_C0p1 | 10 % | 648 | 192 | 187 | -5 (-15 a 4) | -1.1 | 11.28 → 11.41 |  |
| logc_C0p1 | 20 % | 1215 | 291 | 290 | -1 (-8 a 6) | -0.2 | 22.86 → 22.88 |  |

Con C = 0,1 la logística con clima queda en −3 en T+1 y −4 en T+2 frente a C = 1.
Al 10 % pasa la barra en T+2 (+7,0 pp) pero en T+1 pierde A por poco (+2,8, IC 0,0 a
5,5). C = 1 sigue siendo la mejor elección; regularizar más no le quita ruido al
clima.

Corrida del 11 de noviembre sobre main (`3011db9`), mismo panel y mismas filas (8 124 predicciones por combinación).
