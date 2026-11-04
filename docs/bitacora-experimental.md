# Bitácora experimental

Registro público de la experimentación sobre el sistema de alerta temprana.
Cada tanda deja aquí su hipótesis, lo que se corrió, los resultados y el
veredicto, **incluyendo lo que no funcionó**. Un experimento que no quedó
escrito no cuenta.

Este archivo se actualiza en cada prueba, análisis, resultado y decisión. Es la
trazabilidad del trabajo: si una cifra del informe no se puede rastrear hasta
una entrada de aquí, esa cifra no está sustentada.

---

## 1. El problema

En Colombia el dengue se vigila con el **canal endémico**: se comparan los
casos del mes contra los percentiles históricos del mismo municipio y el mismo
mes calendario. Es una herramienta retrospectiva. Dice que el municipio ya está
en exceso, no que va a estarlo.

El sistema busca anticipar. Para cada par municipio-mes se estima la
probabilidad de que el mes siguiente (T+1) o el subsiguiente (T+2) supere el
percentil 75 del canal endémico de ese municipio.

### Definiciones

| Término | Definición |
| --- | --- |
| **Exceso** en `p` | Los casos de `p` superan el P75 del canal de ese municipio para ese mes calendario |
| **Inicio de brote** en `p` | Hay exceso en `p` **y no** hay exceso en `p-1`. Si el estado de `p-1` es desconocido, el inicio no es evaluable |
| **Falsa alarma** | Se emitió alerta y no hubo exceso |
| **Tasa de falsas alarmas** | Falsas alertas sobre el total de alertas emitidas |

La distinción entre inicio y continuación es el centro del trabajo. Un brote ya
empezado lo detecta cualquiera, incluido el canal. El valor está en anticipar
el que todavía no empieza.

### Criterio de utilidad

Fijado en la propuesta de grado, antes de cualquier experimento:

1. Detectar una fracción apreciable de los **inicios**, no solo de los meses en
   exceso.
2. Superar al **canal endémico** y a la **persistencia** sobre exactamente las
   mismas filas.
3. Mantener la tasa de falsas alarmas dentro de **cinco puntos porcentuales**
   por encima de la del canal.

---

## 2. Experimento base

Todo se compara contra esto.

**Datos.** Panel mensual de los 76 municipios de Tolima y Meta. Matrices
preparadas por el pipeline de Kedro del repositorio científico, con 28
variables: conteos de dengue y dengue grave, nueve climáticas mensuales, zona
del canal, rezagos de casos y de grave, cambio a un mes, media de tres meses,
zona del canal rezagada, rezagos de lluvia, temperatura, rocío y escorrentía, y
estacionalidad en seno y coseno.

**Particiones.** Cuatro cortes de ventana expansiva: 2018-12, 2020-12, 2022-12
y 2024-06, en los dos horizontes. El corte más reciente tiene 11.400 filas de
entrenamiento y 456 de validación.

**Líneas base, calculadas sobre exactamente las mismas filas evaluables:**

- *Canal endémico*: alerta si los casos del mes en curso ya superan el P75 del
  mes objetivo.
- *Persistencia*: alerta si el mes en curso ya está en exceso.

**Resultado base.** La evaluación congelada del repositorio científico, que es
la que publica el tablero desplegado, dejó las seis combinaciones
candidato-horizonte en `does_not_meet`. XGBoost en T+1 alcanza AUROC 0,819 y
average precision 0,676, con 50,6 % de falsas alarmas y 25,6 % de sensibilidad
de inicios. El canal no es superado.

---

## 3. Métricas

### Vigentes

| Métrica | Qué responde |
| --- | --- |
| **Inicios detectados a presupuesto comparable** | La que decide. ¿Con el mismo esfuerzo operativo, quién anticipa más brotes? |
| Tasa de falsas alarmas | ¿Qué fracción de las alertas emitidas fue en vano? |
| **Falsas alarmas por inicio detectado** | ¿Cuánto cuesta cada brote anticipado? Invariante al volumen de alertas |
| AUROC y average precision sobre inicios | Calidad del ordenamiento, independiente del umbral |
| Brier | Calidad de la probabilidad, no solo del orden |
| Inicios evaluables y reales | Tamaño de muestra; sin esto ninguna cifra se interpreta |

### Historial de cambios de métrica

Un cambio de métrica después de ver resultados es la forma más común de
engañarse. Por eso cada cambio queda aquí con su fecha, su motivo y la
declaración explícita de si nació antes o después de observar un resultado.

