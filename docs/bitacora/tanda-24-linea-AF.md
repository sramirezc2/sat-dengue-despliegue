# Tanda 24, línea AF — El mes como ciclo en la logística

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **preinscrita, sin correr.** Se corre sobre la base común del
> retroanálisis: `canonical.mode=approved`, calendario y departamentos de
> `parameters_retroanalisis.yml` sin tocar, `conjunto.csv` reportado.

## Hipótesis

La logística recibe `month_of_year` como un número del 1 al 12. Para un modelo
lineal eso obliga a que el riesgo suba o baje de forma monótona a lo largo del
año, y deja a diciembre y enero en extremos opuestos. XGBoost no tiene ese
problema porque corta el mes en tramos. Codificar el mes como ciclo, con su seno
y su coseno, le permite a la logística un pico estacional en cualquier época.

## Qué se corre

Dos columnas derivadas, `mes_sin` y `mes_cos`, calculadas del mes de origen en la
preparación (`variables_mes: true`), sin tocar la tabla canónica:

- logística sin clima con el mes cíclico agregado, y con el mes cíclico en lugar
  del numérico;
- lo mismo sobre la logística con clima.

Referencias: la logística sin clima para las dos primeras y la logística con
clima para las otras dos. Requiere la opción `variables_mes`, por PR a main.

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
