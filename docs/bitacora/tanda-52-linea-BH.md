# Tanda 52, línea BH — El clima sobre las variantes de la mínima

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **preinscrita, sin correr.** Se corre sobre la base común del
> retroanálisis: `canonical.mode=approved`, calendario y departamentos de
> `parameters_retroanalisis.yml` sin tocar, `conjunto.csv` reportado.

## Origen

Se escribe después de las tandas 17 y 22 y se declara así: el clima sumó +15 en T+1
sobre la mínima (tanda 22), y la mínima con rezago 2 y la mínima con P25 quedaron
dentro de 5 puntos de la completa (tanda 17), pero nunca se probaron con clima.

## Hipótesis

Si una de esas variantes con clima rinde igual o mejor que la mínima con clima, el
modelo explicable puede ganar una variable útil sin perder la señal del clima.

## Qué se corre

La mínima + rezago 2 y la mínima + P25, cada una con las nueve variables de clima.
Referencias: la mínima con clima (tanda 22) y, como segunda lectura, la misma
variante sin clima (tanda 17).

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
