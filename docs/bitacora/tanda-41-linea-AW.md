# Tanda 41, línea AW — Reglas desplegables: umbrales fijados con el año anterior

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **preinscrita, sin correr.** Se corre sobre la base común del
> retroanálisis: `canonical.mode=approved`, calendario y departamentos de
> `parameters_retroanalisis.yml` sin tocar, `conjunto.csv` reportado.

## Hipótesis

Las tandas 33 a 38 obligan a modelo y canal a emitir el mismo número de alertas
por mes, lo que exige conocer el presupuesto del canal en cada mes. Una secretaría
necesita una regla que se fije antes del año: un umbral. Si cada método fija su
umbral con el año anterior para emitir el 10 % y lo aplica tal cual el año
siguiente (regla 4.2), el número de alertas realizado cambia, y lo que importa es
cuántos inicios detecta cada uno con cuántas alertas.

## Qué se corre

Ningún modelo nuevo. Para cada año objetivo de 2019 a 2024:

- **canal**: la fracción f del P75 (en la grilla de siempre) cuyo canal
  condicionado emitió en el año anterior el número de alertas más cercano al 10 %
  de 76 × 12;
- **modelo**: el umbral de probabilidad que en el año anterior dio ese mismo 10 %.

Cada regla se aplica tal cual al año siguiente. Se reportan alertas realizadas,
inicios detectados y carga, por año y en total, para la logística sin clima y con
clima, T+1 y T+2.

## Qué decide

Si el modelo detecta más inicios con un número de alertas igual o menor, la
ventaja sobrevive a una regla desplegable. Si para detectar más emite muchas más
alertas, la ventaja de la tanda 33 dependía de igualar el presupuesto por mes.
