# Tanda 51, línea BG — Presión epidémica regional, reabierta contra el techo medido

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Línea reclamada por Stevan. Estado: **cerrada**; ver Resultados.

## Por qué se reabre una línea cerrada

La línea H se cerró en la tanda 5 —«presión epidémica regional», rechazada 0 de
3 cortes—, y la regla de parada dice que una línea cerrada no se reabre sin un
mecanismo nuevo. Aquí hay dos cosas nuevas, y ninguna es «probemos otra vez».

**El instrumento cambió.** La tanda 5 midió sobre el modelo que no veía las
columnas de umbral y sobre tres cortes de 60 inicios. La tanda 13 mostró que ese
instrumento no reproduce: el mismo modelo, sobre la base común, pasa de 388 a
515 inicios. Un rechazo medido allá no es un rechazo aquí.

**Y ahora sabemos dónde está el techo.** La tanda 46 lo midió: al presupuesto
del 10 %, en T+1, **299 de los 641 inicios (47 %) no los anticipa nadie**, ni el
canal ni el modelo, y **el 52 % de esos arranca con cero casos en el mes de
origen** —unos 155—. Su mediana de casos sobre P75 es 0,00.

Un municipio en cero no tiene señal propia. Ni sus casos, ni sus rezagos, ni su
margen al umbral dicen nada, porque todos valen lo mismo: nada. Lo único que
puede anunciar un brote ahí es **lo que está pasando alrededor**. Eso es
exactamente la línea H, y es la única de las líneas abiertas que apunta al grupo
donde está la mitad del techo.

## Hipótesis

Dar al modelo el estado epidémico de los **demás** municipios de su departamento
en el mes de origen le permite anticipar inicios en municipios que hoy no tienen
señal propia, que son los que nadie anticipa.

## Qué se corre

Un bloque derivado de tres columnas, construido en preparación como el de la
línea G —no entra a la tabla canónica, para no tocar el digest ni la
certificación—, calculado **excluyendo el propio municipio** de todos los
agregados:

    presion_exceso_t    = fracción de los demás municipios del departamento en
                          EXCESO en el mes de origen
    presion_exceso_vel  = presion_exceso_t menos su valor del mes anterior
    presion_casos_t     = log1p de los casos de dengue de los demás municipios
                          del departamento en el mes de origen

La exclusión del propio municipio no es cosmética: sin ella la columna
reencodea el estado que el modelo ya tiene en `zona_canal_t`, y mediríamos otra
cosa.

Dos brazos sobre la base común, mismo panel, mismo calendario, mismas filas:
`log_conclima` —la mejor receta de la noche— contra `log_conclima` más el
bloque. Horizontes T+1 y T+2. Presupuestos 5 %, 10 % y 20 % de la sección 0.1,
con el veredicto al 10 %.

**Fuga.** Las tres columnas son del mes de origen, la misma disponibilidad que
los casos propios (`availability: 0` en la receta). Ninguna mira hacia adelante.
La velocidad necesita el mes anterior, así que aplica el filtro de filas comunes
del retroanálisis, igual que con G.

## Qué métrica decide

Inicios detectados al presupuesto de la sección 0, contra el canal condicionado,
en T+1. Nada de métricas nuevas.

## Criterio numérico, declarado antes de medir

Hoy, al 10 % en T+1, el canal condicionado detecta **279** inicios y
`log_conclima` detecta **299**: +3,1 pp, por debajo de la barra de 5 puntos. Para
pasarla el modelo necesita **311**, es decir **12 inicios más** de los que tiene.

1. **Barra de la sección 0.** El bloque pasa si `log_conclima + H` detecta **311
   o más** inicios al 10 % en T+1, con la cota inferior del intervalo por
   bloques de mes por encima de cero. Menos de 311: no pasa, y la línea H vuelve
   a cerrarse, ahora sobre el instrumento bueno.

2. **El mecanismo, que es lo que de verdad se está probando.** De los inicios
   que arrancan con cero casos en el mes de origen y que hoy no anticipa nadie
   —unos 155 en T+1—, el bloque tiene que convertir **15 o más**. Los 12 que
   hacen falta para la barra, más tres de margen por lo que se pierda en otro
   lado.

3. **El caso incómodo, declarado de antemano.** Si se cumple 1 pero no 2 —el
   agregado mejora pero el grupo de cero casos no se mueve— **no se reporta como
   H confirmada**, sino como «mejora sin el mecanismo declarado», y hay que
   averiguar de dónde salió antes de proponer nada.

## Qué contaría como fracaso

Que el bloque **reste** inicios, o que el grupo de cero casos no se mueva en
absoluto. Lo primero cierra la línea definitivamente; lo segundo dice que la
información regional a escala de departamento es demasiado gruesa, y entonces lo
que seguiría es vecindad real, no departamento —pero eso sería otra línea, con
su propia preinscripción y sus propios datos de adyacencia, que hoy no tenemos.

## Qué no decide esta tanda

No decide sobre el umbral de utilidad ni sobre el veredicto del proyecto. No
decide sobre T+2, donde el modelo ya pasa la barra: ahí el bloque se mide y se
reporta, pero el veredicto de la línea se emite en T+1, que es donde está el
problema.

