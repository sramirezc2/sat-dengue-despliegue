# Tanda 48, línea BD — El clima de los meses anteriores

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **preinscrita, sin correr.** Se corre sobre la base común del
> retroanálisis: `canonical.mode=approved`, calendario y departamentos de
> `parameters_retroanalisis.yml` sin tocar, `conjunto.csv` reportado.

## Origen

Se escribe después de ver las tandas 15, 22, 32 y 39: el clima del mes de origen
aporta poco y de forma consistente, sobre todo el punto de rocío. El panel no trae
rezagos del clima.

## Hipótesis

El mosquito tarda en responder al clima: la lluvia y la humedad de uno o dos meses
antes crean criaderos y aumentan la población del vector antes de que suban los
casos. Si es así, el clima rezagado debería aportar más que el del mes de origen,
sobre todo en T+1, donde ningún modelo llega a la barra.

## Qué se corre

Seis columnas derivadas (`clima_rezagos: true`): punto de rocío, lluvia y
temperatura de uno y dos meses antes del origen, calculadas por municipio sobre la
historia completa; todas conocidas en el mes de origen, sin fuga. Sobre la
logística sin clima, la logística con clima y la mínima con clima. Referencias: las
mismas recetas sin los rezagos. Requiere la opción, que va al PR #6.

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