**4 de noviembre de 2026 — se agrega "falsas alarmas por inicio detectado".**

*Origen:* nació de una observación de la tanda 2, no de un razonamiento previo.
Se declara así de forma explícita.

*Motivo:* la tasa de falsas alarmas premia diluir. El canal emite unas
doscientas alertas, la mayoría sobre excesos que ya están ocurriendo y que por
eso acierta; esos aciertos fáciles le bajan la tasa. Un modelo que emite setenta
alertas difíciles sale peor en tasa aunque cueste menos falsas alarmas en
términos absolutos. La métrica nueva es invariante al volumen y responde
directamente cuánto cuesta cada brote anticipado.

*Qué no cambia:* la tercera condición de utilidad sigue escrita en tasa de
falsas alarmas y se sigue reportando. La métrica nueva **se agrega**, no
reemplaza. El informe final debe discutir cuál corresponde al problema de
decisión real de una secretaría de salud, que opera con una restricción de
capacidad y no de precisión.

---

## 4. Reglas de método

Sin estas reglas los resultados se ven bien y no valen nada.

1. **El bloque congelado de 2025 es evidencia consumida.** Ya se usó para la
   comparación final. Ninguna tanda lo usa para elegir entre configuraciones.
   Experimentar y comparar se hace sobre los cortes de validación.
2. **El umbral nunca se elige sobre los datos con que se mide.** Se fija sobre
   una partición interna y se aplica tal cual. Siempre se reporta la tasa de
   falsas alarmas **realizada**, no la buscada.
3. **Consistencia entre cortes, no el mejor caso.** Una mejora se declara solo
   si aparece en al menos tres de los cuatro cortes del mismo horizonte. Se
   reportan todas las configuraciones probadas, no solo las que funcionaron.
4. **El tamaño de muestra se declara siempre.** No se concluye nada de celdas
   con menos de 30 inicios evaluables.
5. **La prevalencia cambia entre periodos.** El exceso pasa de 24,0 % en
   entrenamiento a 45,9 % en validación y 53,5 % en prueba. Toda política de
   umbral se evalúa por su estabilidad entre años.
6. **Fuga por la etiqueta.** La etiqueta resulta de comparar casos contra un
   percentil histórico. El canal, la razón de incidencia, la endemicidad y la
   etiqueta se recalculan dentro de cada partición con solo años anteriores.
7. **Las líneas base van sobre las mismas filas.** Toda comparación incluye
   canal y persistencia sobre el mismo conjunto evaluable.
8. **Se preinscribe antes de mirar.** Cada tanda escribe, antes de correr,
   qué hipótesis prueba, qué métrica decide, qué contaría como mejora y qué
   contaría como fracaso.

---

## 5. Registro de tandas

### Tanda 1 — Objetivo de entrenamiento: exceso contra inicio

**Hipótesis.** El informe concluye que el modelo aprendió a prolongar el estado
actual. La asimetría entre lo que se optimiza (exceso en `t+h`) y lo que se
mide (detección de inicios) es la causa, y entrenar directamente sobre el
inicio la corrige.

**Qué se corrió.** XGBoost entrenado dos veces por celda, una con la etiqueta
de exceso y otra con la etiqueta de inicio derivada del panel. Cuatro cortes,
dos horizontes. Medición de detección de inicios sobre validación.

**Resultado.** El objetivo actual está en o por debajo del azar para detectar
inicios.

| Corte | Horizonte | AUROC entrenando en exceso | AUROC entrenando en inicio |
| --- | --- | --- | --- |
| 2018-12 | T+1 | 0,257 | 0,876 |
| 2020-12 | T+1 | 0,562 | 0,573 |
| 2022-12 | T+1 | 0,231 | 0,874 |
| 2024-06 | T+1 | 0,287 | 0,828 |
| 2018-12 | T+2 | 0,313 | 0,655 |
| 2020-12 | T+2 | 0,579 | 0,502 |
| 2022-12 | T+2 | 0,344 | 0,674 |
| 2024-06 | T+2 | 0,452 | 0,613 |

**Interpretación.** El efecto es mecánico. Un inicio implica, por definición,
que el mes anterior **no** estaba en exceso; un modelo entrenado a predecir que
el exceso continúa asigna probabilidad baja justo a los casos que interesan.

**Limitación detectada y corregida.** El umbral se había elegido sobre el mismo
conjunto de validación con que se medía, lo que hacía optimistas los conteos de
inicios detectados. De ahí nació la regla 2. Lo sólido de esta tabla es el
AUROC, que no depende de umbral.

