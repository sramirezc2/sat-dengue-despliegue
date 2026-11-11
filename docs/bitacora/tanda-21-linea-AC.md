# Tanda 21, línea AC — Ventana de entrenamiento móvil

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **preinscrita, sin correr.** Se corre sobre la base común del
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
