# Tanda 36, línea AR — Repartir el presupuesto entre el canal y el modelo

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **cerrada** el 10 de noviembre de 2026. Se corre sobre la base común del
> retroanálisis: `canonical.mode=approved`, calendario y departamentos de
> `parameters_retroanalisis.yml` sin tocar, `conjunto.csv` reportado.

## Origen y relación con la línea N

Se escribe después de ver la tanda 35 y se declara así. La línea N («repartir el
trabajo con el canal») se cerró en la tanda 7 con XGBoost y el bloque G. La
sección 7 dice que una línea cerrada no se reabre sin un mecanismo nuevo: el
mecanismo nuevo es el de la tanda 35, medido con la logística sobre la base
común. El modelo gana 31 a 49 inicios donde el canal no puede ver y pierde 13 a 24
donde el canal está seguro.

## Hipótesis

Si en cada mes se dejan las alertas «seguras» del canal y el modelo llena el resto
del cupo, se suman las dos ventajas.

## Qué se corre

Al 10 % de la sección 0. Cada mes, el canal condicionado con la f de la tanda 33
emite K alertas. Dos reglas, fijadas aquí y sin buscar parámetros:

1. **Seguras primero**: se conservan las alertas del canal donde los casos del
   origen ya pasan el P75 completo del mes objetivo (casos ≥ P75); el modelo llena
   el resto del cupo K entre las demás filas, por puntaje.
2. **Mitad y mitad**: la mitad del cupo (redondeada hacia abajo) para las alertas
   del canal con mayor casos/P75, y la otra mitad para el modelo entre las demás
   filas.

Para la logística sin clima y la logística con clima, T+1 y T+2. Se compara cada
regla contra el modelo solo y contra el canal solo, con el IC por bloques de mes.

## Qué contaría como mejora

Que la regla supere al **modelo solo** en al menos 5 puntos en algún horizonte con
la cota inferior sobre cero. Sin efecto si queda dentro de ±5 puntos; empeora si
resta 5 o más.

## Resultado: repartir no supera al modelo solo

| Receta | Horizonte | Regla | Canal | Modelo | Regla | Contra el modelo (pp, IC mes) | Contra el canal (pp, IC mes) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| logistica_sin_clima | T+1 | seguras | 279 | 286 | 279 | -1.1 (-3.4 a 1.4) | +0.0 (-1.1 a 1.2) |
| logistica_sin_clima | T+1 | mitad | 279 | 286 | 292 | +0.9 (-0.6 a 2.5) | +2.0 (-0.2 a 4.1) |
| logistica_sin_clima | T+2 | seguras | 152 | 179 | 156 | -5.0 (-8.7 a -1.1) | +0.9 (-0.4 a 2.2) |
| logistica_sin_clima | T+2 | mitad | 152 | 179 | 176 | -0.7 (-2.8 a 1.5) | +5.2 (1.7 a 8.9) |
| log_conclima | T+1 | seguras | 279 | 299 | 282 | -2.7 (-5.5 a 0.0) | +0.5 (-0.8 a 1.7) |
| log_conclima | T+1 | mitad | 279 | 299 | 305 | +0.9 (-0.8 a 2.5) | +4.1 (1.7 a 6.6) |
| log_conclima | T+2 | seguras | 152 | 185 | 156 | -6.3 (-10.7 a -2.2) | +0.9 (-0.4 a 2.2) |
| log_conclima | T+2 | mitad | 152 | 185 | 173 | -2.6 (-4.8 a -0.7) | +4.6 (0.9 a 7.8) |

- **Seguras primero** casi reproduce al canal: la mayoría de sus alertas ya cumplen
  casos ≥ P75, así que al modelo le queda poco cupo. **Empeora** frente al modelo
  en T+2 (−5,0 y −6,3 pp, IC por mes que excluye el cero).
- **Mitad y mitad** queda a +0,9 pp del modelo en T+1 y resta en T+2 (−0,7 y −2,6).
  **Sin efecto** en T+1.

Ninguna regla supera al modelo solo en 5 puntos. La pérdida del modelo en el
tercio cercano al umbral (tanda 35) no se recupera dándole ese tercio al canal,
porque el modelo ya ordena bien esas filas y lo que gana en las lejanas pesa más.
La línea N sigue cerrada, ahora también con la logística.

Herramienta: `pipeline/tools/noche/hibrido.py`.