---

### Tanda 1, cierre — Banco de evaluación con umbral fuera de muestra

Se construyó el banco que faltaba: umbral elegido sobre el último año del
entrenamiento como partición interna y aplicado tal cual a validación, con
canal y persistencia sobre exactamente las mismas filas.

**Resultado 1: con umbral desplegable, ningún modelo supera al canal.**

| Corte | T | Canal | XGB exceso | XGB inicio |
| --- | --- | --- | --- | --- |
| 2018-12 | T+1 | 17/60 a 13,0 % | 25/60 a 21,4 % | 26/60 a 50,9 % |
| 2022-12 | T+1 | 14/57 a 13,2 % | 21/57 a 24,5 % | 23/57 a 54,0 % |
| 2024-06 | T+1 | 21/48 a 29,6 % | 16/48 a 38,6 % | 13/48 a 59,4 % |
| 2018-12 | T+2 | 18/48 a 10,9 % | 25/48 a 20,2 % | 19/48 a 35,5 % |
| 2022-12 | T+2 | 14/41 a 13,2 % | 27/41 a 21,7 % | 10/41 a 39,6 % |
| 2024-06 | T+2 | 24/37 a 34,2 % | 20/37 a 43,8 % | 2/37 a 46,2 % |

Inicios detectados y tasa de falsas alarmas realizada. El modelo de inicio
emite muy pocas alertas porque su umbral no transfiere entre particiones.

**Conclusión.** Entrenar sobre el inicio mejora sustancialmente el ordenamiento
de inicios, pero por sí solo y con la política de umbral vigente **no produce
un sistema desplegable**.

---

### Tanda 2 — Política de umbral: valor absoluto contra tasa

**Hipótesis preinscritas.**

- *A*: un umbral definido como fracción de filas alertadas mantiene estable la
  tasa de falsas alarmas entre periodos de prevalencia distinta, donde un valor
  absoluto de probabilidad no lo hace.
- *F*: una política de presupuesto de alertas transfiere entre periodos y
  permite detectar más inicios que el canal al mismo costo operativo.

**Qué se corrió.** Tres políticas, todas con su parámetro fijado solo sobre la
partición interna: *valor*, *tasa propia* y *presupuesto del canal*. Dos
objetivos de entrenamiento, cuatro cortes, dos horizontes. Se excluye 2020-12
por la regla 4: tiene 13 y 14 inicios evaluables.

**A queda rechazada, por la razón contraria a la esperada.**

Amplitud entre el máximo y el mínimo de la tasa de falsas alarmas realizada:

| Candidato | Horizonte | valor | tasa propia | presupuesto |
| --- | --- | --- | --- | --- |
| xgboost · exceso | T+1 | **17,2 %** | 35,0 % | 33,0 % |
| xgboost · exceso | T+2 | **23,6 %** | 39,6 % | 36,6 % |
| xgboost · inicio | T+1 | **8,4 %** | 8,8 % | 22,2 % |
| xgboost · inicio | T+2 | **10,6 %** | 24,5 % | 19,4 % |

La política de valor es más estable en las cuatro combinaciones. El mecanismo:
la escala de la probabilidad **lleva información sobre la prevalencia**. Cuando
el modelo ve un periodo con menos riesgo baja sus probabilidades y alerta
menos, y eso amortigua la tasa. Fijar la fracción de alertas descarta esa señal
y obliga a alertar lo mismo en un año tranquilo que en uno epidémico.

**F queda confirmada en T+1 y rechazada en T+2.**

La fracción del canal medida en la partición interna produce en validación
menos alertas de las que el canal realmente emite, porque la prevalencia
cambia. Al modelo se le dio un presupuesto **más chico** que el del canal:

| Corte | T | Canal: alertas / falsas / inicios | XGB inicio: alertas / falsas / inicios |
| --- | --- | --- | --- |
| 2018-12 | T+1 | 208 / 27 / 17 de 60 | **69 / 35 / 34** |
| 2022-12 | T+1 | 204 / 27 / 14 de 57 | **96 / 56 / 40** |
| 2024-06 | T+1 | 203 / 60 / 21 de 48 | **203 / 148 / 48** |
| 2018-12 | T+2 | 156 / 17 / 18 de 48 | 57 / 22 / 13 |
| 2022-12 | T+2 | 151 / 20 / 14 de 41 | 71 / 30 / 15 |
| 2024-06 | T+2 | 158 / 54 / 24 de 37 | 162 / 94 / 27 |

