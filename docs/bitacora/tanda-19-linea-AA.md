# Tanda 19, línea AA — Lectura por nivel de transmisión del año

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **cerrada** el 10 de noviembre de 2026. Se corre sobre la base común del
> retroanálisis: `canonical.mode=approved`, calendario y departamentos de
> `parameters_retroanalisis.yml` sin tocar, `conjunto.csv` reportado.

## Hipótesis

La ventaja del modelo sobre el canal no es igual todos los años: en años de
transmisión baja casi nadie gana. Si la ventaja se concentra en años de alta
transmisión, eso es parte del resultado y no debe quedar escondido en el
agregado (punto 7 de la regla de utilidad).

## Qué se corre

Ningún modelo nuevo. Sobre el `por_anio.csv` de las tandas 14 a 18, cada año se
clasifica **antes de mirar el desempeño** como alto o bajo según su número de
inicios evaluables: alto si está por encima de la mediana de los siete años, por
horizonte. Se reporta la diferencia contra el canal condicionado en cada grupo.

Aquí no hay mejora que declarar: es una lectura. Se reporta si la ventaja de
cada brazo es del mismo signo en los dos grupos o si depende de uno solo.

## Qué no decide

No cambia el veredicto de ninguna tanda ni la meta del contrato. Con siete años,
cada grupo tiene tres o cuatro; se declara así y no se concluye nada de un grupo
con menos de 30 inicios.

## Resultado

Lectura sobre el `por_anio.csv` de las tandas 14 a 17, contra el canal
condicionado al presupuesto de cada año (canal 323 en T+1 y 207 en T+2, como en
la tanda 11). Los años se clasificaron por sus inicios evaluables antes de mirar
el desempeño; con siete años, cada grupo tiene tres o cuatro.

**T+1.** Años altos (más de 89 inicios): 2019, 2023, 2024; bajos: 2018, 2020, 2021, 2022.

| Receta | Altos: canal → modelo (inicios) | Diferencia | Bajos: canal → modelo (inicios) | Diferencia |
| --- | --- | --- | --- | --- |
| logistica_sin_clima | 188 → 201 (342) | +13 | 135 → 146 (299) | +11 |
| log_conclima | 188 → 207 (342) | +19 | 135 → 152 (299) | +17 |
| log_minima | 188 → 209 (342) | +21 | 135 → 130 (299) | -5 |
| logistica_g | 188 → 203 (342) | +15 | 135 → 146 (299) | +11 |
| xgb_banco_s53 | 188 → 203 (342) | +15 | 135 → 139 (299) | +4 |
| xgb_banco_s7 | 188 → 195 (342) | +7 | 135 → 133 (299) | -2 |
| xgb_banco_s13 | 188 → 195 (342) | +7 | 135 → 136 (299) | +1 |
| xgb_banco_s29 | 188 → 202 (342) | +14 | 135 → 137 (299) | +2 |
| xgb_banco_s42 | 188 → 195 (342) | +7 | 135 → 130 (299) | -5 |

**T+2.** Años altos (más de 66 inicios): 2019, 2022, 2023; bajos: 2018, 2020, 2021, 2024.

| Receta | Altos: canal → modelo (inicios) | Diferencia | Bajos: canal → modelo (inicios) | Diferencia |
| --- | --- | --- | --- | --- |
| logistica_sin_clima | 85 → 97 (230) | +12 | 122 → 151 (229) | +29 |
| log_conclima | 85 → 100 (230) | +15 | 122 → 153 (229) | +31 |
| log_minima | 85 → 97 (230) | +12 | 122 → 148 (229) | +26 |
| logistica_g | 85 → 99 (230) | +14 | 122 → 151 (229) | +29 |
| xgb_banco_s53 | 85 → 96 (230) | +11 | 122 → 151 (229) | +29 |
| xgb_banco_s7 | 85 → 94 (230) | +9 | 122 → 149 (229) | +27 |
| xgb_banco_s13 | 85 → 93 (230) | +8 | 122 → 147 (229) | +25 |
| xgb_banco_s29 | 85 → 98 (230) | +13 | 122 → 144 (229) | +22 |
| xgb_banco_s42 | 85 → 90 (230) | +5 | 122 → 144 (229) | +22 |

Lo que se lee:

- **En T+1 la ventaja de la logística no depende del grupo**: +13 en años altos y
  +11 en bajos, y con clima +19 y +17. La **mínima solo gana en años altos** (+21
  y −5), y lo mismo XGBoost en todas sus semillas: su ventaja en T+1 está casi
  entera en los años altos.
- **En T+2 la ventaja es mayor en los años bajos** (+29 frente a +12 con la
  logística sin clima), y así en todas las recetas. Es el canal el que se cae en
  esos años: detecta 122 de 229 inicios en años bajos y 85 de 230 en altos.
- Todos los grupos tienen más de 30 inicios, así que la regla 4 no impide leerlos,
  pero son tres o cuatro años por grupo y no sostienen una conclusión por sí solos.

Para el informe: la ventaja de la logística en T+1 no está escondida en un tipo
de año, pero la de la versión mínima y la de XGBoost sí.
