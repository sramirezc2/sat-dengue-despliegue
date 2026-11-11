# Tanda 13, línea U — Acercar el banco y el retroanálisis, una diferencia a la vez

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Línea reclamada por Stevan. Estado: **cerrada**. El banco queda explicado y
> la línea G también; ver Resultados de la corrida 2.

## El problema que hay que resolver

La tanda 12 dejó una distancia sin explicar. El banco de la línea O reportó
**388 inicios sin el bloque G y 467 con él**, a unas 1 830 alertas. El
retroanálisis, con los mismos hiperparámetros y sobre la base común, detecta
**515 y 519** a 1 866 alertas.

Esa distancia no se puede atribuir a nada todavía, porque banco y retroanálisis
difieren en tres cosas a la vez (ver `tanda-12-linea-T.md`):

1. **Insumos.** El banco arma su matriz desde el `features.csv` de un *replay*
   archivado: 29 variables, sin clima. El retroanálisis usa las 33 del contrato.
2. **Cadencia de reentrenamiento.** El banco reentrena **una vez al año**. El
   retroanálisis reentrena **en cada mes de origen**: 82 ajustes en vez de 7.
3. **Reparto de alertas.** El banco usa un cupo mensual (`top_cupo`,
   `MESES_CUPO = 12`). El retroanálisis iguala el volumen total contra el de la
   línea base y deja que el umbral decida dónde caen.

Mientras las tres estén juntas, **ninguna cifra del banco es comparable con
ninguna cifra del pipeline**, y eso incluye el veredicto sobre la línea G.

## Hipótesis

**La cadencia explica la mayor parte de la distancia.** Un modelo que reentrena
cada mes ve, en promedio, seis meses más de historia que uno que reentrena en
enero y se queda quieto todo el año, y reparte ese aprendizaje sobre los meses
en los que el brote está empezando. La cadencia es además la única de las tres
diferencias que no cambia ni los insumos ni la métrica: cambia cuántas veces se
mira.

## Qué se corre

Una sola diferencia a la vez, en este orden. Esta tanda cubre **solo la
primera**; las otras dos quedan preinscritas aquí pero se corren después y con
su propio cierre.

**Corrida 1 — cadencia.** El retroanálisis con reentrenamiento anual en vez de
mensual, sobre el mismo panel, el mismo calendario, las mismas filas y los
mismos presupuestos de la tanda 12. Dos brazos, con y sin el bloque G, y los dos
modelos del banco (`xgboost_banco.yml` y `xgboost_banco_g.yml`). Horizontes T+1
y T+2.

La implementación no puede tocar el contrato del arnés: la cadencia entra como
un corte de entrenamiento declarado que, cuando no se declara, deja los folds
byte a byte como están hoy.

## Qué métrica decide

Inicios detectados al presupuesto de alertas de cada línea base, sobre la base
común, igual que las tandas 11 y 12. Nada de AUROC ni de métricas nuevas.

## Qué contaría como respuesta, declarado antes de mirar

Sobre el brazo **sin** bloque en T+1, que hoy detecta 515 de 641 a 1 866
alertas, contra los 388 del banco. La distancia a explicar es de **127 inicios**.

- **La cadencia explica la distancia** si con reentrenamiento anual el brazo sin
  bloque baja a **452 o menos**, es decir al menos la mitad de la distancia.
- **La cadencia no la explica** si baja a **483 o más**, es decir menos de un
  cuarto.
- Entre 452 y 483 el resultado es **parcial**: se reporta como tal y se corre la
  segunda diferencia sin declarar nada sobre la primera.

Y por separado, sobre el aporte del bloque:

- **El aporte de G reaparece** si bajo cadencia anual el bloque suma **32
  inicios o más** (los 5 puntos de la sección 0 sobre 641) con la cota inferior
  del intervalo por encima de cero.
- **No reaparece** si suma menos, que es lo que ya midió la tanda 12 bajo
  cadencia mensual: entre −2 y +12.

