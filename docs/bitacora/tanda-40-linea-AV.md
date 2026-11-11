# Tanda 40, línea AV — El punto de rocío como único clima

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **preinscrita, sin correr.** Se corre sobre la base común del
> retroanálisis: `canonical.mode=approved`, calendario y departamentos de
> `parameters_retroanalisis.yml` sin tocar, `conjunto.csv` reportado.

## Origen

Se escribe después de ver la tanda 39 y se declara así: el punto de rocío es la
variable de clima con mayor coeficiente. Elegir una variable por su coeficiente y
luego medirla sobre los mismos años es selección después de mirar; por eso esta
tanda **no puede declarar mejora sobre el clima completo**, solo si la versión de
una variable es equivalente.

## Hipótesis

Si casi todo el aporte del clima pasa por la humedad, una logística con solo el
punto de rocío rinde igual que con las nueve variables, y es más fácil de explicar
y de mantener.

## Qué se corre

La logística con clima y la mínima con clima, cada una con el punto de rocío como
única variable de clima. Referencias: las mismas recetas con las nueve variables.

## Qué métrica decide

Inicios detectados al presupuesto de alertas de cada línea base (canal P75,
condicionado y ajustado), sobre la base común y las mismas filas, igual que las
tandas 11 y 12. El brazo de referencia es `logistica_sin_clima.yml` corrido **en
la misma corrida**. Se publican también el resumen por año y la curva.

## Qué contaría como mejora, declarado antes de mirar

Al presupuesto del canal condicionado, por horizonte:

- **Equivalente** si queda dentro de ±5 puntos de la referencia; no se declara
  mejora aunque la supere, por la selección después de mirar.
- (Criterio general, que aquí no se aplica para mejora:) **Mejora** si el brazo suma al menos 5 puntos de inicios sobre la referencia
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
