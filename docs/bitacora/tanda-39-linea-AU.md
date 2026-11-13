# Tanda 39, línea AU — Qué aprende la logística con clima

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **cerrada** el 10 de noviembre de 2026. Se corre sobre la base común del
> retroanálisis: `canonical.mode=approved`, calendario y departamentos de
> `parameters_retroanalisis.yml` sin tocar, `conjunto.csv` reportado.

## Hipótesis

Ninguna que decida algo. El informe necesita explicar qué hace el modelo: qué
variables pesan más y con qué signo, y si las del clima tienen el signo que la
biología del vector espera (más lluvia y más temperatura, más riesgo).

## Qué se corre

La logística sin clima y con clima, reentrenadas en el último origen evaluable de
cada horizonte (2024-11 en T+1 y 2024-10 en T+2) con toda la historia desde
2012-01, igual que en el retroanálisis. Se leen los coeficientes estandarizados
(log-odds por una desviación estándar de cada columna).

## Qué no decide

Es descriptiva. Los coeficientes de una logística con variables correlacionadas no
se leen como efectos causales.

## Resultado

Coeficientes estandarizados más grandes, en valor absoluto, en el último fold:

- Sin clima, T+1: `p75_h5_t1` -2.80, `total_notifications_count` +1.13, `total_notifications_count_lag2` +1.05, `total_notifications_count_lag1` +0.86, `dengue_notifications_count_lag2` -0.86, `total_notifications_count_lag3` +0.67, `p75_h5_t2` +0.66, `dengue_notifications_count_lag12` -0.48.
- Sin clima, T+2: `p75_h5_t2` -2.36, `p75_h5_t1` +1.40, `dengue_notifications_count_lag12` -0.67, `total_notifications_count` +0.63, `total_notifications_count_lag12` +0.58, `total_notifications_count_lag1` +0.55, `dengue_notifications_count_lag1` -0.33, `dengue_notifications_count_lag2` +0.24.
- Con clima, T+1: `p75_h5_t1` -2.88, `total_notifications_count` +1.01, `total_notifications_count_lag2` +1.00, `dengue_notifications_count_lag2` -0.81, `total_notifications_count_lag1` +0.71, `total_notifications_count_lag3` +0.60, `p75_h5_t2` +0.47, `dewpoint_mean_c_month_mean` +0.42.
- Con clima, T+2: `p75_h5_t2` -2.51, `p75_h5_t1` +1.33, `dengue_notifications_count_lag12` -0.61, `total_notifications_count` +0.53, `total_notifications_count_lag12` +0.51, `total_notifications_count_lag1` +0.44, `dengue_notifications_count_lag2` +0.31, `dewpoint_mean_c_month_mean` +0.24.

Variables de clima de la logística con clima:

| Variable de clima | T+1 | T+2 |
| --- | --- | --- |
| `dewpoint_mean_c_month_mean` | +0.42 | +0.24 |
| `temp_mean_c_month_mean` | -0.18 | -0.09 |
| `soil_water_l1_month_mean` | -0.17 | -0.17 |
| `wind_v_ms_month_mean` | -0.14 | -0.20 |
| `total_evaporation_mm_month_sum_ecmwf` | +0.12 | +0.10 |
| `solar_radiation_mj_m2_month_sum` | +0.10 | +0.03 |
| `surface_runoff_mm_month_sum` | -0.06 | -0.02 |
| `wind_u_ms_month_mean` | +0.03 | +0.09 |
| `rain_mm_month_sum` | +0.02 | -0.02 |

Lo que se lee:

- **El modelo es, sobre todo, el margen contra el umbral en escala log**: el P75 del
  mes objetivo entra con el coeficiente más grande y negativo (−2,4 a −2,9) y los
  conteos actuales y recientes con signo positivo. Es la resta de logaritmos que
  midió la tanda 11, y lo que explica la tanda 16.
- En T+1 pesan más los **conteos totales** que los de dengue, y los de dengue con
  rezago 2 entran con signo negativo: el modelo usa la diferencia entre total y
  dengue como señal.
- **Del clima, la variable que más pesa es el punto de rocío, con signo positivo**
  (+0,42 en T+1 y +0,24 en T+2): más humedad, más riesgo de inicio, que es lo que
  se espera para el vector. La lluvia del mes casi no pesa (±0,02); la humedad del
  suelo y la temperatura media entran con signo negativo una vez que el punto de
  rocío está en el modelo, algo que con variables tan correlacionadas no se puede
  leer por separado.
- Los coeficientes de clima son chicos frente a los del margen (0,4 frente a 2,9),
  coherente con un aporte de unos 2 puntos (tandas 15, 22 y 32).

Herramienta: `pipeline/tools/noche/coeficientes.py`.

## Corrección del 13 de noviembre

La lectura de arriba sobre «la diferencia entre total y dengue» se apoyaba en una
premisa equivocada: en el panel, las notificaciones totales son dengue más dengue
grave, así que esa diferencia es el dengue grave, no otros síndromes febriles. Ver la
corrección de la tanda 56.
