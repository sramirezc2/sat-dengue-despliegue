# Tanda 24, línea AF — El mes como ciclo en la logística

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **cerrada** el 10 de noviembre de 2026. Se corre sobre la base común del
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

## Resultado parcial (la corrida se interrumpió)

La corrida se detuvo por falta de memoria en el equipo después de las dos primeras
recetas; las dos variantes con clima quedan sin correr. Sobre la logística sin
clima, al presupuesto del canal condicionado:

| | T+1 (347 de referencia) | T+2 (248 de referencia) |
| --- | --- | --- |
| Mes cíclico agregado | 350, +3 (IC −3 a 8) | 245, −3 (IC −9 a 3) |
| Mes cíclico en lugar del numérico | 351, +4 (IC −1 a 8) | 244, −4 (IC −10 a 1) |

**Sin efecto** sobre la logística sin clima: la forma del mes no cambia casi nada,
probablemente porque el canal ya trae la estacionalidad del municipio.

## Resultado completo: tampoco con clima

Las dos variantes con clima se corrieron después, de a una. Contra la logística
con clima (359 y 253): mes cíclico agregado +1 y −1; mes cíclico en lugar del
numérico −1 y −1. **Sin efecto** en las cuatro variantes. La forma del mes no
importa para la logística: la estacionalidad ya la trae el canal.

| T+1, 641 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| logc_mes | condicionado | 817 | 359 | 360 | +1 (-7 a 9) | +0.2 | 11.22 → 11.20 | 2+ / 2− |
| logc_mes | 5 % | 209 | 112 | 112 | +0 (-4 a 4) | +0.0 | 2.38 → 2.38 |  |
| logc_mes | 10 % | 406 | 194 | 194 | +0 (-9 a 9) | +0.0 | 5.19 → 5.19 |  |
| logc_mes | 20 % | 817 | 317 | 316 | -1 (-7 a 5) | -0.2 | 12.25 → 12.27 |  |
| logc_mes_solo | condicionado | 817 | 359 | 358 | -1 (-7 a 4) | -0.2 | 11.22 → 11.24 | 1+ / 2− |
| logc_mes_solo | 5 % | 209 | 112 | 113 | +1 (0 a 3) | +0.2 | 2.38 → 2.35 |  |
| logc_mes_solo | 10 % | 406 | 194 | 196 | +2 (-4 a 8) | +0.3 | 5.19 → 5.14 |  |
| logc_mes_solo | 20 % | 817 | 317 | 315 | -2 (-7 a 3) | -0.3 | 12.25 → 12.30 |  |

| T+2, 459 inicios | Presupuesto | Alertas | Referencia | Receta | Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| logc_mes | condicionado | 1158 | 253 | 252 | -1 (-9 a 7) | -0.2 | 22.39 → 22.41 | 2+ / 3− |
| logc_mes | 5 % | 207 | 65 | 64 | -1 (-8 a 5) | -0.2 | 3.51 → 3.54 |  |
| logc_mes | 10 % | 402 | 127 | 127 | +0 (-7 a 7) | +0.0 | 6.80 → 6.80 |  |
| logc_mes | 20 % | 809 | 211 | 215 | +4 (-3 a 11) | +0.9 | 14.79 → 14.70 |  |
| logc_mes_solo | condicionado | 1158 | 253 | 252 | -1 (-7 a 5) | -0.2 | 22.39 → 22.41 | 2+ / 3− |
| logc_mes_solo | 5 % | 207 | 65 | 68 | +3 (-1 a 7) | +0.7 | 3.51 → 3.44 |  |
| logc_mes_solo | 10 % | 402 | 127 | 129 | +2 (-4 a 8) | +0.4 | 6.80 → 6.75 |  |
| logc_mes_solo | 20 % | 809 | 211 | 219 | +8 (1 a 15) | +1.7 | 14.79 → 14.60 |  |
