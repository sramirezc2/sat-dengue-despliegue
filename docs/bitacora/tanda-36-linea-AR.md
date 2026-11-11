# Tanda 36, línea AR — Repartir el presupuesto entre el canal y el modelo

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **preinscrita, sin correr.** Se corre sobre la base común del
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
