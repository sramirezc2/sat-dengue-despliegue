# Tanda 18, línea Z — Entrenar con todo el país y evaluar en Tolima y Meta

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **preinscrita, sin correr.** Se corre sobre la base común del
> retroanálisis: `canonical.mode=approved`, calendario y departamentos de
> `parameters_retroanalisis.yml` sin tocar, `conjunto.csv` reportado.

## Hipótesis

Tolima y Meta tienen unos 600 inicios en siete años; el país tiene muchos más.
Entrenar con todos los municipios del país da al modelo muchos más ejemplos de
cómo arranca un brote, sin cambiar las filas que se evalúan. En la exploración
de la tanda 10, con otro instrumento, esta variante fue la mejor en T+2, pero
eso no se cita aquí como evidencia: esta tanda lo decide sobre la base común.

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