**Costo por inicio detectado**, la métrica invariante al volumen:

| Corte | T | Canal | Modelo | Gana |
| --- | --- | --- | --- | --- |
| 2018-12 | T+1 | 1,59 | **1,03** | modelo |
| 2022-12 | T+1 | 1,93 | **1,40** | modelo |
| 2024-06 | T+1 | 2,86 | 3,08 | canal |
| 2018-12 | T+2 | 0,94 | 1,69 | canal |
| 2022-12 | T+2 | 1,43 | 2,00 | canal |
| 2024-06 | T+2 | 2,25 | 3,48 | canal |

El modelo gana dos de tres cortes en T+1 y ninguno en T+2.

**Lectura honesta.** En T+1, en 2018-12 y 2022-12 el modelo **domina**: cubre
más del doble de inicios (57 % contra 28 %, y 70 % contra 25 %) y además gasta
menos falsas alarmas por cada inicio que encuentra. En 2024-06 compra cobertura
total pagando más por inicio, lo que es un intercambio defendible pero no
dominancia. En T+2 no gana por ningún lado.

**Nota metodológica.** Una versión preliminar de este análisis destacaba el
corte 2018-12, el más favorable de los seis, como resultado principal. Eso es
exactamente lo que la regla 3 existe para evitar. La tabla completa y la
métrica invariante al volumen corrigen esa lectura.

**Segundo hallazgo: el modelo de exceso es un detector de continuaciones.**
Con presupuesto acotado alcanza tasas de falsas alarmas de 1,4 %, 3,5 %, 6,2 %
y 8,5 %, precisión altísima, y detecta **cero o un inicio**. Concentra toda su
confianza en excesos que ya empezaron.

---

### Tanda 3 — Modelo en dos etapas según el estado del mes en curso

**Hipótesis preinscrita.** Separar el problema en dos según el estado del canal
en el mes de referencia funciona mejor que un solo modelo que atiende las dos
preguntas. Filas ya en exceso: ¿continúa? Filas sin exceso: ¿empieza uno nuevo?
En T+1 el segundo estrato es, por definición, la única población donde un
inicio puede ocurrir.

**Regla de reparto, fijada de antemano.** El presupuesto total es la fracción
de filas que alertó el canal en la partición interna. Se reparte entre los dos
estratos en proporción a su tamaño, o sea la misma tasa de alerta en cada uno.
No se buscó la mejor asignación.

**Criterio de fracaso preinscrito.** Que la combinación no supere al modelo de
inicio único con el mismo presupuesto, que es el mejor resultado vigente.

**Resultado: la hipótesis falla, en las seis celdas.**

| Corte | T | Dos etapas | Canal | Inicio único |
| --- | --- | --- | --- | --- |
| 2018-12 | T+1 | 16/60 a 0,94 | 17/60 a 1,59 | **34/60 a 1,03** |
| 2022-12 | T+1 | 19/57 a 1,42 | 14/57 a 1,93 | **40/57 a 1,40** |
| 2024-06 | T+1 | 33/48 a 2,88 | 21/48 a 2,86 | **48/48 a 3,08** |
| 2018-12 | T+2 | 8/48 a 1,62 | **18/48 a 0,94** | 13/48 a 1,69 |
| 2022-12 | T+2 | 9/41 a 1,56 | **14/41 a 1,43** | 15/41 a 2,00 |
| 2024-06 | T+2 | 18/37 a 4,61 | **24/37 a 2,25** | 27/37 a 3,48 |

Inicios detectados y falsas alarmas por inicio. La combinación nunca supera al
modelo único, y solo domina al canal en uno de los tres cortes de T+1.

**El mecanismo, y es un error de diseño del propio experimento.** El reparto
proporcional asigna el presupuesto según el tamaño de cada estrato, y en estos
datos más de la mitad de las filas ya están en exceso:

| Corte | T+1 | Filas ya en exceso | Cupo gastado en continuaciones |
| --- | --- | --- | --- |
| 2018-12 | | 207 de 380 | 38 de 69 alertas |
| 2022-12 | | 215 de 380 | 54 de 96 alertas |
| 2024-06 | | 189 de 380 | 101 de 203 alertas |

En T+1, **un inicio es imposible en una fila que ya está en exceso**, por la
definición misma de inicio. La regla de reparto preinscrita gastaba alrededor
de la mitad del presupuesto en un estrato con capacidad de detección
estructuralmente nula. El experimento midió bien y la hipótesis cayó, pero cayó
por cómo se repartió el presupuesto y no por la idea de estratificar.

