# Tanda 41, línea AW — Reglas desplegables: umbrales fijados con el año anterior

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **cerrada** el 10 de noviembre de 2026. Se corre sobre la base común del
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

## Resultado: la ventaja sobrevive a una regla desplegable

Años objetivo 2019 a 2024 (2018 se usa solo para fijar el umbral de 2019):

| Receta | Horizonte | Método | Alertas | Inicios | Detectados | Falsas por acierto |
| --- | --- | --- | --- | --- | --- | --- |
| log_conclima | T+1 | canal | 592 | 552 | 264 | 1.24 |
| log_conclima | T+1 | modelo | 586 | 552 | 279 | 1.10 |
| log_conclima | T+2 | canal | 601 | 398 | 141 | 3.26 |
| log_conclima | T+2 | modelo | 557 | 398 | 169 | 2.30 |
| logistica_sin_clima | T+1 | canal | 592 | 552 | 264 | 1.24 |
| logistica_sin_clima | T+1 | modelo | 605 | 552 | 276 | 1.19 |
| logistica_sin_clima | T+2 | canal | 601 | 398 | 141 | 3.26 |
| logistica_sin_clima | T+2 | modelo | 570 | 398 | 168 | 2.39 |

- **T+2: el modelo detecta más con menos alertas.** La logística con clima detecta
  **169 inicios con 557 alertas**, frente a 141 con 601 del canal: 28 más (7,0
  puntos de 398) con 44 alertas menos, y 2,3 falsas por acierto frente a 3,3. Sin
  clima, 168 con 570. Años a favor / en contra: con clima 5+ / 1−, sin clima 5+ / 0−.
- **T+1: con clima también**: 279 con 586 alertas frente a 264 con 592 (4+ / 2−).
  Sin clima, 276 con 605 alertas (4+ / 2−), un poco más de alertas.
- Ninguno de los dos métodos clava el 10 % el año siguiente, porque la frecuencia
  de casos cambia entre años; los dos se desvían de forma parecida (557 a 605
  alertas sobre unas 547 esperadas).

Lectura: la ventaja de la tanda 33 **no depende de igualar el presupuesto mes a
mes**. Con una regla que una secretaría podría fijar en enero, el modelo anticipa
más inicios con igual o menor número de alertas, sobre todo a dos meses.

Herramienta: `pipeline/tools/noche/reglas_umbral.py`.