## Qué contaría como fracaso de la tanda

Que el brazo sin bloque **suba** con reentrenamiento anual, o que la corrida no
produzca folds en algún horizonte. Lo primero invalidaría la hipótesis del
mecanismo y habría que decirlo así, no buscarle una explicación después.

## Qué no decide esta tanda

No decide sobre la línea G. G sigue **no reproducida** hasta que el banco
reproduzca, y esta tanda solo mide una de las tres diferencias que lo impiden.
Tampoco decide si el banco estaba bien o mal construido: decide cuánto de la
distancia explica la cadencia.

## Trampa conocida, anotada antes de caer en ella

Los 647 inicios coinciden entre banco y pipeline, y **eso no valida el
instrumento**: la etiqueta depende del panel, no del modelo ni del protocolo.
Coincidir en las etiquetas no es coincidir en la medición, y la tanda 12 estuvo
a punto de usar esa coincidencia como si lo fuera.

## Resultados

> Estado: **corrida 1 cerrada. La hipótesis se rechaza por su propio criterio.**

Mismas filas que las tandas 11 y 12 —7 612 en T+1 y 7 572 en T+2—, cero
orígenes omitidos, mismo panel y mismo calendario. Lo único que cambió es la
cadencia.

**El brazo sin bloque, en T+1 a 1 866 alertas: 515 con cadencia mensual, 520 con
cadencia anual.** El criterio declarado era bajar a 452 o menos para explicar la
distancia, y a 483 o más para no explicarla. No solo no bajó: **subió**, que es
exactamente la condición de fracaso que esta preinscripción había escrito.

Al presupuesto de cada línea base, T+1, inicios detectados:

| Brazo | Canal P75 (315) | Condicionado (817) | Ajustado (1 128) |
| --- | --- | --- | --- |
| Sin bloque, mensual | 160 | 328 | 385 |
| Sin bloque, anual | 156 | 325 | 376 |
| Con bloque, mensual | 169 | 340 | 391 |
| Con bloque, anual | 174 | 337 | 388 |

En T+2 el patrón es el mismo: sin bloque pasa de 106, 242 y 243 a 113, 241 y
242. Nada se mueve más allá del ruido, y lo poco que se mueve va en los dos
sentidos.

**Veredicto declarado: la cadencia no explica nada de los 127 inicios.** Siete
reentrenamientos al año producen prácticamente el mismo modelo que ochenta y
dos. Eso es un hallazgo por sí solo: la ventaja del retroanálisis sobre el banco
no viene de mirar más veces.

**Y el bloque G sigue sin reaparecer.** Bajo cadencia anual suma +12 inicios al
presupuesto del canal condicionado y +10 a 1 866 alertas, contra los **32 o más
con cota inferior sobre cero** que esta preinscripción exigía. Es el mismo orden
de magnitud que midió la tanda 12 bajo cadencia mensual.

## Corrección: el razonamiento del cupo estaba mal, y leyendo el código apareció la respuesta

Arriba quedó escrito que la siguiente corrida sería el reparto de alertas,
porque «el cupo mensual del banco obliga a repartir parejo entre los doce meses
y el retroanálisis deja que el umbral las concentre». **Eso era una mala lectura
de los dos lados, y se corrige antes de medir nada.**

Leyendo `top_cupo` y `anio` en el script del banco: el cupo **no es mensual**.
Se calcula una vez por año —la tasa de alerta del canal en los últimos doce
meses de entrenamiento, por el número de filas del año— y `top_cupo` toma las
mejores de **todo el año**, los doce meses y los 76 municipios juntos. Y el
retroanálisis hace lo contrario: `emparejar` emite **en cada mes de origen**
exactamente tantas alertas como la línea base emitió ese mes.

O sea que el que concentra es el banco, no nosotros. Y como concentrar
libremente dentro del año es una restricción **menos** exigente que igualar mes
a mes, el reparto del banco **favorece** al modelo del banco. Predice el signo
contrario al que hace falta: no puede explicar por qué el banco detecta menos.