**Variante corregida, y el hallazgo que deja la tanda.** Se probó la versión
que no comete ese error: todo el presupuesto para el modelo de inicio, pero
restringido a alertar solo donde un inicio es posible. No es una búsqueda de la
mejor asignación, es quitar de la lista filas con capacidad nula.

| Corte | T | Inicio único | Inicio acotado |
| --- | --- | --- | --- |
| 2018-12 | T+1 | 69 alertas, 35 falsas, 34 inicios | idéntico |
| 2022-12 | T+1 | 96 alertas, 56 falsas, 40 inicios | idéntico |
| 2024-06 | T+1 | 203 alertas, 148 falsas, 48 inicios | 191 alertas, 143 falsas, 48 inicios |
| 2018-12 | T+2 | 57, 22, 13 | 57, 27, 16 |
| 2022-12 | T+2 | 71, 30, 15 | 71, 33, 21 |
| 2024-06 | T+2 | 162, 94, 27 | 152, 106, 21 |

En T+1 el resultado es **idéntico en tres de cuatro cortes**. El modelo
entrenado sobre el inicio ya coloca por su cuenta todas sus alertas de mayor
probabilidad en filas que no están en exceso: aprendió la estratificación sin
que nadie se la impusiera. En 2024-06 la restricción ahorra cinco falsas
alarmas sin perder un solo inicio, porque el estrato elegible es más chico que
el presupuesto.

**Veredicto. La línea C se cierra.** La estratificación explícita no aporta,
por una razón que es en sí misma el resultado útil de la tanda: el modelo ya la
hace internamente. Imponerla por fuera solo puede restringirlo.

**Sobre T+2.** Estaba preinscrito qué concluir si volvía a perder en todas las
configuraciones. Ocurrió: en dos de los tres cortes el canal domina al modelo
en cobertura y en costo a la vez, y en el tercero hay un intercambio sin
ganador claro. Sumado a las tandas 1 y 2, **a dos meses no hay en estos datos
señal anticipatoria suficiente para superar al canal endémico**. Eso se reporta
como resultado y se deja de buscar por ese lado.

La asimetría estaba advertida en la preinscripción: en T+2 el estrato definido
por el estado del mes en curso es solo una aproximación, porque un inicio en
T+2 exige que T+1 no esté en exceso y T+1 es desconocido al decidir. Esa
aproximación explica por qué la variante acotada se comporta de forma errática
en T+2, mejor en dos cortes y peor en uno, mientras que en T+1 es casi exacta.

---

## 6. Estado de las líneas de trabajo

| Línea | Estado |
| --- | --- |
| Objetivo de entrenamiento sobre el inicio | Confirmada en ordenamiento; insuficiente por sí sola |
| A. Umbral por tasa en vez de valor | **Cerrada**: rechazada en la tanda 2 |
| F. Presupuesto de alertas | **Resuelta**: confirmada en T+1, rechazada en T+2 |
| B. Entrenar sin las variables del canal | Abierta |
| C. Modelo en dos etapas | **Cerrada**: rechazada en la tanda 3; el modelo ya estratifica solo |
| D. Costo asimétrico en el entrenamiento | Abierta |
| E. Variables demográficas y sociales | Abierta, en curso por otro integrante |

**Horizonte T+2.** Cerrado como línea de mejora tras la tanda 3: en tres tandas
ninguna configuración superó al canal endémico de forma consistente a dos
meses. Se reporta como resultado.

---

## 7. Cuándo parar

La experimentación tiene rendimientos decrecientes y el proyecto tiene fecha.

**Una línea se cierra** cuando se probó en los cuatro cortes y no mejora en al
menos tres del mismo horizonte, cuando la mejora es menor que la incertidumbre
del tamaño de muestra, o cuando requiere datos que no estarán disponibles a
tiempo. Una línea cerrada no se reabre sin un mecanismo nuevo.

**El ciclo completo para** cuando dos tandas seguidas cierren todas sus líneas
sin mejora, o cuando falten menos de cinco días para una entrega y haya trabajo
de escritura pendiente.

**Qué no cuenta como mejora:** ganar AUROC global perdiendo inicios; ganar en
una celda y perder en otras tres; ganar bajando el umbral, que es alertar más y
no detectar mejor; ganar contra la persistencia pero no contra el canal.

**Si nada funciona**, es un resultado. Que cuatro familias de modelos no
superen al canal endémico en la detección de inicios, con este aparato de
validación, es un hallazgo publicable y no un fracaso.
