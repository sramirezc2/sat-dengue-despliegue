# Tanda 35, línea AQ — Qué inicios gana el modelo al 10 %

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **cerrada** el 10 de noviembre de 2026. Se corre sobre la base común del
> retroanálisis: `canonical.mode=approved`, calendario y departamentos de
> `parameters_retroanalisis.yml` sin tocar, `conjunto.csv` reportado.

## Hipótesis

En la tanda 10, con otro instrumento, la ventaja del modelo estaba en municipios
poco endémicos y en brotes que arrancan con pocos casos, donde el canal no ve
nada. Si se repite sobre la base común y al presupuesto de referencia, eso dice a
quién le sirve el modelo.

## Qué se corre

Ningún modelo nuevo. Al 10 % de la sección 0, para la logística sin clima y la
logística con clima, los inicios detectados por el canal condicionado y por el
modelo, separados en tercios (fijados sobre todas las filas evaluadas, antes de
mirar el desempeño) de:

- **endemicidad**: el P75 del mes objetivo del municipio;
- **cercanía al umbral en el origen**: casos del mes de origen sobre el P75 del
  mes objetivo.

## Qué no decide

Es una lectura; no cambia veredictos.

## Resultado: el modelo gana donde el canal no puede ver, y pierde donde el canal está seguro

| Receta | Horizonte | Corte | Tercio | Inicios | Canal | Modelo | Diferencia |
| --- | --- | --- | --- | --- | --- | --- | --- |
| logistica_sin_clima | T+1 | endemicidad (P75 objetivo) | bajo | 268 | 107 | 117 | +10 |
| logistica_sin_clima | T+1 | endemicidad (P75 objetivo) | medio | 231 | 106 | 101 | -5 |
| logistica_sin_clima | T+1 | endemicidad (P75 objetivo) | alto | 142 | 66 | 68 | +2 |
| logistica_sin_clima | T+1 | cercanía al umbral (casos/P75) | bajo | 118 | 0 | 19 | +19 |
| logistica_sin_clima | T+1 | cercanía al umbral (casos/P75) | medio | 115 | 0 | 12 | +12 |
| logistica_sin_clima | T+1 | cercanía al umbral (casos/P75) | alto | 408 | 279 | 255 | -24 |
| logistica_sin_clima | T+2 | endemicidad (P75 objetivo) | bajo | 185 | 57 | 88 | +31 |
| logistica_sin_clima | T+2 | endemicidad (P75 objetivo) | medio | 167 | 61 | 56 | -5 |
| logistica_sin_clima | T+2 | endemicidad (P75 objetivo) | alto | 107 | 34 | 35 | +1 |
| logistica_sin_clima | T+2 | cercanía al umbral (casos/P75) | bajo | 104 | 0 | 30 | +30 |
| logistica_sin_clima | T+2 | cercanía al umbral (casos/P75) | medio | 104 | 0 | 18 | +18 |
| logistica_sin_clima | T+2 | cercanía al umbral (casos/P75) | alto | 251 | 152 | 131 | -21 |
| log_conclima | T+1 | endemicidad (P75 objetivo) | bajo | 268 | 107 | 120 | +13 |
| log_conclima | T+1 | endemicidad (P75 objetivo) | medio | 231 | 106 | 116 | +10 |
| log_conclima | T+1 | endemicidad (P75 objetivo) | alto | 142 | 66 | 63 | -3 |
| log_conclima | T+1 | cercanía al umbral (casos/P75) | bajo | 118 | 0 | 18 | +18 |
| log_conclima | T+1 | cercanía al umbral (casos/P75) | medio | 115 | 0 | 15 | +15 |
| log_conclima | T+1 | cercanía al umbral (casos/P75) | alto | 408 | 279 | 266 | -13 |
| log_conclima | T+2 | endemicidad (P75 objetivo) | bajo | 185 | 57 | 87 | +30 |
| log_conclima | T+2 | endemicidad (P75 objetivo) | medio | 167 | 61 | 62 | +1 |
| log_conclima | T+2 | endemicidad (P75 objetivo) | alto | 107 | 34 | 36 | +2 |
| log_conclima | T+2 | cercanía al umbral (casos/P75) | bajo | 104 | 0 | 28 | +28 |
| log_conclima | T+2 | cercanía al umbral (casos/P75) | medio | 104 | 0 | 21 | +21 |
| log_conclima | T+2 | cercanía al umbral (casos/P75) | alto | 251 | 152 | 136 | -16 |

- **Cercanía al umbral.** En los dos tercios con pocos casos en el origen frente al
  umbral, **el canal no detecta ningún inicio**: por construcción solo alerta
  cuando los casos ya pasan f × P75. Ahí el modelo detecta entre 12 y 30 inicios
  por tercio. En el tercio cercano al umbral el canal es mejor: el modelo
  **pierde entre 13 y 24 inicios**, porque gasta en las filas lejanas parte del
  presupuesto que el canal pone en las cercanas.
- **Endemicidad.** En T+2 casi toda la ventaja está en los **municipios poco
  endémicos** (+30 y +31); en los medios y altos el modelo empata. En T+1, sin
  clima, la ventaja también es de los poco endémicos (+10); con clima se suma la
  endemicidad media (+10).

Lo que abre, declarado como hipótesis: si el modelo pierde inicios en el tercio
donde el canal está seguro, **repartir el presupuesto** (el canal en las filas
cercanas al umbral y el modelo en el resto) podría sumar las dos ventajas. La
línea N cerró esa idea en la tanda 7 con XGBoost y el bloque G; esta lectura es
un mecanismo nuevo con la logística, y se preinscribe aparte.
