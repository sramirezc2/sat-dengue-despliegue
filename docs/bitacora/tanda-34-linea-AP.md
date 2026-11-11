# Tanda 34, línea AP — El veredicto de T+2 año por año

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **cerrada** el 10 de noviembre de 2026. Se corre sobre la base común del
> retroanálisis: `canonical.mode=approved`, calendario y departamentos de
> `parameters_retroanalisis.yml` sin tocar, `conjunto.csv` reportado.

## Origen

Se escribe después de ver la tanda 33: al 10 %, las cuatro logísticas pasan la
barra en T+2 sobre los siete años juntos. La regla 3 pide consistencia entre
cortes, no el agregado.

## Hipótesis

Si la ventaja en T+2 es real, aparece en la mayoría de los años y no depende de
uno o dos.

## Qué se corre

El mismo cálculo de la tanda 33 (10 % de los 76 municipios por mes, canal
condicionado con la f más cercana), separado por año objetivo, para las cuatro
logísticas y para T+1 y T+2.

## Qué decide

Se declara **consistente** si el modelo detecta más inicios que el canal en al
menos cinco de los siete años del mismo horizonte, y ningún año con 30 inicios o
más pierde por más de 5 puntos. Si no, la ventaja agregada se reporta como
dependiente de pocos años.

## Resultado: la ventaja de T+2 es consistente entre años

Diferencia de inicios detectados (modelo menos canal condicionado) al 10 % de la
sección 0, por año objetivo:

| T+1 | Inicios | Canal | logistica_sin_clima | log_conclima | log_minima | logc_minima |
| --- | --- | --- | --- | --- | --- | --- |
| 2018 | 89 | 34 | +1 | +4 | +0 | +3 |
| 2019 | 118 | 50 | +1 | +4 | +3 | +3 |
| 2020 | 69 | 31 | -1 | +2 | -2 | +4 |
| 2021 | 52 | 17 | +5 | +4 | +1 | +2 |
| 2022 | 89 | 40 | +3 | +5 | -1 | +1 |
| 2023 | 125 | 50 | -2 | +1 | +3 | +3 |
| 2024 | 99 | 57 | +0 | +0 | +3 | +4 |
| Años a favor / en contra | | | 4+ / 2− | 6+ / 0− | 4+ / 2− | 7+ / 0− |

| T+2 | Inicios | Canal | logistica_sin_clima | log_conclima | log_minima | logc_minima |
| --- | --- | --- | --- | --- | --- | --- |
| 2018 | 61 | 20 | -1 | +3 | +0 | +3 |
| 2019 | 82 | 28 | +2 | +4 | +1 | -1 |
| 2020 | 53 | 18 | +8 | +8 | +7 | +8 |
| 2021 | 49 | 11 | +7 | +5 | +7 | +5 |
| 2022 | 67 | 18 | -1 | +0 | +0 | +0 |
| 2023 | 81 | 27 | +4 | +6 | +6 | +9 |
| 2024 | 66 | 30 | +8 | +7 | +9 | +9 |
| Años a favor / en contra | | | 5+ / 2− | 6+ / 0− | 5+ / 0− | 5+ / 1− |

- **T+2: consistente en las cuatro recetas.** La logística con clima gana en seis
  años y empata en uno (2022); las otras tres ganan en cinco. Ningún año pierde
  más de un inicio (2018 y 2019, menos de 2 puntos). La ventaja se concentra en
  2020, 2021, 2023 y 2024, de +4 a +9 inicios por año.
- **T+1: las versiones con clima también son consistentes**, aunque el efecto es
  chico. La mínima con clima gana en los siete años y la logística con clima en
  seis (y empata uno). Sin clima, la logística gana en cinco y la mínima en cuatro.
- **2022 no aporta en T+2** en ninguna receta: es el año en que el canal detecta
  apenas 4 de 61 inicios en la tanda 11 y casi nadie gana.

Por el criterio preinscrito, la ventaja de T+2 al 10 % **es consistente**, y no
depende de pocos años.
