# Tanda 38, línea AT — El canal como ranking, con cupo fijo por mes

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **preinscrita, sin correr.** Se corre sobre la base común del
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
