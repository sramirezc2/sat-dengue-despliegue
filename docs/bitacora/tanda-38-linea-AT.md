# Tanda 38, línea AT — El canal como ranking, con cupo fijo por mes

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **cerrada** el 10 de noviembre de 2026. Se corre sobre la base común del
> retroanálisis: `canonical.mode=approved`, calendario y departamentos de
> `parameters_retroanalisis.yml` sin tocar, `conjunto.csv` reportado.

## Hipótesis

En la tanda 33 el canal condicionado alerta donde los casos pasan f × P75, así que
su número de alertas cambia mes a mes y el modelo copia ese reparto. Una secretaría
con un cupo fijo de 8 visitas por mes podría usar el canal de otra forma: ordenar
cada mes los municipios fuera de exceso por casos / P75 y visitar los 8 primeros.
Ese «canal como ranking» usa la misma información del canal y reparte el cupo
igual que el modelo. Si el modelo sigue ganando contra él, la ventaja no viene de
cómo se reparte el presupuesto entre meses.

## Qué se corre

Al 10 % de la sección 0, con cupo **exacto por mes** (round(0,10 × 76) = 8 alertas
por mes de origen, entre las filas fuera de exceso) para los dos métodos:

- canal como ranking: casos del origen / P75 del mes objetivo;
- modelo: su puntaje.

Para las cuatro logísticas de la tanda 33, T+1 y T+2, con el IC por bloques de mes.

## Qué decide

La misma barra de la sección 0 (5 puntos, cota inferior sobre cero), pero contra
este canal. Se reportan los dos veredictos, contra el condicionado (tanda 33) y
contra el ranking, según la regla 10.

## Resultado: el canal como ranking es más débil que el condicionado

Con 8 alertas fijas por mes (656 en T+1 y 648 en T+2):

| Receta | Horizonte | Alertas | Canal como ranking | Modelo | Diferencia (pp) | IC por bloques de mes | Carga canal → modelo | Barra 5 pp |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| logistica_sin_clima | T+1 | 656 | 273 | 297 | +3.7 | 0.9 a 6.6 | 9.38 → 8.79 | NO |
| logistica_sin_clima | T+2 | 648 | 147 | 190 | +9.4 | 5.4 a 13.1 | 12.39 → 11.33 | CUMPLE |
| log_conclima | T+1 | 656 | 273 | 308 | +5.5 | 2.7 a 8.1 | 9.38 → 8.53 | CUMPLE |
| log_conclima | T+2 | 648 | 147 | 192 | +9.8 | 5.9 a 13.5 | 12.39 → 11.28 | CUMPLE |
| log_minima | T+1 | 656 | 273 | 289 | +2.5 | -0.3 a 5.3 | 9.38 → 8.99 | NO |
| log_minima | T+2 | 648 | 147 | 188 | +8.9 | 5.2 a 12.4 | 12.39 → 11.38 | CUMPLE |
| logc_minima | T+1 | 656 | 273 | 301 | +4.4 | 2.0 a 6.7 | 9.38 → 8.70 | NO |
| logc_minima | T+2 | 648 | 147 | 184 | +8.1 | 4.1 a 11.8 | 12.39 → 11.48 | CUMPLE |

- **El canal como ranking es una línea base más débil** que el canal condicionado
  de la tanda 33: con algo más de alertas (656 frente a 621 en T+1) detecta menos
  inicios (273 frente a 279 en T+1; 147 frente a 152 en T+2). El umbral f × P75 con
  reparto variable entre meses es mejor que ordenar por casos / P75 con cupo fijo.
- Contra él, el modelo pasa la barra en **T+2 con las cuatro recetas** (+8,1 a
  +9,8 pp) y en **T+1 con la logística con clima** (+5,5 pp, IC 2,7 a 8,1).
- Como es la línea base más débil, **el veredicto que manda sigue siendo el de la
  tanda 33**, contra el condicionado. Esta tanda muestra que la ventaja del modelo
  no viene de copiar el reparto mensual del canal: con cupo fijo es mayor.

Herramienta: `pipeline/tools/noche/canal_ranking.py`.
