# Tanda 16, línea X — Regularización y escala de la logística

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **preinscrita, sin correr.** Se corre sobre la base común del
> retroanálisis: `canonical.mode=approved`, calendario y departamentos de
> `parameters_retroanalisis.yml` sin tocar, `conjunto.csv` reportado.

## Hipótesis

Dos preguntas sobre el mismo modelo. Primera: la regularización por defecto
(C = 1) no se eligió; si el resultado depende mucho de C, la logística está mal
afinada. Segunda: la tanda 11 midió que la escala log1p arma el margen G por
dentro del modelo. Si es así, quitar log1p debería empeorar la logística, y
agregar el bloque G sin log1p debería recuperar lo perdido.

## Qué se corre

- C = 0,01, 0,1, 10 y 100 (`log_C*.yml`).
- Sin log1p (`log_sin_log1p.yml`).
- Sin log1p y con el bloque G (`log_sin_log1p_g.yml`).

Para C, la mejora tiene que aparecer en un valor y no ser un pico aislado: se
reporta toda la grilla.

**Predicción del mecanismo, declarada antes:** sin log1p pierde inicios, y con G
los recupera en buena parte. Si sin log1p no pierde nada, el mecanismo de la
tanda 11 no explica por qué G no aporta.

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
