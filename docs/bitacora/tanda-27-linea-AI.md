# Tanda 27, línea AI — Un solo modelo con indicador de departamento

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **preinscrita, sin correr.** Se corre sobre la base común del
> retroanálisis: `canonical.mode=approved`, calendario y departamentos de
> `parameters_retroanalisis.yml` sin tocar, `conjunto.csv` reportado.

## Origen

Se escribe después de ver las tandas 25 y 26 y se declara así: el clima gana en
Meta con un modelo único y pierde esa ganancia con un modelo por departamento.

## Hipótesis

Un modelo único con un indicador de Tolima conserva lo que se aprende juntando
los dos departamentos y deja que cada uno tenga su propio nivel base de riesgo.
Si la diferencia entre departamentos es solo de nivel, el indicador debería
ayudar; si no ayuda, la diferencia está en otra parte.

## Qué se corre

Una columna derivada `depto_73` (1 en Tolima, 0 en Meta), al final de la matriz
(`variable_depto: true`), sobre la logística sin clima y sobre la logística con
clima. Referencias: las mismas recetas sin el indicador. Requiere la opción, por
PR a main.

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
