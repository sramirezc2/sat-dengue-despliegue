# Tanda 33, línea AO — Veredicto de la sección 0 para las mejores recetas

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **cerrada** el 10 de noviembre de 2026. Se corre sobre la base común del
> retroanálisis: `canonical.mode=approved`, calendario y departamentos de
> `parameters_retroanalisis.yml` sin tocar, `conjunto.csv` reportado.

## Hipótesis

Ninguna. Es la aplicación del criterio de la sección 0 tal como está escrito, a
las recetas que mejor quedaron en la noche: la logística sin clima, la logística
con clima, la mínima y la mínima con clima.

## Qué se corre

Para cada receta y horizonte, contra el canal condicionado al presupuesto de
referencia del **10 %** y, como curva, al 5 y al 20 %: el canal usa la fracción
del P75 cuyo número de alertas queda más cerca del presupuesto, y el modelo emite
las mismas alertas por mes. Se reportan A (IC por bloques de mes que excluye el
cero), la barra de 5 puntos con la cota inferior sobre cero, C (carga de falsas
alertas por 100 municipio-mes con su cota superior) y, como apoyo, el IC por
municipio. B queda NO_EVALUABLE en la cohorte primaria, como dice la sección 0.

## Qué decide

El veredicto se emite **al 10 %**. Lo demás es curva.

## Resultado: al 10 % ninguna receta pasa la barra; aplica la sección 0.4

El canal condicionado usa la fracción del P75 cuyo volumen queda más cerca del
presupuesto: al 10 % es f = 1,0, el P75 completo (315 alertas en T+1 y 378 en
T+2, las mismas de la tanda 11). Sobre 641 y 459 inicios.

