# Tanda 18, línea Z — Entrenar con todo el país y evaluar en Tolima y Meta

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **cerrada** el 11 de noviembre de 2026. Se corre sobre la base común del
> retroanálisis: `canonical.mode=approved`, calendario y departamentos de
> `parameters_retroanalisis.yml` sin tocar, `conjunto.csv` reportado.

## Hipótesis

Tolima y Meta tienen unos 600 inicios en siete años; el país tiene muchos más.
Entrenar con todos los municipios del país da al modelo muchos más ejemplos de
cómo arranca un brote, sin cambiar las filas que se evalúan. En la exploración
de la tanda 10, con otro instrumento, esta variante fue la mejor en T+2, pero
eso no se cita aquí como evidencia: esta tanda lo decide sobre la base común.

## Enmienda antes de correr (10 de noviembre, 23:00)

La corrida original se detuvo por falta de memoria antes de producir resultados.
Al relanzarla se cambia la segunda receta: en lugar de la mínima, **la logística
con clima**, porque las tandas 25 y 26 mostraron que el clima aporta en Meta solo
cuando se entrena juntando municipios, y entrenar con todo el país es la forma
más fuerte de juntarlos. Se declara después de ver esas tandas y antes de ver
cualquier resultado de esta.

## Qué se corre

La logística sin clima con `entrenamiento_nacional: true`: entrena en cada mes
de origen con todo el panel nacional y predice solo los 76 municipios de Tolima y
Meta. Las líneas base y las filas evaluadas son las mismas de la referencia; el
`conjunto.csv` de esta corrida cuenta filas nacionales y se declara aparte.

Requiere la opción `entrenamiento_nacional` en el retroanálisis, que va por PR a
main y no cambia nada cuando no se declara.

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

## Resultado: entrenar con todo el país no ayuda

Las dos corridas entrenaron con 130 810 y 130 189 filas comunes del país (T+1 y
T+2) y evaluaron las mismas 4 082 y 4 042 filas de Tolima y Meta que el modelo de
siempre. Contra la misma receta entrenada solo con Tolima y Meta:

Sin clima:

| T+1, 641 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| logistica_sin_clima | condicionado | 817 | 347 | 340 | -7 (-26 a 11) | -1.1 | 11.51 → 11.69 | 2+ / 5− |
| logistica_sin_clima | 5 % | 328 | 179 | 169 | -10 (-28 a 7) | -1.6 | 3.65 → 3.90 |  |
| logistica_sin_clima | 10 % | 656 | 297 | 294 | -3 (-24 a 17) | -0.5 | 8.79 → 8.87 |  |
| logistica_sin_clima | 20 % | 1230 | 426 | 428 | +2 (-17 a 20) | +0.3 | 19.70 → 19.65 |  |

| T+2, 459 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| logistica_sin_clima | condicionado | 1158 | 248 | 248 | +0 (-15 a 14) | +0.0 | 22.51 → 22.51 | 1+ / 3− |
| logistica_sin_clima | 5 % | 324 | 106 | 111 | +5 (-10 a 21) | +1.1 | 5.39 → 5.27 |  |
| logistica_sin_clima | 10 % | 648 | 190 | 186 | -4 (-21 a 12) | -0.9 | 11.33 → 11.43 |  |
| logistica_sin_clima | 20 % | 1215 | 276 | 282 | +6 (-12 a 23) | +1.3 | 23.23 → 23.08 |  |

Con clima:

| T+1, 641 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| log_conclima | condicionado | 817 | 359 | 345 | -14 (-34 a 2) | -2.2 | 11.22 → 11.56 | 2+ / 5− |
| log_conclima | 5 % | 328 | 180 | 172 | -8 (-27 a 11) | -1.2 | 3.63 → 3.82 |  |
| log_conclima | 10 % | 656 | 308 | 296 | -12 (-30 a 7) | -1.9 | 8.53 → 8.82 |  |
| log_conclima | 20 % | 1230 | 441 | 437 | -4 (-26 a 15) | -0.6 | 19.33 → 19.43 |  |

| T+2, 459 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| log_conclima | condicionado | 1158 | 253 | 252 | -1 (-15 a 14) | -0.2 | 22.39 → 22.41 | 2+ / 3− |
| log_conclima | 5 % | 324 | 103 | 102 | -1 (-17 a 16) | -0.2 | 5.47 → 5.49 |  |
| log_conclima | 10 % | 648 | 192 | 193 | +1 (-15 a 18) | +0.2 | 11.28 → 11.26 |  |
| log_conclima | 20 % | 1215 | 291 | 288 | -3 (-20 a 14) | -0.7 | 22.86 → 22.93 |  |

- **Sin clima: sin efecto** (−7 en T+1, 0 en T+2).
- **Con clima: empeora en T+1**, −14 inicios (IC −34 a 2, cinco años en contra), y
  empata en T+2.
- Lo que la tanda 26 sugería no se confirma: juntar Meta con Tolima sí ayuda al
  clima, pero juntar a todo el país lo diluye. La relación entre clima e inicio en
  Tolima y Meta no es la del resto del país.

Cada receta tardó unos 35 minutos (contra 3 del modelo de dos departamentos). La
línea se cierra.
