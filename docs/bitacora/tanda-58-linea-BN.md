# Tanda 58, línea BN — Las combinaciones, confirmadas en la reserva 2023-2024

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **cerrada** el 11 de noviembre de 2026. Se corre sobre la base común del
> retroanálisis: `canonical.mode=approved`, calendario y departamentos de
> `parameters_retroanalisis.yml` sin tocar, `conjunto.csv` reportado.

## Origen

Las tandas 14 a 57 eligieron y midieron sobre los mismos siete años. La búsqueda de
Stevan (tandas 94 a 132) fijó un protocolo con reserva: buscar en 2018-2022 y
confirmar en 2023-2024. Él lo aplicó a sus reglas (DG, DH y DJ); esta tanda lo aplica
a las **combinaciones sin regla** de las tandas 14 a 57, que no estaban confirmadas.
No toca DJ ni ninguna regla de reparto.

## Regla de selección, escrita antes de mirar la reserva

1. **Búsqueda.** Para cada combinación logística o XGBoost de las tandas 14 a 57 con
   predicciones guardadas, el veredicto de la sección 0 al 10 % (fracción de 76
   municipios por mes, `veredicto.py` con semilla por celda) **solo con los años
   objetivo 2018-2022**. La f del canal se elige igual que en la tanda 33, pero sobre
   esos años.
2. **Selección.** Pasan a la reserva las **tres** combinaciones con mayor ganancia en
   T+2 en la búsqueda, más la logística con clima como referencia si no está entre
   ellas. Empates por la ganancia en T+1.
3. **Confirmación.** El mismo veredicto **solo con 2023-2024**, sin cambiar nada.

## Qué decide

Una combinación **confirma** en T+2 si en la reserva pasa la barra de la sección 0.3
(al menos 5 puntos con la cota inferior del IC por bloques de mes sobre cero). En T+1
se reporta si cumple A. Con dos años de reserva (unos 150 inicios en T+2) la potencia
es baja; un «no confirma» con el punto estimado sobre 5 se lee como falta de
potencia, no como refutación, y se declara así.

## Qué no decide

No compara familias ni elige campeón. No usa 2025.

## Resultado

**Búsqueda (2018-2022, 417 inicios en T+1 y 312 en T+2).** Las diez mejores de 65
combinaciones con las mismas filas, por T+2:

| Combinación | T+1 (pp) | T+2 (pp) |
| --- | --- | --- |
| xgb_d2_sinclima_s7 | +1.7 | +8.3 |
| logc_mes | +5.0 | +7.7 |
| xgb_d2_sinclima_s13 | +0.2 | +7.7 |
| log_conclima_sin2020 | +2.9 | +7.1 |
| xgb_d2_sinclima_s42 | +1.7 | +7.1 |
| log_conclima | +4.3 | +6.7 |
| logc_depto | +4.3 | +6.7 |
| xgb_d2_sinclima_s29 | +1.4 | +6.7 |
| xgb_d2_s7 | +1.2 | +6.7 |
| logc_log1p_lluvia | +4.6 | +6.4 |

Por la regla, pasan a la reserva las tres primeras por T+2 (`xgb_d2_sinclima_s7`, y
`logc_mes` y `xgb_d2_sinclima_s13`, empatadas en +7,7 y ordenadas por T+1), más
`log_conclima` como referencia.

**Confirmación (2023-2024, 224 inicios en T+1 y 147 en T+2):**

| Combinación | Horizonte | Búsqueda 2018-2022 (pp, IC mes) | Reserva 2023-2024 (pp, IC mes) | Barra en la reserva |
| --- | --- | --- | --- | --- |
| xgb_d2_sinclima_s7 | T+2 | +8.3 (3.5 a 13.1) | +6.8 (0.7 a 12.9) | CUMPLE |
| xgb_d2_sinclima_s7 | T+1 | +1.7 (-1.7 a 5.0) | +1.3 (-1.3 a 3.6) | NO / A: NO |
| logc_mes | T+2 | +7.7 (2.9 a 12.2) | +10.2 (4.8 a 16.3) | CUMPLE |
| logc_mes | T+1 | +5.0 (1.4 a 8.6) | +2.7 (-0.9 a 6.2) | NO / A: NO |
| xgb_d2_sinclima_s13 | T+2 | +7.7 (2.6 a 12.8) | +6.1 (-0.7 a 12.2) | NO |
| xgb_d2_sinclima_s13 | T+1 | +0.2 (-2.9 a 3.4) | +2.7 (0.0 a 5.4) | NO / A: NO |
| log_conclima | T+2 | +6.7 (2.2 a 11.2) | +8.8 (1.4 a 16.3) | CUMPLE |
| log_conclima | T+1 | +4.3 (0.5 a 7.9) | +2.2 (-1.3 a 5.8) | NO / A: NO |

- **En T+2 confirman tres de las cuatro**: la logística con clima (+8,8 pp, IC 1,4 a
  16,3), el mes cíclico con clima (+10,2 pp, IC 4,8 a 16,3) y el XGBoost de
  profundidad 2 sin clima con semilla 7 (+6,8 pp, IC 0,7 a 12,9). La semilla 13 queda
  en +6,1 con la cota en −0,7: por lo declarado, **falta de potencia, no
  refutación**.
- **En T+1 ninguna confirma.** El mes cíclico con clima pasaba la barra en la
  búsqueda (+5,0 pp, IC 1,4 a 8,6), pero en la reserva cae a +2,7 (IC −0,9 a 6,2).
  Es el patrón esperable de una selección entre 65.
- **La logística con clima, la configuración que ya veníamos usando, confirma en
  T+2 sin haber sido elegida por la búsqueda.** El mes cíclico la supera en 1,4
  puntos en la reserva, dentro del ruido, y en la tanda 24 el mes cíclico no aportó
  nada por sí solo; no hay base para preferirlo.

Contexto declarado (regla 9): como dos de las seleccionadas son semillas sueltas de
XGBoost, se reportan las cinco en la reserva:

| Semilla | Reserva T+2 (pp, IC mes) | Barra |
| --- | --- | --- |
| 7 | +6.8 (0.7 a 12.9) | CUMPLE |
| 13 | +6.1 (-0.7 a 12.2) | NO |
| 53 | +6.8 (0.7 a 12.9) | CUMPLE |
| 29 | +6.8 (0.0 a 12.9) | NO |
| 42 | +6.8 (0.0 a 13.6) | NO |

Todas quedan entre +6,1 y +6,8 pp; dos pasan la barra y tres quedan con la cota
inferior en cero o apenas debajo. El XGBoost simple sin clima es consistente pero
queda unos 2 puntos por debajo de la logística con clima en la reserva.

Nota: las corridas con entrenamiento nacional (tanda 18) no entraron, porque sus
predicciones comparten nombre con las locales; ninguna había mejorado.
Herramienta: `veredicto.py` de main (semilla por celda), con un filtro de años objetivo
aplicado en una copia local; no se tocó el código del repositorio.
