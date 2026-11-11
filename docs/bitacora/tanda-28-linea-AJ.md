# Tanda 28, línea AJ — Excluir 2020 del entrenamiento

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **cerrada** el 11 de noviembre de 2026. Se corre sobre la base común del
> retroanálisis: `canonical.mode=approved`, calendario y departamentos de
> `parameters_retroanalisis.yml` sin tocar, `conjunto.csv` reportado.

## Hipótesis

En 2020 la vigilancia del dengue se alteró por la pandemia de COVID-19: menos
consultas y menos notificación. Si las etiquetas de 2020 están sesgadas, entrenar
con ellas le enseña al modelo una relación falsa entre casos y brotes. Excluirlas
del entrenamiento, **sin sacarlas de la evaluación**, debería ayudar en los años
siguientes.

## Qué se corre

`excluir_entrenamiento: [2020]`: los objetivos de 2020 no entran al ajuste de
ningún fold; 2020 se sigue evaluando y las filas evaluadas son las mismas. Sobre
la logística sin clima y la logística con clima, contra las mismas recetas sin
exclusión. Requiere la opción, por PR a main.

Se reporta además el efecto solo sobre 2021-2024, que es donde la exclusión puede
actuar.

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

## Resultado: excluir 2020 no ayuda; con clima resta algo en T+1

Comprobaciones previas: mismas 8 124 filas que la referencia, y el 72 % de los
puntajes cambia (la opción sí actúa). Dos corridas independientes de cada receta
dieron predicciones idénticas (diferencia máxima 0), así que el resultado es
reproducible.

Sin clima:

| T+1, 641 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| logistica_sin_clima_sin2020 | condicionado | 817 | 347 | 347 | +0 (-7 a 7) | +0.0 | 11.51 → 11.51 | 2+ / 2− |
| logistica_sin_clima_sin2020 | 5 % | 328 | 179 | 179 | +0 (-6 a 7) | +0.0 | 3.65 → 3.65 |  |
| logistica_sin_clima_sin2020 | 10 % | 656 | 297 | 295 | -2 (-11 a 7) | -0.3 | 8.79 → 8.84 |  |
| logistica_sin_clima_sin2020 | 20 % | 1230 | 426 | 424 | -2 (-7 a 3) | -0.3 | 19.70 → 19.75 |  |

| T+2, 459 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| logistica_sin_clima_sin2020 | condicionado | 1158 | 248 | 251 | +3 (-1 a 7) | +0.7 | 22.51 → 22.44 | 2+ / 0− |
| logistica_sin_clima_sin2020 | 5 % | 324 | 106 | 108 | +2 (-3 a 8) | +0.4 | 5.39 → 5.34 |  |
| logistica_sin_clima_sin2020 | 10 % | 648 | 190 | 189 | -1 (-4 a 2) | -0.2 | 11.33 → 11.36 |  |
| logistica_sin_clima_sin2020 | 20 % | 1215 | 276 | 277 | +1 (-3 a 5) | +0.2 | 23.23 → 23.21 |  |

Con clima:

| T+1, 641 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| log_conclima_sin2020 | condicionado | 817 | 359 | 351 | -8 (-15 a -2) | -1.2 | 11.22 → 11.42 | 0+ / 4− |
| log_conclima_sin2020 | 5 % | 328 | 180 | 181 | +1 (-4 a 7) | +0.2 | 3.63 → 3.60 |  |
| log_conclima_sin2020 | 10 % | 656 | 308 | 306 | -2 (-12 a 8) | -0.3 | 8.53 → 8.57 |  |
| log_conclima_sin2020 | 20 % | 1230 | 441 | 441 | +0 (-6 a 6) | +0.0 | 19.33 → 19.33 |  |

| T+2, 459 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| log_conclima_sin2020 | condicionado | 1158 | 253 | 253 | +0 (-6 a 6) | +0.0 | 22.39 → 22.39 | 1+ / 1− |
| log_conclima_sin2020 | 5 % | 324 | 103 | 105 | +2 (-3 a 8) | +0.4 | 5.47 → 5.42 |  |
| log_conclima_sin2020 | 10 % | 648 | 192 | 192 | +0 (-4 a 4) | +0.0 | 11.28 → 11.28 |  |
| log_conclima_sin2020 | 20 % | 1215 | 291 | 289 | -2 (-7 a 4) | -0.4 | 22.86 → 22.91 |  |

- **Sin clima: sin efecto** (0 en T+1, +3 en T+2). Sobre 2021-2024, donde la
  exclusión puede actuar: 0 y +3.
- **Con clima: resta 8 inicios en T+1** (IC −15 a −2, cuatro años en contra y
  ninguno a favor) y nada en T+2. Sobre 2021-2024: −8 y 0.
- Las etiquetas de 2020 no le enseñan al modelo nada falso que haya que quitar; con
  clima, al contrario, 2020 aporta.
