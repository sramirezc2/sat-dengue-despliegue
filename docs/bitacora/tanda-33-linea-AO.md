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

## Corrección del 10 de noviembre, 23:00: el primer cálculo usó mal el presupuesto

La primera versión de este resultado, publicada en esta misma rama minutos antes,
calculó los presupuestos como fracción de las **filas elegibles** (las que no
están en exceso, unas 4 080 por horizonte) y no de los **76 municipios por mes**
que fija la sección 0.1. Su «10 %» eran 315 alertas en T+1, unas 3,8 por mes: en
realidad era el 5 % de la sección 0. Esa versión concluía que al 10 % ninguna
receta pasaba la barra y que aplicaba la sección 0.4. **Esa conclusión era
incorrecta y se retira.** Lo que sigue es el cálculo corregido.

## Resultado: al 10 %, en T+2 las cuatro recetas pasan la barra; en T+1 ninguna

Presupuesto = fracción × 76 × meses de origen evaluados (82 en T+1 y 81 en T+2).
El canal condicionado usa la fracción f del P75 cuyo volumen queda más cerca del
objetivo; el modelo emite las mismas alertas por mes. Al 10 % son unas 7,6 a 7,8
alertas por mes, las «8 alertas al mes» de la sección 0.1.

| Receta | Horizonte | Presupuesto | f | Alertas (por mes) | Canal | Modelo | Diferencia (pp) | IC por bloques de mes | IC por municipio | Carga (dif.) | A | Barra 5 pp | C |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| logistica_sin_clima | T+1 | 5 % | 1.05 | 310 (3.8) | 175 | 173 | -0.3 | -2.2 a 1.6 | -2.8 a 2.2 | +0.05 | NO | NO | CUMPLE |
| logistica_sin_clima | T+1 | 10 % | 0.85 | 621 (7.6) | 279 | 286 | +1.1 | -1.4 a 3.7 | -2.3 a 4.7 | -0.17 | NO | NO | CUMPLE |
| logistica_sin_clima | T+1 | 20 % | 0.45 | 1230 (15.0) | 401 | 428 | +4.2 | 1.2 a 7.0 | -1.7 a 10.3 | -0.66 | CUMPLE | NO | CUMPLE |
| logistica_sin_clima | T+2 | 5 % | 1.3 | 308 (3.8) | 83 | 99 | +3.5 | 0.4 a 6.5 | 0.2 a 6.8 | -0.40 | CUMPLE | NO | CUMPLE |
| logistica_sin_clima | T+2 | 10 % | 0.95 | 632 (7.8) | 152 | 179 | +5.9 | 2.0 a 9.6 | 1.1 a 10.5 | -0.67 | CUMPLE | CUMPLE | CUMPLE |
| logistica_sin_clima | T+2 | 20 % | 0.45 | 1245 (15.4) | 239 | 278 | +8.5 | 3.7 a 13.1 | 1.3 a 15.7 | -0.96 | CUMPLE | CUMPLE | CUMPLE |
| log_conclima | T+1 | 5 % | 1.05 | 310 (3.8) | 175 | 172 | -0.5 | -2.5 a 1.4 | -3.6 a 2.8 | +0.07 | NO | NO | CUMPLE |
| log_conclima | T+1 | 10 % | 0.85 | 621 (7.6) | 279 | 299 | +3.1 | 0.3 a 5.9 | -0.8 a 7.2 | -0.49 | CUMPLE | NO | CUMPLE |
| log_conclima | T+1 | 20 % | 0.45 | 1230 (15.0) | 401 | 438 | +5.8 | 3.1 a 8.4 | 0.2 a 11.4 | -0.91 | CUMPLE | CUMPLE | CUMPLE |
| log_conclima | T+2 | 5 % | 1.3 | 308 (3.8) | 83 | 91 | +1.7 | -1.1 a 4.8 | -1.5 a 5.0 | -0.20 | NO | NO | CUMPLE |
| log_conclima | T+2 | 10 % | 0.95 | 632 (7.8) | 152 | 185 | +7.2 | 3.3 a 11.3 | 2.4 a 12.2 | -0.82 | CUMPLE | CUMPLE | CUMPLE |
| log_conclima | T+2 | 20 % | 0.45 | 1245 (15.4) | 239 | 290 | +11.1 | 6.8 a 15.3 | 3.9 a 18.3 | -1.26 | CUMPLE | CUMPLE | CUMPLE |
| log_minima | T+1 | 5 % | 1.05 | 310 (3.8) | 175 | 177 | +0.3 | -1.3 a 2.0 | -1.7 a 2.2 | -0.05 | NO | NO | CUMPLE |
| log_minima | T+1 | 10 % | 0.85 | 621 (7.6) | 279 | 286 | +1.1 | -1.9 a 3.7 | -2.2 a 4.2 | -0.17 | NO | NO | CUMPLE |
| log_minima | T+1 | 20 % | 0.45 | 1230 (15.0) | 401 | 415 | +2.2 | -1.6 a 5.6 | -3.9 a 8.3 | -0.34 | NO | NO | CUMPLE |
| log_minima | T+2 | 5 % | 1.3 | 308 (3.8) | 83 | 101 | +3.9 | 1.3 a 6.5 | 0.9 a 7.2 | -0.45 | CUMPLE | NO | CUMPLE |
| log_minima | T+2 | 10 % | 0.95 | 632 (7.8) | 152 | 182 | +6.5 | 2.2 a 10.5 | 1.7 a 11.5 | -0.74 | CUMPLE | CUMPLE | CUMPLE |
| log_minima | T+2 | 20 % | 0.45 | 1245 (15.4) | 239 | 273 | +7.4 | 2.6 a 12.0 | 0.7 a 14.8 | -0.84 | CUMPLE | CUMPLE | CUMPLE |
| logc_minima | T+1 | 5 % | 1.05 | 310 (3.8) | 175 | 178 | +0.5 | -0.9 a 2.2 | -2.7 a 3.6 | -0.07 | NO | NO | CUMPLE |
| logc_minima | T+1 | 10 % | 0.85 | 621 (7.6) | 279 | 299 | +3.1 | 0.8 a 5.6 | -0.3 a 7.0 | -0.49 | CUMPLE | NO | CUMPLE |
| logc_minima | T+1 | 20 % | 0.45 | 1230 (15.0) | 401 | 439 | +5.9 | 3.0 a 8.9 | 0.2 a 12.6 | -0.93 | CUMPLE | CUMPLE | CUMPLE |
| logc_minima | T+2 | 5 % | 1.3 | 308 (3.8) | 83 | 90 | +1.5 | -1.1 a 4.1 | -1.7 a 4.6 | -0.17 | NO | NO | CUMPLE |
| logc_minima | T+2 | 10 % | 0.95 | 632 (7.8) | 152 | 185 | +7.2 | 3.5 a 11.3 | 2.8 a 11.5 | -0.82 | CUMPLE | CUMPLE | CUMPLE |
| logc_minima | T+2 | 20 % | 0.45 | 1245 (15.4) | 239 | 281 | +9.2 | 4.6 a 13.7 | 2.6 a 16.1 | -1.04 | CUMPLE | CUMPLE | CUMPLE |