| Receta | Horizonte | Presupuesto | Alertas | Canal | Modelo | Diferencia (pp) | IC por bloques de mes | IC por municipio | Carga (dif.) | A | Barra 5 pp | C |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| logistica_sin_clima | T+1 | 5 % | 213 | 127 | 126 | -0.2 | -1.9 a 1.6 | -2.0 a 1.9 | +0.02 | NO | NO | CUMPLE |
| logistica_sin_clima | T+1 | 10 % | 315 | 177 | 176 | -0.2 | -2.0 a 1.9 | -2.8 a 2.5 | +0.02 | NO | NO | CUMPLE |
| logistica_sin_clima | T+1 | 20 % | 857 | 343 | 357 | +2.2 | -0.9 a 5.1 | -2.0 a 6.7 | -0.34 | NO | NO | CUMPLE |
| logistica_sin_clima | T+2 | 5 % | 249 | 67 | 82 | +3.3 | 0.7 a 6.1 | 0.2 a 6.3 | -0.37 | CUMPLE | NO | CUMPLE |
| logistica_sin_clima | T+2 | 10 % | 378 | 99 | 117 | +3.9 | 0.9 a 7.0 | -0.2 a 7.8 | -0.45 | CUMPLE | NO | CUMPLE |
| logistica_sin_clima | T+2 | 20 % | 786 | 178 | 211 | +7.2 | 3.3 a 11.1 | 2.0 a 12.2 | -0.82 | CUMPLE | CUMPLE | CUMPLE |
| log_conclima | T+1 | 5 % | 213 | 127 | 126 | -0.2 | -1.7 a 1.3 | -2.7 a 2.3 | +0.02 | NO | NO | CUMPLE |
| log_conclima | T+1 | 10 % | 315 | 177 | 174 | -0.5 | -2.5 a 1.6 | -3.6 a 3.0 | +0.07 | NO | NO | CUMPLE |
| log_conclima | T+1 | 20 % | 857 | 343 | 371 | +4.4 | 1.1 a 7.3 | 0.5 a 8.6 | -0.69 | CUMPLE | NO | CUMPLE |
| log_conclima | T+2 | 5 % | 249 | 67 | 77 | +2.2 | 0.0 a 4.4 | -0.7 a 5.0 | -0.25 | NO | NO | CUMPLE |
| log_conclima | T+2 | 10 % | 378 | 99 | 109 | +2.2 | -0.9 a 5.2 | -1.7 a 5.9 | -0.25 | NO | NO | CUMPLE |
| log_conclima | T+2 | 20 % | 786 | 178 | 219 | +8.9 | 4.6 a 13.1 | 3.5 a 14.6 | -1.01 | CUMPLE | CUMPLE | CUMPLE |
| log_minima | T+1 | 5 % | 213 | 127 | 128 | +0.2 | -1.2 a 1.4 | -1.9 a 2.2 | -0.02 | NO | NO | CUMPLE |
| log_minima | T+1 | 10 % | 315 | 177 | 179 | +0.3 | -1.2 a 1.9 | -1.7 a 2.3 | -0.05 | NO | NO | CUMPLE |
| log_minima | T+1 | 20 % | 857 | 343 | 352 | +1.4 | -1.9 a 4.7 | -3.6 a 6.7 | -0.22 | NO | NO | CUMPLE |
| log_minima | T+2 | 5 % | 249 | 67 | 88 | +4.6 | 2.4 a 7.0 | 1.7 a 7.6 | -0.52 | CUMPLE | NO | CUMPLE |
| log_minima | T+2 | 10 % | 378 | 99 | 119 | +4.4 | 1.3 a 7.4 | -0.2 a 8.5 | -0.49 | CUMPLE | NO | CUMPLE |
| log_minima | T+2 | 20 % | 786 | 178 | 210 | +7.0 | 2.8 a 10.7 | 2.0 a 12.4 | -0.79 | CUMPLE | CUMPLE | CUMPLE |
| logc_minima | T+1 | 5 % | 213 | 127 | 128 | +0.2 | -1.1 a 1.4 | -2.7 a 3.0 | -0.02 | NO | NO | CUMPLE |
| logc_minima | T+1 | 10 % | 315 | 177 | 180 | +0.5 | -1.1 a 2.0 | -2.8 a 3.9 | -0.07 | NO | NO | CUMPLE |
| logc_minima | T+1 | 20 % | 857 | 343 | 375 | +5.0 | 2.2 a 8.0 | 0.5 a 9.8 | -0.78 | CUMPLE | NO | CUMPLE |
| logc_minima | T+2 | 5 % | 249 | 67 | 77 | +2.2 | -0.2 a 4.4 | -0.7 a 5.2 | -0.25 | NO | NO | CUMPLE |
| logc_minima | T+2 | 10 % | 378 | 99 | 107 | +1.7 | -1.3 a 4.8 | -1.7 a 5.2 | -0.20 | NO | NO | CUMPLE |
| logc_minima | T+2 | 20 % | 786 | 178 | 212 | +7.4 | 3.3 a 12.0 | 2.4 a 12.6 | -0.84 | CUMPLE | CUMPLE | CUMPLE |

Veredicto al presupuesto de referencia del **10 %**:

- **T+1: ninguna receta supera al canal condicionado.** Las cuatro quedan entre
  −0,5 y +0,5 puntos. A no se cumple en ninguna.
- **T+2: A se cumple para la logística sin clima (+3,9 pp, IC por mes 0,9 a 7,0)
  y para la mínima (+4,4 pp, IC 1,3 a 7,4)**, pero **ninguna llega a la barra de 5
  puntos**. Las versiones con clima quedan por debajo en T+2 (+2,2 y +1,7) y no
  cumplen A.
- **C se cumple en todas**: el modelo nunca aumenta la carga de falsas alertas;
  en T+2 la reduce.
- B queda NO_EVALUABLE, como fija la sección 0.

Fuera del presupuesto de referencia, al 20 %, las cuatro pasan la barra en T+2
(+7,0 a +8,9 pp, con la cota inferior entre 2,8 y 4,6), y la mínima con clima
llega a +5,0 en T+1 (IC por mes 2,2 a 8,0). Esa es la curva, no el veredicto.

**Conclusión según lo preinscrito:** al presupuesto que una secretaría puede
atender, ningún modelo supera al canal condicionado lo suficiente para
justificar operarlo. Es el resultado que la sección 0.4 describe: el camino corto
es ajustar y condicionar el canal. El modelo empieza a aportar en T+2 cuando se
aceptan más alertas.

Herramienta: `pipeline/tools/noche/veredicto.py`.
