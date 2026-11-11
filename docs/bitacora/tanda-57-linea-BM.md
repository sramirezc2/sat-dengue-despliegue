# Tanda 57, línea BM — Los cinco vecinos más cercanos

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **preinscrita, sin correr.** Se corre sobre la base común del
> retroanálisis: `canonical.mode=approved`, calendario y departamentos de
> `parameters_retroanalisis.yml` sin tocar, `conjunto.csv` reportado.

## Origen y relación con la línea H

La tanda 46 midió que la mitad de los inicios que no anticipa nadie arranca con
cero casos. La tanda 51 (línea BG, de Stevan) midió la presión del departamento
entero y no aportó. Esta tanda mide una escala más fina: los cinco municipios más
cercanos por centroide DIVIPOLA. Se avisó a Stevan porque es vecina de su línea.

## Hipótesis

Para un municipio con pocos o cero casos, lo que pasa en sus vecinos inmediatos
anuncia un brote mejor que el promedio del departamento. Debería verse sobre todo
en T+1 y en los inicios desde cero casos.

## Qué se corre

`log_conclima_vecinos.yml`: la logística con clima más el bloque
`variables_vecinos` (`domain/vecinos.py`: casos y exceso de los 5 vecinos más
cercanos dentro del panel, sin el propio, y su cambio mensual), PR a main.
Referencia: la logística con clima. Se reporta el veredicto al 10 % y, como lectura,
cuántos de los inicios desde cero casos pasa a anticipar.

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