### La diferencia que sí explica el gap

Comparando el `features.csv` del replay que el banco consume contra el contrato
canónico: el banco entrena con 28 columnas y **ninguna de las siete de umbral**.

| En el canon | En el banco |
| --- | --- |
| `p25_canal_t`, `p50_canal_t`, `p75_canal_t` | no están |
| `p25_h5_t1`, `p75_h5_t1`, `p25_h5_t2`, `p75_h5_t2` | no están |
| `total_notifications_count` y sus rezagos | no están |
| `zona_canal_t` | sí, y es lo único del canal que ve |

El banco ve **la zona del canal**, que es la decisión ya tomada, pero nunca ve
**el umbral**. Y la etiqueta que queremos predecir es exactamente «los casos del
mes objetivo pasan ese umbral».

Eso reordena todo lo medido en las tandas 11, 12 y 13 en una sola explicación:

- El modelo del banco no puede ver el umbral, así que el bloque G —que es la
  distancia al umbral— es su **única** vía para conocerlo. De ahí el +79.
- El modelo del pipeline ve los umbrales directamente. La logística forma el
  margen como resta de logaritmos (correlación de rangos 0,999, tanda 11) y
  XGBoost puede cortar sobre las dos columnas. De ahí que G no aporte: +2 sobre
  la logística, entre −2 y +12 sobre los árboles.
- Y de ahí también los 515 contra 388: la columna más informativa para esta
  etiqueta es el umbral del mes objetivo, y el banco no la tenía. En la tanda 11
  el coeficiente más grande de la logística es `p75_h5_t1` en −2,83, contra
  +1,29 de los casos.

**Si esto es correcto, G nunca fue una mejora general: era el parche de un
modelo que no podía ver el umbral del canal.**

## Corrida 2 — los insumos. Predicción declarada antes de medir

Se corre el modelo del banco sobre la base común **quitándole las siete columnas
de umbral**, con y sin el bloque G, cadencia mensual, mismo panel, mismo
calendario y mismas filas. Dos predicciones, las dos falsables:

1. **El brazo sin bloque cae.** De 515 a **452 o menos** en T+1 a 1 866 alertas,
   acercándose a los 388 del banco.
2. **El aporte de G reaparece.** Sin los umbrales, el bloque suma **32 inicios o
   más** con la cota inferior del intervalo por encima de cero, contra los +10
   que suma hoy teniéndolos.

**Si las dos se cumplen, la línea G queda explicada**: aporta cuando el modelo
no ve el umbral y no aporta cuando sí lo ve, y el banco queda reproducido en su
mecanismo aunque no en su cifra exacta.

**Si la primera se cumple y la segunda no**, los umbrales explican el nivel pero
no el aporte del bloque, y G sigue sin explicación.

**Si ninguna se cumple**, esta lectura del `features.csv` es incorrecta y hay que
volver a empezar por el script del banco.

## Resultados de la corrida 2: las dos predicciones se cumplen

Mismo panel, mismo calendario, mismas 7 612 filas en T+1, cero orígenes
omitidos. Inicios detectados en T+1 a 1 866 alertas:

| Brazo | Inicios de 641 |
| --- | --- |
| Con umbrales, sin bloque | 515 |
| Con umbrales, con bloque | 519 |
| **Sin umbrales, sin bloque** | **411** |
| **Sin umbrales, con bloque** | **527** |

Y al presupuesto de las líneas base, T+1:

| Brazo | Canal P75 (315) | Ajustado (1 128) |
| --- | --- | --- |
| Con umbrales, sin bloque | 160 | 385 |
| Sin umbrales, sin bloque | 106 | 283 |
| Sin umbrales, con bloque | 163 | 388 |

**Predicción 1, cumplida.** Quitar las siete columnas de umbral derrumba el
modelo: de 515 a **411** a 1 866 alertas, por debajo del 452 declarado, y a
tiro de los 388 del banco. En el presupuesto del canal ajustado la caída es de
385 a 283.

