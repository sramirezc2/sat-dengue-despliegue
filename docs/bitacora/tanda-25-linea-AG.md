# Tanda 25, línea AG — Lectura por departamento

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **cerrada** el 10 de noviembre de 2026. Se corre sobre la base común del
> retroanálisis: `canonical.mode=approved`, calendario y departamentos de
> `parameters_retroanalisis.yml` sin tocar, `conjunto.csv` reportado.

## Hipótesis

En la tanda 10, con otro instrumento, la logística ganaba en Tolima y perdía en
Meta en T+1. Si eso se repite sobre la base común, la ventaja del modelo depende
de un departamento y hay que reportarlo (punto 7 de la regla de utilidad).

## Qué se corre

Ningún modelo nuevo. Con las predicciones de las tandas 14 y 15, por departamento
(50 Meta, 73 Tolima) y por horizonte: inicios detectados por el canal condicionado
y por cada receta, con el mismo presupuesto por mes que en la comparación total.

## Qué no decide

Es una lectura. No cambia veredictos; se reporta si la ventaja tiene el mismo
signo en los dos departamentos.

## Resultado: en T+1 la ventaja es de Tolima, y el clima es lo que gana en Meta

Inicios detectados al presupuesto del canal condicionado, por departamento (los
totales cuadran con la tanda 11: 323 y 207 del canal).

| T+1 | Meta: canal 152 de 264 | Tolima: canal 171 de 377 |
| --- | --- | --- |
| logistica_sin_clima | 154 (+2) | 193 (+22) |
| log_conclima | 168 (+16) | 191 (+20) |
| log_minima | 149 (-3) | 190 (+19) |
| xgb_banco_s53 | 149 (-3) | 193 (+22) |
| xgb_banco_s7 | 143 (-9) | 185 (+14) |
| xgb_banco_s13 | 142 (-10) | 189 (+18) |
| xgb_banco_s29 | 148 (-4) | 191 (+20) |
| xgb_banco_s42 | 139 (-13) | 186 (+15) |

| T+2 | Meta: canal 92 de 182 | Tolima: canal 115 de 277 |
| --- | --- | --- |
| logistica_sin_clima | 102 (+10) | 146 (+31) |
| log_conclima | 106 (+14) | 147 (+32) |
| log_minima | 100 (+8) | 145 (+30) |
| xgb_banco_s53 | 100 (+8) | 147 (+32) |
| xgb_banco_s7 | 101 (+9) | 142 (+27) |
| xgb_banco_s13 | 102 (+10) | 138 (+23) |
| xgb_banco_s29 | 98 (+6) | 144 (+29) |
| xgb_banco_s42 | 89 (-3) | 145 (+30) |

- **T+1.** La logística sin clima gana en Tolima (+22) y **empata en Meta** (+2).
  La mínima y XGBoost, con las cinco semillas, **pierden en Meta** (−3 a −13).
- **El clima es lo que cambia Meta**: con clima la logística pasa de +2 a **+16**
  en Meta, y en Tolima casi no cambia (+22 a +20). Los +12 inicios que el clima
  sumó en la tanda 15 salen casi todos de Meta.
- **T+2.** Todas las recetas ganan en los dos departamentos, más en Tolima (+23 a
  +32) que en Meta (−3 a +14).

Lo que esto abre, declarado como hipótesis y no como resultado: el clima aporta
donde el canal endémico se queda corto, que en T+1 es Meta. Un modelo por
departamento ya se descartó antes con otro instrumento; lo que no se ha probado es
el clima solo en Meta.

## Agregado: la misma lectura al 10 % de la sección 0

Con el presupuesto de referencia de la tanda 33 (unas 8 alertas por mes):

| Receta | Horizonte | Meta (canal → receta) | Tolima (canal → receta) |
| --- | --- | --- | --- |
| logistica_sin_clima | T+1 | 134 → 136 (+2) | 145 → 150 (+5) |
| log_conclima | T+1 | 134 → 147 (+13) | 145 → 152 (+7) |
| log_minima | T+1 | 134 → 131 (-3) | 145 → 155 (+10) |
| logc_minima | T+1 | 134 → 143 (+9) | 145 → 156 (+11) |
| logistica_sin_clima | T+2 | 65 → 76 (+11) | 87 → 103 (+16) |
| log_conclima | T+2 | 65 → 78 (+13) | 87 → 107 (+20) |
| log_minima | T+2 | 65 → 76 (+11) | 87 → 106 (+19) |
| logc_minima | T+2 | 65 → 74 (+9) | 87 → 111 (+24) |

- **T+2 gana en los dos departamentos** con las cuatro recetas: Meta +9 a +13,
  Tolima +16 a +24. La ventaja de T+2 de la tanda 33 no depende de un departamento.
- **En T+1 se repite el patrón del clima en Meta**: sin clima +2, con clima +13; en
  Tolima el clima casi no cambia (+5 a +7). La mínima sin clima pierde en Meta (−3).
