# Tanda 60, línea BP — La logística con clima en la reserva, por presupuesto y por departamento

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **cerrada** el 11 de noviembre de 2026. Se corre sobre la base común del
> retroanálisis: `canonical.mode=approved`, calendario y departamentos de
> `parameters_retroanalisis.yml` sin tocar, `conjunto.csv` reportado.

## Origen

La tanda 58 confirmó la logística con clima en T+2 al 10 % en la reserva 2023-2024.
Esta tanda no busca nada nuevo: describe esa confirmación para el informe.

## Qué se corre

Ningún modelo nuevo. Sobre la reserva 2023-2024, con la logística con clima: el
veredicto de la sección 0 al 5, 10, 15, 20 y 30 %, y la lectura por departamento al
10 %.

## Qué no decide

Es una lectura; el veredicto es el de la tanda 58. Con dos años de reserva, ningún
corte se interpreta solo.

## Resultado

Logística con clima, reserva 2023-2024 (224 inicios en T+1 y 147 en T+2):

| Horizonte | Presupuesto | Alertas por mes | Canal | Modelo | Diferencia (pp) | IC por bloques de mes | Barra |
| --- | --- | --- | --- | --- | --- | --- | --- |
| T+1 | 5 % | 3.8 | 59 | 58 | -0.4 | -3.6 a 2.2 | NO |
| T+1 | 10 % | 7.9 | 98 | 103 | +2.2 | -1.3 a 5.8 | NO |
| T+1 | 15 % | 11.3 | 129 | 136 | +3.1 | -1.8 a 8.0 | NO |
| T+1 | 20 % | 15.6 | 147 | 165 | +8.0 | 4.0 a 12.1 | CUMPLE |
| T+1 | 30 % | 23.2 | 166 | 191 | +11.2 | 7.1 a 15.2 | CUMPLE |
| T+2 | 5 % | 3.9 | 29 | 35 | +4.1 | -1.4 a 9.5 | NO |
| T+2 | 10 % | 8.7 | 57 | 70 | +8.8 | 1.4 a 16.3 | CUMPLE |
| T+2 | 15 % | 11.5 | 68 | 83 | +10.2 | 3.4 a 17.0 | CUMPLE |
| T+2 | 20 % | 15.5 | 85 | 98 | +8.8 | 2.0 a 15.6 | CUMPLE |
| T+2 | 30 % | 23.0 | 104 | 121 | +11.6 | 5.4 a 18.4 | CUMPLE |

Por departamento, al 10 %:

| Horizonte | Departamento | Inicios | Canal | Modelo |
| --- | --- | --- | --- | --- |
| T+1 | Meta | 89 | 52 | 52 |
| T+1 | Tolima | 135 | 46 | 51 |
| T+2 | Meta | 57 | 26 | 32 |
| T+2 | Tolima | 90 | 31 | 38 |

- **T+2 pasa la barra en la reserva desde el 10 % hasta el 30 %** (+8,8 a +11,6 pp),
  y gana en los dos departamentos (+6 en Meta y +7 en Tolima al 10 %). Por debajo
  del 10 % gana algo (+4,1 al 5 %) sin llegar a la barra.
- **T+1 pasa la barra en la reserva desde el 20 %** (+8,0 pp, IC 4,0 a 12,1, unas 15,6
  alertas por mes), lo mismo que la tanda 45 vio en el periodo completo. Al 10 % no
  (+2,2). En Meta, al 10 %, empata con el canal.
- Para el informe: en años que el modelo nunca vio para elegirse, **a dos meses supera
  al canal desde el presupuesto que una secretaría puede atender; a un mes, si se
  aceptan unas 15 alertas por mes.** Es una lectura de la confirmación de la tanda
  58, no una confirmación nueva: el corte del 20 % no estaba preinscrito como
  veredicto.