**Predicción 2, cumplida y por mucho.** Sin los umbrales, el bloque G suma
**+116 inicios** (411 → 527), contra los 32 que exigía el criterio y contra los
+4 que suma cuando los umbrales están presentes. En el presupuesto del canal
ajustado, +105 (283 → 388).

## Lo que esto explica, que es todo

**El bloque G no es una mejora: es un sustituto de una columna faltante.**

El modelo del banco no podía ver el umbral del canal. G se lo daba, codificado
como distancia relativa. Por eso allá valía +79 inicios. El modelo del pipeline
tiene los umbrales en su contrato canónico, así que G le repite algo que ya
sabe, y por eso no vale nada: +2 sobre la logística (tanda 11) y entre −2 y +12
sobre los árboles (tanda 12).

La prueba está en que **G recupera casi exactamente lo que quitar los umbrales
destruye**: 283 → 388 contra los 385 del modelo que sí los tiene. No es que el
bloque agregue información nueva; es que vuelve a meter la que se había sacado.

Vale anotar un matiz, sin sobreleerlo: sin umbrales y con bloque (527) queda
apenas por encima de con umbrales y sin bloque (515), y las dos diferencias
contra 519 están dentro de lo que la regla 9 no deja reportar. La lectura
prudente es que **la información es la misma y la representación casi no
importa**; la lectura tentadora —que el cociente es mejor que los números
crudos para un árbol— necesitaría cinco semillas antes de escribirse.

## Veredicto de la línea U

**El banco queda explicado en su mecanismo.** La distancia de 127 inicios es, en
su mayor parte, las siete columnas de umbral que el `features.csv` del replay no
traía: quitarlas lleva el modelo de 515 a 411, y los 23 que faltan para los 388
del banco caben de sobra en las otras diferencias del `features.csv`, que son
muchas más que las siete.

**Y la línea G queda cerrada, con explicación.** No se cierra por no reproducir:
se cierra porque **se entiende qué medía**. G aporta cuando el modelo es ciego al
umbral y no aporta cuando no lo es. La tanda 5 y la tanda 7 midieron bien sobre
un modelo ciego; lo que no era válido era extrapolar ese aporte a un modelo que
ve los umbrales, y el contrato canónico del pipeline los ve.

Consecuencia directa para el informe: **la configuración declarada vigente tras
la tanda 5 —el modelo con el bloque G— es equivalente a darle al modelo las
columnas de umbral que el canon ya tiene.** No hay nada que portar. Lo que hay
que reportar es el modelo canónico sin bloque, y entre los medidos el mejor es
la logística sin clima.

## Qué quedó del orden anterior




Quedan dos diferencias: los insumos (29 variables sin clima contra las 33 del
contrato) y el reparto de alertas (cupo mensual contra volumen igualado).

**Se cambia el orden declarado en esta preinscripción, y la razón se escribe
antes de medir:** la siguiente corrida es el **reparto de alertas**, no los
insumos. El motivo es mecánico. El cupo mensual del banco obliga a repartir las
alertas parejo entre los doce meses; el retroanálisis deja que el umbral las
concentre donde la probabilidad es alta, que es justamente donde el brote está
ocurriendo. Un instrumento que gasta el mismo número de alertas en un mes de
enero tranquilo que en el pico de la epidemia tiene que detectar menos inicios,
y esa pérdida crece con lo estacional que sea el fenómeno. Después de la tanda 6
sabemos que este lo es bastante.

Criterio, declarado igual que el anterior: el reparto explica la distancia si
imponer el cupo mensual baja el brazo sin bloque de 515 a **452 o menos** en
T+1 a 1 866 alertas; no la explica si queda en **483 o más**; en medio es
parcial. Si tampoco la explica, quedan los insumos, y si los insumos tampoco,
hay que volver a leer el script del banco buscando una cuarta diferencia que no
vimos.
