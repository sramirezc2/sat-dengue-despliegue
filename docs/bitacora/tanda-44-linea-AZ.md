# Tanda 44, línea AZ — Todas las recetas de la noche al presupuesto de referencia

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **preinscrita, sin correr.** Se corre sobre la base común del
> retroanálisis: `canonical.mode=approved`, calendario y departamentos de
> `parameters_retroanalisis.yml` sin tocar, `conjunto.csv` reportado.

## Hipótesis

Ninguna. Es una tabla de referencia para el informe: el veredicto de la sección 0
al 10 % (tanda 33) para todas las recetas corridas sobre la base común esta noche,
con la regla 3.3 de reportar todas las configuraciones probadas y no solo las que
funcionaron.

## Qué se corre

`tools/noche/veredicto.py` sobre las predicciones de las tandas 14 a 26, una fila
por receta y horizonte al 10 %.

## Qué no decide

Nada nuevo. Con unas treinta recetas, que alguna pase la barra por azar es
esperable; la tabla no sirve para elegir la mejor, sino para ver el conjunto.
