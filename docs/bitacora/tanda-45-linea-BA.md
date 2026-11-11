# Tanda 45, línea BA — La curva de presupuesto completa

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **cerrada** el 10 de noviembre de 2026. Se corre sobre la base común del
> retroanálisis: `canonical.mode=approved`, calendario y departamentos de
> `parameters_retroanalisis.yml` sin tocar, `conjunto.csv` reportado.

## Hipótesis

Ninguna. La sección 0.1 pide publicar siempre la curva además del punto de
operación. Esta tanda la da completa, con el presupuesto definido como en la
tanda 33, para saber desde qué volumen de alertas el modelo empieza a aportar en
cada horizonte.

## Qué se corre

`veredicto.py` con presupuestos de 2,5, 5, 7,5, 10, 12,5, 15, 20, 25 y 30 % de los
76 municipios por mes, para la logística sin clima y con clima.

## Qué no decide

El veredicto sigue siendo el del 10 % (tanda 33).

## Resultado

| Receta | Horizonte | Presupuesto | Alertas por mes (real) | Canal | Modelo | Diferencia (pp) | IC por bloques de mes | Barra |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| logistica_sin_clima | T+1 | 2.5 % | 2.2 | 113 | 107 | -0.9 | -2.8 a 0.8 | NO |
| logistica_sin_clima | T+1 | 5 % | 3.8 | 175 | 173 | -0.3 | -2.2 a 1.6 | NO |
| logistica_sin_clima | T+1 | 7.5 % | 7.1 | 264 | 274 | +1.6 | -1.2 a 4.5 | NO |
| logistica_sin_clima | T+1 | 10 % | 7.6 | 279 | 286 | +1.1 | -1.7 a 3.6 | NO |
| logistica_sin_clima | T+1 | 12.5 % | 9.4 | 321 | 331 | +1.6 | -1.4 a 4.4 | NO |
| logistica_sin_clima | T+1 | 15 % | 11.0 | 354 | 368 | +2.2 | -0.9 a 5.1 | NO |
| logistica_sin_clima | T+1 | 20 % | 15.0 | 401 | 428 | +4.2 | 1.2 a 7.2 | NO |
| logistica_sin_clima | T+1 | 25 % | 19.5 | 432 | 473 | +6.4 | 3.1 a 9.7 | CUMPLE |
| logistica_sin_clima | T+1 | 30 % | 22.8 | 446 | 507 | +9.5 | 6.1 a 12.9 | CUMPLE |
| logistica_sin_clima | T+2 | 2.5 % | 3.1 | 67 | 82 | +3.3 | 0.7 a 5.9 | NO |
| logistica_sin_clima | T+2 | 5 % | 3.8 | 83 | 99 | +3.5 | 0.7 a 6.8 | NO |
| logistica_sin_clima | T+2 | 7.5 % | 4.7 | 99 | 117 | +3.9 | 0.9 a 7.0 | NO |
| logistica_sin_clima | T+2 | 10 % | 7.8 | 152 | 179 | +5.9 | 2.2 a 9.6 | CUMPLE |
| logistica_sin_clima | T+2 | 12.5 % | 9.7 | 178 | 211 | +7.2 | 3.1 a 11.3 | CUMPLE |
| logistica_sin_clima | T+2 | 15 % | 11.2 | 196 | 232 | +7.8 | 3.9 a 11.8 | CUMPLE |
| logistica_sin_clima | T+2 | 20 % | 15.4 | 239 | 278 | +8.5 | 3.7 a 13.1 | CUMPLE |
| logistica_sin_clima | T+2 | 25 % | 19.7 | 276 | 313 | +8.1 | 3.1 a 12.6 | CUMPLE |
| logistica_sin_clima | T+2 | 30 % | 22.8 | 294 | 341 | +10.2 | 5.2 a 15.0 | CUMPLE |
| log_conclima | T+1 | 2.5 % | 2.2 | 113 | 111 | -0.3 | -1.9 a 1.2 | NO |
| log_conclima | T+1 | 5 % | 3.8 | 175 | 172 | -0.5 | -2.5 a 1.6 | NO |
| log_conclima | T+1 | 7.5 % | 7.1 | 264 | 287 | +3.6 | 0.6 a 6.4 | NO |
| log_conclima | T+1 | 10 % | 7.6 | 279 | 299 | +3.1 | 0.5 a 5.9 | NO |
| log_conclima | T+1 | 12.5 % | 9.4 | 321 | 343 | +3.4 | 0.6 a 6.2 | NO |
| log_conclima | T+1 | 15 % | 11.0 | 354 | 384 | +4.7 | 1.7 a 7.6 | NO |
| log_conclima | T+1 | 20 % | 15.0 | 401 | 438 | +5.8 | 3.0 a 8.6 | CUMPLE |
| log_conclima | T+1 | 25 % | 19.5 | 432 | 490 | +9.0 | 5.6 a 12.3 | CUMPLE |
| log_conclima | T+1 | 30 % | 22.8 | 446 | 514 | +10.6 | 7.2 a 13.9 | CUMPLE |
| log_conclima | T+2 | 2.5 % | 3.1 | 67 | 77 | +2.2 | -0.2 a 4.6 | NO |
| log_conclima | T+2 | 5 % | 3.8 | 83 | 91 | +1.7 | -1.1 a 4.8 | NO |
| log_conclima | T+2 | 7.5 % | 4.7 | 99 | 109 | +2.2 | -1.1 a 5.4 | NO |
| log_conclima | T+2 | 10 % | 7.8 | 152 | 185 | +7.2 | 3.3 a 11.1 | CUMPLE |
| log_conclima | T+2 | 12.5 % | 9.7 | 178 | 219 | +8.9 | 4.6 a 13.1 | CUMPLE |
| log_conclima | T+2 | 15 % | 11.2 | 196 | 238 | +9.2 | 4.6 a 13.5 | CUMPLE |
| log_conclima | T+2 | 20 % | 15.4 | 239 | 290 | +11.1 | 6.8 a 15.3 | CUMPLE |
| log_conclima | T+2 | 25 % | 19.7 | 276 | 319 | +9.4 | 4.6 a 14.2 | CUMPLE |
| log_conclima | T+2 | 30 % | 22.8 | 294 | 343 | +10.7 | 6.1 a 15.0 | CUMPLE |

- **T+2: el modelo pasa la barra desde el 10 %** (unas 8 alertas por mes) en las dos
  recetas, y la ventaja crece hasta unos 10 puntos al 30 %. Por debajo del 10 % gana
  algo (+2 a +4 pp), con IC sobre cero sin clima, pero sin llegar a 5.
- **T+1: hacen falta más alertas.** La logística con clima pasa la barra desde el
  **20 %** (15 alertas por mes, +5,8 pp) y la sin clima desde el **25 %** (19,5 por
  mes, +6,4 pp). Al 5 % o menos, el canal es igual o mejor.
- Nota: la f del canal se elige en una grilla de 0,05, así que a presupuestos bajos
  el número real de alertas se aleja del objetivo (por ejemplo, 7,1 por mes en lugar
  de 5,7 al 7,5 % en T+1). La columna de alertas reales es la que vale.

Para el informe: **a dos meses, el modelo supera al canal desde el presupuesto que
una secretaría puede atender; a un mes, solo si se aceptan unas 15 alertas por mes
o más.**