## Trampas conocidas, anotadas antes de caer en ellas

**La regla 9, que esta línea tiene que pasar antes de nada.** «Separar no es
aportar»: antes de atribuirle nada al bloque hay que entrenar un modelo con las
variables vigentes para predecir cada una de las tres columnas. Si las predice
bien, el modelo ya podía construirlas y el bloque no agrega —que es exactamente
lo que le pasó a G en la tanda 13—. Esta comprobación va **antes** de leer los
inicios detectados, no después.

**El riesgo de la comparación múltiple.** Van 51 tandas sobre los mismos 641
inicios. Esta línea tiene **una** hipótesis, **un** criterio y **un**
presupuesto de veredicto, declarados arriba. No se prueban variantes del bloque
buscando cuál pasa: si estas tres columnas no funcionan, la línea se cierra.

**Y la trampa de la tanda 13.** Antes de atribuirle el resultado al bloque, hay
que enumerar todo lo que cambió entre los dos brazos. Debe ser una sola cosa: las
tres columnas. Se verifica con `conjunto.csv` —mismas `filas_comunes` en los
dos— antes de mirar el resumen.

## Resultados

> Estado: **cerrada**. Los dos criterios fallan.

### El brazo de control reproduce la noche, a la unidad

Antes de leer nada del bloque: `log_conclima` sin tocar, sobre esta base, da en
T+1 al presupuesto del 10 % (f = 0,85, 621 alertas) **279 del canal contra 299
del modelo**, y en T+2 (f = 0,95, 632 alertas) **152 contra 185**. Son
exactamente las cifras de la tanda 33, medidas por otra persona con otro script.

Es la primera reproducción cruzada del proyecto y vale por sí sola: la base
común no depende de quién la corra.

Las filas comunes siguen siendo **7 612 en T+1 y 7 572 en T+2**, idénticas a
todas las corridas anteriores, ahora con nueve columnas derivadas en el filtro
en vez de seis. El bloque nuevo no movió el conjunto evaluable, así que la
comparación con todo lo medido antes sigue en pie.

### La regla 9 se pasó antes de mirar ningún inicio

R² fuera de muestra al predecir cada columna nueva con las variables vigentes,
entrenando 2012-2017 y evaluando 2018-2024:

| Columna | Lineal | Árbol | Spearman |
| --- | --- | --- | --- |
| `presion_exceso_t` | 0,32 | 0,14 | 0,57 |
| `presion_exceso_vel` | −0,01 | −0,26 | **0,09** |
| `presion_casos_t` | 0,25 | 0,16 | 0,51 |

Las variables vigentes explican entre un cuarto y un tercio del nivel —lógico,
un municipio correlaciona con su departamento porque comparten estación y onda—
y **nada de la velocidad**. El contraste con el bloque G es el punto: allá la
correlación de rangos con lo que el modelo ya podía construir era 0,999, una
reformulación; acá el máximo es 0,57. La información es nueva.

### Criterio 1: no pasa

| T+1, 10 % (621 alertas) | Canal | Modelo |
| --- | --- | --- |
| `log_conclima` | 279 | 299 |
| `log_conclima` + H | 279 | **296** |

El criterio pedía **311**. El bloque queda en 296, tres por debajo del control y
quince por debajo de la barra. En T+2 los dos brazos dan 185.

### Criterio 2: tampoco, y por mucho

El bloque **no es inerte**: gana 21 inicios y pierde 24. De los 21 que gana, 13
no los anticipaba nadie. Pero de esos, **solo 4 arrancan con cero casos en el
mes de origen**, contra los 15 que exigía el criterio.

De paso queda confirmada la tanda 46 por una vía independiente: de los 299
inicios que no anticipa nadie, **156 arrancan desde cero casos**, el 52 %.

### Veredicto: la línea H se cierra, ahora sobre el instrumento bueno

El bloque mueve detecciones de sitio en vez de agregarlas. Y donde tenía que
servir —los 156 inicios sin señal propia— convierte cuatro.

La lectura que deja, y que es la rama que esta preinscripción había declarado
para este caso: **la presión regional a escala de departamento es demasiado
gruesa.** Un departamento son 47 o 29 municipios; saber que el 34 % de ellos
está en exceso dice poco sobre un municipio concreto que hoy tiene cero casos.
Lo que seguiría es **vecindad real** —municipios contiguos o a cierta
distancia—, y eso es otra línea, con sus propios datos de adyacencia, que hoy no
están en el contrato canónico.

**Y una lección sobre la regla 9.** El bloque la pasó holgadamente: su
información era nueva, no una reformulación de lo que el modelo ya tenía. Y aun
así no aportó. La regla 9 es necesaria y no suficiente, y esta tanda es el
contraejemplo que lo demuestra: sirve para descartar barato —como habría
descartado a G— pero no para prometer nada.

### Lo que queda sin tocar

Los 156 inicios que arrancan desde cero casos y que nadie anticipa siguen
siendo la mitad del techo, y ninguna de las 51 tandas los ha movido. Quien
quiera atacarlos necesita información que hoy no está en el panel.