Veredicto al presupuesto de referencia del **10 %**:

- **T+2: las cuatro recetas cumplen A, la barra de 5 puntos y C.** La logística
  con clima y la mínima con clima quedan en **+7,2 pp (IC por bloques de mes 3,3 a
  11,3 y 3,5 a 11,3)**, la mínima en +6,5 (IC 2,2 a 10,5) y la sin clima en +5,9
  (IC 2,0 a 9,6). Todas bajan la carga de falsas alertas.
- **T+1: ninguna pasa la barra.** Con clima se cumple A (+3,1 pp, IC 0,3 a 5,9,
  y lo mismo la mínima con clima), sin clima no (+1,1, IC −1,4 a 3,7).
- B queda NO_EVALUABLE en la cohorte primaria, como fija la sección 0.

Al 5 % ninguna pasa la barra en ningún horizonte; al 20 % pasan todas en T+2 y,
en T+1, las dos con clima (+5,8 y +5,9 pp).

**Lectura:** la sección 0 fija que solo T+1 decide la pregunta primaria y que T+2
se lee aparte; esa jerarquía no se toca aquí. Con el criterio tal como está
escrito, **en T+2 los modelos superan la barra al presupuesto de referencia, y en
T+1 no**. El clima es lo que lleva a T+1 a cumplir A. Estas cifras salen de una
exploración con unas cuarenta comparaciones en la noche; son evidencia para
preinscribir un experimento registrado, no un veredicto de la fábrica.

Herramienta: `pipeline/tools/noche/veredicto.py` (corregida).

## Agregado: XGBoost del banco con cinco semillas, al 10 %

Para tener la comparación completa, el mismo veredicto al 10 % para el XGBoost del
banco con las cinco semillas de la tanda 14:

| Semilla | T+1: canal → modelo (pp, IC mes) | T+2: canal → modelo (pp, IC mes) | Barra en T+2 |
| --- | --- | --- | --- |
| 53 | 279 → 287 (+1.2, -1.4 a 3.9) | 152 → 174 (+4.8, 0.0 a 9.4) | NO |
| 7 | 279 → 275 (-0.6, -3.6 a 2.5) | 152 → 181 (+6.3, 2.0 a 10.9) | CUMPLE |
| 13 | 279 → 280 (+0.2, -2.7 a 3.1) | 152 → 173 (+4.6, 0.0 a 8.9) | NO |
| 29 | 279 → 277 (-0.3, -3.0 a 2.3) | 152 → 173 (+4.6, 0.4 a 9.4) | NO |
| 42 | 279 → 274 (-0.8, -3.3 a 1.9) | 152 → 167 (+3.3, -1.1 a 7.8) | NO |

En T+1 XGBoost queda en cero (media -0.1 pp); en T+2 en
**+4.7 pp de media (+3,3 a +6,3)**, y **solo una de las cinco
semillas pasa la barra**. Las cuatro logísticas la pasan en T+2 (+5,9 a +7,2) sin
depender de semillas, porque son deterministas. Al presupuesto de referencia la
logística es la familia que cumple.
