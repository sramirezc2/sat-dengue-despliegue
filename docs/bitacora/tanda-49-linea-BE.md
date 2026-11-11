# Tanda 49, línea BE — El punto de rocío distinto en Meta

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **cerrada** el 11 de noviembre de 2026. Se corre sobre la base común del
> retroanálisis: `canonical.mode=approved`, calendario y departamentos de
> `parameters_retroanalisis.yml` sin tocar, `conjunto.csv` reportado.

## Origen

Se escribe después de ver las tandas 25, 26 y 39 y se declara así: el clima gana en
Meta y no en Tolima, solo con un modelo único, y su variable principal es el punto
de rocío.

## Hipótesis

Si la humedad pesa más en Meta (Llanos Orientales) que en Tolima (valle del
Magdalena), un modelo único con un término propio del punto de rocío en Meta
debería aprovecharlo mejor, sin perder lo que se aprende juntando los dos.

## Qué se corre

Una columna derivada `rocio_x_meta` (`rocio_meta: true`): el punto de rocío del mes
de origen en los municipios de Meta y cero en Tolima, al final de la matriz. Sobre
la logística con clima y la mínima con clima; referencias: las mismas sin la
interacción. Es una interacción, una familia que se cerró en general antes; se
reabre solo para esta, por el mecanismo de la tanda 25.

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

Contra la logística con clima, el punto de rocío × Meta queda en −4 y −1; contra la
mínima con clima, en −2 y −1 (tablas completas en la tanda 48, misma corrida). El
modelo único ya usa el clima donde sirve; un término propio para Meta no agrega.
