# Tanda 28, línea AJ — Excluir 2020 del entrenamiento

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **preinscrita, sin correr.** Se corre sobre la base común del
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
