# Tanda 44, línea AZ — Todas las recetas de la noche al presupuesto de referencia

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **cerrada** el 10 de noviembre de 2026. Se corre sobre la base común del
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

## Resultado

Al 10 % de la sección 0, contra el canal condicionado, ordenadas por T+2 (36
recetas; todas cumplen C):

| Receta | T+1 (pp) | IC mes T+1 | A T+1 | T+2 (pp) | IC mes T+2 | Barra T+2 |
| --- | --- | --- | --- | --- | --- | --- |
| logc_mes | +3.7 | 0.9 a 6.6 | CUMPLE | +8.3 | 4.6 a 11.8 | CUMPLE |
| log_minima_lag2 | +0.9 | -2.2 a 3.7 | NO | +7.2 | 3.3 a 11.1 | CUMPLE |
| log_conclima | +3.1 | 0.2 a 5.8 | CUMPLE | +7.2 | 3.3 a 11.3 | CUMPLE |
| logc_C10 | +3.1 | 0.6 a 5.6 | CUMPLE | +7.2 | 3.1 a 10.7 | CUMPLE |
| logc_minima | +3.1 | 0.6 a 5.5 | CUMPLE | +7.2 | 3.5 a 10.9 | CUMPLE |
| logc_mes_solo | +3.6 | 0.9 a 6.2 | CUMPLE | +7.2 | 3.9 a 10.7 | CUMPLE |
| log_mes | +1.6 | -1.2 a 4.4 | NO | +7.0 | 3.1 a 10.7 | CUMPLE |
| log_minima_p25 | +1.6 | -1.2 a 4.4 | NO | +7.0 | 3.3 a 11.1 | CUMPLE |
| log_C100 | +1.9 | -0.6 a 4.2 | NO | +6.5 | 2.6 a 10.7 | CUMPLE |
| logc_log1p_lluvia | +3.6 | 0.9 a 6.2 | CUMPLE | +6.5 | 2.6 a 10.5 | CUMPLE |
| log_minima | +1.1 | -1.6 a 3.9 | NO | +6.5 | 2.4 a 10.7 | CUMPLE |
| log_C10 | +1.2 | -1.4 a 3.7 | NO | +6.5 | 2.4 a 10.7 | CUMPLE |
| xgb_banco_s7 | -0.6 | -3.6 a 2.0 | NO | +6.3 | 1.5 a 10.7 | CUMPLE |
| logistica_g | +0.9 | -1.7 a 3.6 | NO | +6.3 | 2.4 a 10.0 | CUMPLE |
| log_minima_total | +1.4 | -1.4 a 4.1 | NO | +6.3 | 2.2 a 10.5 | CUMPLE |
| logc_lluvia_temp | +3.3 | 0.6 a 5.8 | CUMPLE | +6.3 | 2.2 a 10.0 | CUMPLE |
| log_mes_solo | +1.4 | -1.2 a 4.2 | NO | +6.1 | 2.4 a 9.8 | CUMPLE |
| logistica_sin_clima | +1.1 | -1.6 a 3.7 | NO | +5.9 | 2.4 a 9.4 | CUMPLE |
| logc_sin_viento | +3.3 | 0.6 a 5.9 | CUMPLE | +5.9 | 2.2 a 9.8 | CUMPLE |
| dep_con_clima | +1.2 | -1.4 a 3.9 | NO | +5.9 | 2.0 a 10.0 | CUMPLE |
| log_C0p1 | +1.2 | -1.4 a 3.9 | NO | +5.7 | 2.0 a 9.4 | CUMPLE |
| xgb_d2 | +2.3 | 0.0 a 5.0 | NO | +5.7 | 1.7 a 9.6 | CUMPLE |
| log_canal_dengue | +1.6 | -1.4 a 4.4 | NO | +5.4 | 1.5 a 9.6 | CUMPLE |
| xgb_d3_r150 | +1.7 | -0.8 a 4.2 | NO | +5.0 | 0.7 a 9.6 | CUMPLE |
| xgb_sinclima | +1.4 | -1.2 a 3.9 | NO | +5.0 | 0.7 a 9.6 | CUMPLE |
| xgb_banco_s53 | +1.2 | -1.4 a 3.9 | NO | +4.8 | 0.4 a 9.6 | NO |
| xgb_banco_s13 | +0.2 | -2.7 a 3.0 | NO | +4.6 | 0.2 a 8.9 | NO |
| xgb_banco_s29 | -0.3 | -2.8 a 2.3 | NO | +4.6 | 0.2 a 9.4 | NO |
| xgb_eta002_r600 | +0.8 | -1.9 a 3.4 | NO | +4.4 | 0.2 a 8.5 | NO |
| dep_sin_clima | +0.9 | -1.7 a 3.6 | NO | +4.1 | 0.4 a 7.8 | NO |
| xgb_banco_s42 | -0.8 | -3.3 a 1.7 | NO | +3.3 | -0.9 a 7.2 | NO |
| xgb_d6 | -2.2 | -5.0 a 0.5 | NO | +3.1 | -1.3 a 7.8 | NO |
| log_sin_log1p_g | +0.3 | -2.0 a 2.5 | NO | +3.1 | -1.1 a 7.2 | NO |
| log_C0p01 | -2.3 | -5.1 a 0.5 | NO | +2.4 | -1.5 a 6.3 | NO |
| xgb_eta01 | -0.9 | -3.9 a 2.0 | NO | +2.4 | -1.7 a 6.8 | NO |
| log_sin_log1p | -3.6 | -6.1 a -1.4 | NO | +0.2 | -2.8 a 3.3 | NO |

- **T+2: 25 de 36 recetas pasan la barra.** Pasan **todas las
  logísticas con log1p y C ≥ 0,1**, con o sin clima, mínimas o completas, con o sin
  G, con mes numérico o cíclico. No pasan: cuatro de las cinco semillas del XGBoost
  del banco, XGBoost con profundidad 6 o eta alto, la logística sin log1p, la de
  C = 0,01 y el modelo por departamento sin clima. El resultado de T+2 no depende
  de una receta: es de la familia logística en escala log.
- **T+1: ninguna receta pasa la barra.** Las mejores son las con clima (+3,1 a
  +3,7), y cumplen A; sin clima quedan entre +0,9 y +1,9.
- La receta con el valor más alto en T+2 (mes cíclico con clima, +8,3) no se
  propone por eso: con treinta y seis recetas, el máximo es optimista. Las del
  bloque de arriba están todas dentro de 1 o 2 puntos entre sí.
