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

**4 de noviembre de 2026 — se propone revisar los criterios de la compuerta G5.**

*Origen:* **después** de ver los resultados de la tanda 5. Se declara así de
forma explícita, y es la razón por la que la propuesta conserva los umbrales
numéricos de la política vigente sin tocarlos y exige controles negativos
obligatorios. El documento completo es `politica-de-decision-v2.md`, con su
versión legible por máquina en `politica-de-decision-v2.json`.

*Motivo:* tres inconsistencias internas de la política vigente, todas
verificables en los artefactos registrados y ninguna que dependa de nuestros
resultados. La línea base es la persistencia, que en T+1 detecta cero inicios
por construcción, de modo que el criterio de detección es vacío y el de falsas
casi insatisfacible. El denominador de la carga de falsas es el número de
alertas que el candidato elige emitir. Y la sensibilidad se mide sobre inicios
mientras la falsa alarma se mide sobre excesos, de modo que una alerta sobre un
municipio ya en exceso cuenta como correcta aunque no pueda detectar ningún
inicio: en la corrida registrada la persistencia acumula 151 alertas contadas
como verdaderas con cero inicios detectados.

*Continuidad con el cambio anterior:* el segundo defecto es la misma
observación que motivó agregar "falsas alarmas por inicio detectado" en la
tanda 2, cuando se escribió que la tasa premia diluir y que la métrica debía ser
invariante al volumen. Entonces se aplicó a nuestra métrica de trabajo; ahora se
aplica a la política de gobernanza. No es una crítica nueva inventada para la
ocasión.

*Qué no cambia:* nada de lo ya decidido. El `NOT_APPROVED` del 21 de octubre se
conserva con su autoridad y su motivo. La política vigente sigue siendo v1
hasta que la autoridad decida. El tablero desplegado no se toca. Y los umbrales
de 10,0 y 5,0 se conservan deliberadamente, porque elegir números después de
ver resultados es exactamente lo que esta sección existe para impedir.

*Autocrítica que la propuesta incorpora:* se midió cada cambio por separado y
**dos de los tres, aislados, producen una compuerta inservible** —cambiar solo
el evento de verdad hace que "alertar sobre todo" apruebe en los tres cortes—.
Los controles negativos detectaron eso. Es la evidencia de que el conjunto es
mínimo y coherente y no una colección de ajustes convenientes.

**4 de noviembre de 2026 — el canal endémico se publica como fila de
referencia en la comparación del tablero.**

*Origen:* **después** de ver los resultados, y por una pregunta de lectura, no
de medición: la comparación publicada mostraba al modelo contra la
persistencia, que en T+1 detecta cero inicios por construcción, de modo que la
pantalla hacía ver bien al modelo por una razón que no tiene nada que ver con
el modelo.

*Qué se agrega:* una fila con rol `REFERENCE` por horizonte, marcada con
`source: "computed_from_panel"` para distinguirla de las que vienen de la
corrida evaluada. No se recalcula ninguna métrica existente ni se toca la
corrida: la persistencia sigue publicada como `BASELINE` con sus mismos
números, porque es la línea base que declaró la evaluación.

*Definición:* alerta si los casos observados del municipio en el mes de aviso
superan su P75 del mes, con el mismo canal que usa el proyecto. El acierto se
cuenta contra inicio, no contra exceso, sobre exactamente las mismas filas del
panel que evaluó a los modelos.

*Trampa aritmética que costó una corrección:* en el panel `y_t1[m]` codifica
exceso en `m+1`, de modo que el exceso del mes anterior al objetivo vive en
`y_t1[objetivo − 2]`, no en `objetivo − 1`. Con el desplazamiento equivocado la
definición de inicio daba 0 de 86 en los dos horizontes. Los números
publicados se reconciliaron después contra un recuento independiente en pandas.

*Resultado, que no favorece al modelo:* en T+1 el canal anticipa 27 de 86
inicios con 266 alertas y 105 en falso —3,9 falsas por acierto— contra 22 de 86
del XGBoost publicado con 350 alertas y 177 en falso —8,0 por acierto—. El
canal le gana al modelo publicado en los dos ejes. En T+2 el modelo detecta más
—48 contra 44— pero cada acierto le cuesta 6,0 falsas contra 2,9 del canal.

*Qué no contradice:* la mejora de la tanda 5 no está en esta comparación. La
comparación publica la corrida congelada de octubre, que es anterior al bloque
G; el modelo de la tanda 5 no está desplegado ni autorizado.

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

### Tanda 4 — Variables del canal y costo asimétrico

**Hipótesis preinscritas.** Las dos se comparan contra el mejor resultado
vigente: el modelo entrenado sobre la etiqueta de inicio con el presupuesto de
alertas del canal. Solo T+1 decide; T+2 quedó cerrado en la tanda 3.

- *B*: quitar las dos variables derivadas del canal, `zona_canal_t` y
  `zona_canal_lag_1`, debería mejorar la detección de inicios, porque la
  ablación del informe sugiere que empujan hacia la persistencia.
- *D*: entrenar sobre la etiqueta de exceso con las filas de inicio pesadas
  para que cuenten tanto como el resto junto, debería igualar o superar al
  modelo de inicio sin descartar la información de las continuaciones.

También se preinscribió una **contrahipótesis** para B: si el modelo de inicio
usa `zona_canal_t` para excluir las filas ya en exceso, que es lo que insinuó
la tanda 3, quitársela debería empeorarlo.

**Resultado: las dos fracasan, en los tres cortes de T+1.**

| Corte | Estrategia | Alertas | Falsas | Inicios | Cobertura | Falsas/inicio |
| --- | --- | --- | --- | --- | --- | --- |
| 2018-12 | canal endémico | 208 | 27 | 17/60 | 28 % | 1,59 |
| | **inicio (vigente)** | 69 | 35 | **34/60** | **57 %** | **1,03** |
| | B · sin canal | 69 | 42 | 17/60 | 28 % | 2,47 |
| | D · costo asimétrico | 69 | 5 | 2/60 | 3 % | 2,50 |
| 2022-12 | canal endémico | 204 | 27 | 14/57 | 25 % | 1,93 |
| | **inicio (vigente)** | 96 | 56 | **40/57** | **70 %** | **1,40** |
| | B · sin canal | 96 | 53 | 27/57 | 47 % | 1,96 |
| | D · costo asimétrico | 96 | 14 | 6/57 | 11 % | 2,33 |
| 2024-06 | canal endémico | 203 | 60 | 21/48 | 44 % | 2,86 |
| | **inicio (vigente)** | 203 | 148 | **48/48** | **100 %** | 3,08 |
| | B · sin canal | 203 | 130 | 33/48 | 69 % | 3,94 |
| | D · costo asimétrico | 203 | 82 | 27/48 | 56 % | 3,04 |

**B: se cumple la contrahipótesis, no la hipótesis.** Quitar las dos variables
del canal reduce la detección de inicios a la mitad y encarece cada inicio. En
2018-12 el modelo pasa de 34 inicios a 17, exactamente los mismos que detecta
el canal por sí solo.

Esto cierra el razonamiento que empezó en la tanda 3. Allí se vio que el modelo
de inicio ya se estratifica solo, colocando todas sus alertas en filas que no
están en exceso. Aquí se ve **con qué lo hace**: con `zona_canal_t`. Sin esa
variable pierde la capacidad de distinguir dónde un inicio es posible.

**Y matiza la ablación del informe.** El informe de avance reporta que el
modelo sin variables del canal detecta más inicios a igual tasa de falsas
alarmas, 63 contra 56. Eso se midió con el objetivo de **exceso**, donde las
variables del canal efectivamente arrastran hacia la persistencia. Con el
objetivo de **inicio** las mismas variables cumplen el papel contrario: son las
que permiten excluir las continuaciones. La misma variable, dos roles opuestos
según qué se esté optimizando. Es un matiz que el informe final debería
recoger, porque la lectura literal de la ablación lleva a la decisión
equivocada.

**D: el costo asimétrico no reemplaza al cambio de etiqueta.** Con los inicios
pesados ocho veces, el modelo sigue comportándose como un detector de
continuaciones: en 2018-12 emite 69 alertas con solo 5 falsas, precisión
altísima, y detecta 2 inicios de 60. Pesar las filas cambia la función de
pérdida pero no la etiqueta: las continuaciones siguen siendo positivas y
siguen dominando. Alinear el objetivo requiere cambiar qué se predice, no
cuánto pesa cada fila.

**Veredicto.** Las líneas B y D se cierran.

### Tanda 5 — Lo que el modelo no puede ver

**Por qué se reabre el ciclo.** La condición de parada se activó en la tanda 4
y sigue siendo válida para lo que la activó. Las cuatro familias probadas hasta
ahí eran variaciones de **cómo se entrena y cómo se fija el umbral** sobre la
misma matriz de 29 variables. Esta tanda no reintenta ninguna: cambia **qué ve
el modelo**, que es el mecanismo nuevo que la regla de parada exige para
reabrir.

**El inventario que la motiva.** Comparando las 29 columnas de la matriz
preparada contra las 51 del panel, el modelo nunca recibe la variable de
decisión del canal endémico. Tiene `zona_canal_t`, una categoría de tres
niveles sobre el mes en curso, y el conteo de casos con sus rezagos. Pero el
umbral del canal es específico de cada municipio y de cada mes calendario, y no
está en la matriz. El modelo no puede calcular a qué distancia está un
municipio del umbral del mes siguiente, que es precisamente la pregunta que se
le hace. Faltan además tres bloques: nada espacial, en una enfermedad
transmitida por vector; nada de memoria más allá de un mes; y nada que trate el
cruce del umbral como un fenómeno continuo. La estacionalidad sí está
(`mes_sin`, `mes_cos`) y por eso no se propone.

**Hipótesis preinscritas**, todas contra el vigente (etiqueta de inicio, todas
las variables, presupuesto del canal) y solo en T+1:

- *G · margen al umbral*: dar el margen continuo contra el umbral del mes
  objetivo y del mes en curso, la posición dentro de la banda P25–P75, y la
  velocidad de acercamiento. Un inicio es el cruce de un umbral, y un cruce se
  predice con posición y velocidad.
- *H · presión epidémica regional*: fracción de los otros municipios del
  departamento en exceso (dejando fuera al propio), y la misma señal sobre los
  cinco municipios cuya historia de exceso más correlaciona con la del
  municipio, elegidos solo con datos de entrenamiento. Sustituto de adyacencia
  geográfica, porque el panel no trae coordenadas.
- *I · memoria y agotamiento de susceptibles*: meses desde el último exceso,
  excesos en los últimos 12 y 24 meses, duración de la racha actual en calma.
- *J · regresión sobre el margen*: mecanismo, no feature. Se predice el margen
  continuo del mes objetivo y se ordena por margen predicho entre las filas que
  no están en exceso. Es la alternativa estructural a cambiar la etiqueta,
  después de que la tanda 4 mostró que cambiar el peso no sirve.

Cada una se preinscribió con su **contrahipótesis**. La de G es la más
importante: el margen contra el umbral objetivo *es* la regla del canal, y el
canal detecta pocos inicios, así que dársela podría arrastrar al modelo hacia
el comportamiento del canal y empeorarlo.

**Comprobación de fuga previa.** La columna `history_periods_used_t1` lista los
periodos con que se construye cada umbral: los cinco mismos meses calendario de
años anteriores, estrictamente previos al mes de referencia. Se verificó además
que `p75_canal_t[t] == p75_t1[t-1]`. Usar el umbral como variable es tan
legítimo como que el canal lo use para alertar.

**Guarda contra la comparación múltiple, preinscrita.** Cinco comparaciones
(cuatro hipótesis más la combinación) contra el mismo vigente, con una barra de
2 de 3 cortes, hacen que ganar por ruido no sea despreciable. Toda variante que
pase la barra queda como **candidata**, no como mejora confirmada, y para
confirmarse debe además ir en la misma dirección en el corte 2020-12 —excluido
por tamaño de muestra y usado solo como chequeo de dirección, nunca como
voto— y mostrar las features nuevas entre las que el modelo realmente usa.

#### Resultado: G mejora, y es la primera mejora confirmada del ciclo

| Corte | Estrategia | Alertas | Falsas | Inicios | Cobertura | Falsas/inicio |
| --- | --- | --- | --- | --- | --- | --- |
| 2018-12 | canal endémico | 208 | 27 | 17/60 | 28 % | 1,59 |
| | vigente | 69 | 36 | 33/60 | 55 % | 1,09 |
| | **G · margen al umbral** | 69 | 27 | **42/60** | **70 %** | **0,64** |
| | H · presión regional | 69 | 41 | 28/60 | 47 % | 1,46 |
| | I · memoria | 69 | 35 | 34/60 | 57 % | 1,03 |
| | G+H+I | 69 | 29 | 40/60 | 67 % | 0,72 |
| | J · regresión (acotada) | 69 | 28 | 41/60 | 68 % | 0,68 |
| | J · regresión (libre) | 69 | 0 | 0/60 | 0 % | — |
| 2022-12 | canal endémico | 204 | 27 | 14/57 | 25 % | 1,93 |
| | vigente | 96 | 58 | 38/57 | 67 % | 1,53 |
| | **G · margen al umbral** | 96 | 46 | **49/57** | **86 %** | **0,94** |
| | H · presión regional | 96 | 58 | 38/57 | 67 % | 1,53 |
| | I · memoria | 96 | 58 | 38/57 | 67 % | 1,53 |
| | G+H+I | 96 | 48 | 48/57 | 84 % | 1,00 |
| | J · regresión (acotada) | 96 | 51 | 45/57 | 79 % | 1,13 |
| | J · regresión (libre) | 96 | 3 | 0/57 | 0 % | — |
| 2024-06 | canal endémico | 203 | 60 | 21/48 | 44 % | 2,86 |
| | vigente | 203 | 150 | 48/48 | 100 % | 3,12 |
| | G · margen al umbral | 203 | 148 | 48/48 | 100 % | 3,08 |
| | G+H+I | 203 | 148 | 48/48 | 100 % | 3,08 |
| | J · regresión (acotada) | 191 | 143 | 48/48 | 100 % | 2,98 |

**Veredicto en T+1.** G pasa la barra en 2 de 3 cortes; G+H+I y J acotada
también, en 2 de 3. H falla (0 de 3) e I falla (1 de 3).

El tercer corte, 2024-06, **no es una derrota de G: es un techo.** El vigente
ya detecta 48 de 48 inicios, así que "más inicios" es imposible por
construcción; G empata en el techo y cuesta marginalmente menos (3,08 contra
3,12). Se reporta así y no como una victoria, porque la regla preinscrita exige
*más* inicios.

**G queda confirmada**, porque cumple las dos condiciones de la guarda:

- *Dirección en 2020-12*: 8 inicios contra 6 del vigente, a 12,25 contra 16,67
  falsas por inicio. Mismo sentido.
- *Mecanismo legible*: `margen_curso` y `margen_objetivo` son la primera y
  segunda variable por ganancia en los cuatro cortes (11–13 % y 9–11 %), y al
  entrar desplazan a `zona_canal_t`, que cae del 23–29 % al 3–9 %. O sea que el
  modelo sustituye la categoría de tres niveles por la versión continua de la
  misma información, que es exactamente el mecanismo propuesto.

**H falla y la contrahipótesis explica por qué.** `presion_vecinos` sí aparece
alta en la ganancia (8–12 %), o sea que el modelo la usa, pero el resultado
empeora. Con dos departamentos el agregado toma pocos valores por mes y lo que
el modelo aprende de él no ordena municipios dentro de un mes: gasta capacidad
en una señal que no discrimina donde hace falta discriminar. La señal espacial
puede existir; esta forma de medirla no sirve.

**I falla pese a ser la más usada.** `racha_calma` y `meses_desde_exceso` se
llevan 15–18 % y 12–14 % de la ganancia, y el resultado es idéntico al vigente
en 2022-12 y apenas mejor en 2018-12. Que una variable se use mucho no quiere
decir que aporte: lo más probable es que esté codificando la identidad del
municipio, que el modelo ya tenía por el nivel de casos.

**J: el mecanismo no se puede acreditar.** J acotada pasa la barra, pero fue
construida **sobre el bloque G**, porque el margen es lo que define su objetivo.
Comparar J contra el vigente mezcla dos cambios a la vez. La comparación que
aísla el mecanismo es J contra G, y ahí J pierde en los dos cortes que deciden
(41 contra 42, y 45 contra 49). La regresión no aporta sobre la clasificación;
lo que aportaba eran las variables. Defecto de diseño propio, y por eso J no se
cuenta como mejora.

Y J libre confirma su contrahipótesis de forma total: **0 inicios** en dos
cortes. Los márgenes predichos más altos son los municipios que ya están en
exceso, donde un inicio es imposible por definición. El regresor ordena bien la
magnitud y pésimo el cruce.

#### Verificación de G

*Estabilidad ante la semilla*, cinco semillas, T+1, inicios detectados como
mediana y rango:

| Corte | Inicios reales | Vigente | G |
| --- | --- | --- | --- |
| 2018-12 | 60 | 34 [32–34] a 1,03 | **42 [42–44] a 0,64** |
| 2022-12 | 57 | 38 [38–38] a 1,53 | **49 [48–49] a 0,94** |
| 2024-06 | 48 | 48 [48–48] a 3,08 | 48 [48–48] a 3,08 |

G nunca queda por debajo del vigente en ninguna de las 15 corridas, y queda
estrictamente por encima en 10; los 5 empates son el techo de 2024-06. No es
una semilla con suerte.

*Descomposición del bloque*, para no atribuirle a "G" más de lo que hace
(semilla 7, T+1, inicios a falsas por inicio):

| Subconjunto | 2018-12 | 2022-12 | 2024-06 |
| --- | --- | --- | --- |
| vigente | 33 a 1,09 | 38 a 1,53 | 48 a 3,12 |
| **solo `margen_objetivo`** | **45 a 0,53** | **49 a 0,96** | 48 a 3,12 |
| solo `margen_curso` | 36 a 0,92 | 42 a 1,29 | 48 a 3,10 |
| niveles (los tres) | 44 a 0,57 | 48 a 0,98 | 48 a 3,04 |
| velocidades (las tres) | 39 a 0,77 | 43 a 1,23 | 48 a 3,06 |
| G completo (seis) | 42 a 0,64 | 49 a 0,94 | 48 a 3,08 |

**Una sola variable carga el resultado**, y es el margen contra el umbral del
mes **objetivo**. Sola llega a 45 de 60 inicios a 0,53 falsas por inicio, mejor
que el bloque completo de seis. El margen contra el umbral del mes **en curso**
hace mucho menos (36), lo que tiene sentido: la etiqueta está definida por el
umbral del mes objetivo, no del mes en curso.

#### Definición exacta de las variables del bloque G

Se escriben aquí para que el bloque sea reimplementable desde este documento.
Todas se calculan sobre el mes de referencia `t`, con `casos` el total de
notificaciones del mes y `h` el horizonte en meses. Los umbrales son columnas
del panel: `p75_t{h}` es el P75 del mes objetivo y `p25_canal_t` / `p75_canal_t`
son la banda endémica del mes en curso.

```
margen_objetivo      = (casos[t] - p75_t{h}[t]) / (p75_t{h}[t] + 1)
margen_curso         = (casos[t] - p75_canal_t[t]) / (p75_canal_t[t] + 1)
pos_banda            = (casos[t] - p25_canal_t[t]) / (p75_canal_t[t] - p25_canal_t[t] + 1)
margen_objetivo_vel  = margen_objetivo[t] - margen_objetivo[t-1]
margen_curso_vel     = margen_curso[t]    - margen_curso[t-1]
margen_curso_acel    = margen_curso_vel[t] - margen_curso_vel[t-1]
```

El `+1` del denominador evita la división por cero en municipios con umbral
cero y deja la escala en unidades de umbral. La línea base del canal endémico
alerta exactamente cuando `margen_objetivo > 0`, de modo que la variable es esa
regla medida en magnitud en vez de en signo.

**Prueba anti-fuga aplicada a estas variables.** Se construyó la tabla completa
y una recortada en un mes de corte, y se exigió igualdad exacta en todos los
meses anteriores al corte: una variable sin fuga da el mismo valor en el mes `t`
exista o no el futuro. Las quince variables de las tres hipótesis pasaron en los
dos horizontes.

**Dónde está el código.** Los scripts de las cinco tandas no se publican en este
repositorio; son material de trabajo del autor y quedan disponibles a petición.
Lo que sí está completo aquí es el diseño de cada experimento, las definiciones
de arriba y los resultados por celda, que es lo que permite auditar el método y
rehacerlo. La corrida exacta además depende de artefactos de datos de 1,6 GB que
no son públicos, así que ni publicando los scripts sería reproducible tal cual.

**La lectura de fondo.** El canal endémico no era un competidor del modelo: era
una variable que al modelo le faltaba. `margen_objetivo` es la regla de
decisión del canal convertida de signo en magnitud —el canal alerta cuando esta
cantidad pasa de cero— y el modelo, al recibirla, aprende dónde en esa escala
ocurren de verdad los inicios, que es justo por debajo del umbral y subiendo.
Nueve tandas de variaciones sobre el entrenamiento y el umbral no habían
movido nada; darle al modelo la variable que el canal usa, sí.

**Nota sobre la versión mínima.** Que `margen_objetivo` sola sea mejor que el
bloque completo se descubrió **después** de mirar los resultados, así que
adoptarla como vigente sería elegir el mejor subconjunto a posteriori, que es
exactamente lo que las reglas de esta bitácora prohíben. Lo confirmado es el
bloque G tal como se preinscribió, y es el bloque G el que pasa a ser el
vigente. La versión mínima queda preinscrita para la tanda siguiente.

#### Diagnóstico: ¿esta mejora acerca algo a la compuerta G5?

Pregunta que surgió al reportar la tanda 5 y que obligó a leer la política de
decisión del artefacto en vez de citarla de memoria. El archivo es
`docs/product/stage-5/champion_decision_policy_v1.json`, con SHA-256
`29b5d6d7…`, y sus criterios son explícitos:

| Elemento | Valor |
| --- | --- |
| Línea base de comparación | **persistencia**, no el canal endémico |
| Ganancia mínima de sensibilidad de inicios | 10 pp, sobre la **cota inferior** del intervalo |
| Aumento máximo de la razón de falsas | 5 pp, sobre la **cota superior** del intervalo |
| Razón de falsas | falsas / **alertas emitidas** |
| Métrica de ranking | precisión promedio; AUROC solo complementario |
| Decisión registrada | `NOT_APPROVED`, autoridad Mauricio, 21 de octubre de 2026 |
| Motivo registrado | los seis procedimientos candidato/horizonte excedieron la restricción de aumento de falsas en la comparación 2025 |

**Primero, lo que `NOT_APPROVED` no significa.** No es un veredicto sobre el
modelo de la tanda 5, que nunca se presentó a la compuerta y por lo tanto no
tiene estado en ella. Es una decisión humana sobre los seis candidatos de la
corrida registrada, medidos sobre el bloque 2025, que es evidencia consumida
(regla 4.1) y no se vuelve a medir aquí.

**Segundo, el modelo de la tanda 5 tampoco pasaría, y por mucho.** Medido con
la métrica y la línea base de la compuerta sobre los cortes de validación
propios, con remuestreo por mes:

| Corte | Estrategia | Alertas | Sensibilidad | Razón FA | Ganancia pp [IC] | FA pp [IC] | G5 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2018-12 | persistencia | 207 | 0 % | 15,9 % | referencia | | |
| | vigente | 69 | 55 % | 52,2 % | 55,0 [48,2; 63,1] | 36,2 [27,6; 44,8] | no |
| | G | 69 | 70 % | 39,1 % | 70,0 [65,5; 77,4] | 23,2 [16,5; 27,6] | no |
| | canal endémico | 208 | 28 % | 13,0 % | 28,3 [16,1; 40,7] | −3,0 [−6,5; 2,4] | **PASA** |
| 2022-12 | persistencia | 215 | 0 % | 19,1 % | referencia | | |
| | G | 96 | 86 % | 47,9 % | 86,0 [81,9; 93,8] | 28,8 [21,8; 36,5] | no |
| | canal endémico | 204 | 25 % | 13,2 % | 24,6 [13,6; 40,4] | −5,8 [−7,3; −4,3] | **PASA** |
| 2024-06 | persistencia | 189 | 0 % | 32,3 % | referencia | | |
| | G | 203 | 100 % | 72,9 % | 100,0 [100; 100] | 40,6 [33,5; 47,6] | no |
| | canal endémico | 203 | 44 % | 29,6 % | 43,8 [27,3; 61,0] | −2,7 [−7,3; 1,8] | **PASA** |

G mejora el eje de detección de forma abrumadora —70 y 86 puntos sobre la
línea base, contra un mínimo exigido de 10— y falla el de falsas por 23 a 41
puntos sobre un techo de 5. Igual que los seis candidatos: ninguno falló por
detectar poco.

**Tercero, y es el hallazgo: la restricción es estructuralmente insatisfacible
para un detector de inicios.** En T+1 la persistencia detecta **cero inicios por
construcción**: solo alerta donde ya hay exceso, y un inicio exige que no lo
haya. Y precisamente por eso tiene una razón de falsas *baja*, porque "ya está
en exceso, seguirá en exceso" es una predicción fácil y acertada. De modo que
la compuerta compara a todo detector de inicios contra una línea base que es
máximamente precisa y completamente ciega a lo que se quiere detectar. Un
detector de inicios tiene que alertar donde el exceso **todavía no** está, y eso
eleva mecánicamente su razón de falsas. El techo de 5 pp no mide la calidad del
detector: mide cuánto se aleja uno de alertar sobre excesos ya instalados.

**La evidencia que lo prueba: el canal endémico sí pasa G5**, en los tres
cortes, con aumento de falsas *negativo*. Porque el canal, como la
persistencia, alerta sobre todo donde el exceso ya está. La compuerta tal como
está escrita es satisfacible por reglas que se parecen a la persistencia y
prácticamente insatisfacible por reglas que de verdad detectan inicios.

**Y la razón de falsas depende del volumen de alertas que uno elige.** G emite
69 alertas con 27 falsas; el canal emite 208 con 27 falsas. Las mismas falsas en
términos absolutos, la misma carga real sobre el sistema de salud, y una razón
de 39 % contra 13 % solo porque el denominador es el número de alertas que uno
decidió emitir. Un modelo que alerta poco y bien queda castigado por esta
métrica.

**Qué no se concluye de esto.** Que la restricción esté mal pensada. El
cansancio por falsas alarmas es real y "qué fracción de las alertas que recibo
son falsas" es una preocupación operativa legítima. El problema no es la
métrica sola: es la combinación de esa métrica con una línea base ciega al
objetivo. Y esto **no autoriza a cambiar la métrica para ganar**, que es lo que
la sección 3 de esta bitácora prohíbe. Lo que corresponde es documentar el
hallazgo y dejarlo como recomendación para quien tiene la autoridad de la
compuerta, que según el artefacto es Mauricio.

**Límites de este diagnóstico.** Se midió sobre los cortes de validación
propios, no sobre el bloque 2025 de la compuerta, que es evidencia consumida. El
intervalo es un remuestreo por mes construido aquí, que reproduce la forma de la
regla pero no necesariamente el procedimiento exacto de la corrida registrada.
Es un diagnóstico, no una presentación a la compuerta.

**Qué se hizo con esto.** El diagnóstico derivó en una propuesta formal de
revisión de los criterios, que vive en `politica-de-decision-v2.md` y
`politica-de-decision-v2.json`, con el registro del cambio en la sección 3 de
esta bitácora. Resumen de lo que resultó: bajo los criterios revisados el modelo
de la tanda 5 aprueba en los 3 cortes de T+1, el modelo de la tanda 4 en 2 de 3,
el modelo deliberadamente degradado en 0 de 3, y los cuatro controles negativos
—persistencia, ranking aleatorio, alertar sobre todo y canal inflado con alertas
al azar— en 0 de 3. En T+2 no aprueba nadie, y el veredicto de tres valores
aclara que es por ancho de intervalo con 37 a 48 inicios, no por desempeño. La
propuesta no está vigente: la decisión es de la autoridad declarada en el
artefacto.

**T+2 vuelve a estar en duda.** T+2 se cerró en la tanda 3 porque ninguna
configuración superaba al canal de forma consistente a dos meses. Con G, en
T+2, se detectan 20 contra 10 inicios en 2018-12, 20 contra 18 en 2022-12 y 28
contra 23 en 2024-06, siempre más barato, y en 2022-12 G supera al canal en los
dos ejes a la vez (20 a 0,85 contra 14 a 1,43). Esto **no decide nada**, porque
la preinscripción de esta tanda dice que solo T+1 decide y T+2 es informativo.
Lo que hace es dar el mecanismo nuevo que las reglas exigen para reabrir una
línea cerrada, y por eso T+2 se reabre como hipótesis preinscrita, no como
resultado.

---

## 6. Estado de las líneas de trabajo

| Línea | Estado |
| --- | --- |
| Objetivo de entrenamiento sobre el inicio | Confirmada en ordenamiento; insuficiente por sí sola |
| A. Umbral por tasa en vez de valor | **Cerrada**: rechazada en la tanda 2 |
| F. Presupuesto de alertas | **Resuelta**: confirmada en T+1, rechazada en T+2 |
| B. Entrenar sin las variables del canal | **Cerrada**: rechazada en la tanda 4; esas variables son necesarias |
| C. Modelo en dos etapas | **Cerrada**: rechazada en la tanda 3; el modelo ya estratifica solo |
| D. Costo asimétrico en el entrenamiento | **Cerrada**: rechazada en la tanda 4 |
| G. Margen continuo al umbral del canal | **Confirmada** en la tanda 5; pasa a ser el vigente |
| H. Presión epidémica regional | **Cerrada**: rechazada en la tanda 5 con esta forma de medirla |
| I. Memoria y agotamiento de susceptibles | **Cerrada**: rechazada en la tanda 5 |
| J. Regresión sobre el margen | **Cerrada**: no aporta sobre la clasificación |
| E. Variables demográficas y sociales | Abierta, en curso por otro integrante |
| K. Versión mínima de G (una sola variable) | Preinscrita para la tanda 6 |
| L. Reapertura de T+2 con el margen | Preinscrita para la tanda 6 |

**Horizonte T+2.** Se cerró tras la tanda 3 y **vuelve a estar en duda** tras la
tanda 5: con el margen al umbral, G detecta más inicios y más barato en los tres
cortes de T+2, y en 2022-12 supera al canal en los dos ejes. Se reabre como
hipótesis preinscrita (línea L), no como resultado, porque la preinscripción de
la tanda 5 establecía que solo T+1 decide.

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

**Esa condición se cumplió en la tanda 4** y el ciclo se cerró ahí: la tanda 3
cerró la línea C y la tanda 4 cerró B y D, dos tandas seguidas sin mejora.

**Y se reabrió en la tanda 5**, por la vía que las propias reglas dejan
abierta: un mecanismo nuevo. Las cuatro líneas cerradas hasta la tanda 4 eran
variaciones de cómo se entrena y cómo se fija el umbral sobre la misma matriz;
la tanda 5 cambió qué ve el modelo. Produjo mejora confirmada, así que el
contador de tandas consecutivas sin mejora vuelve a cero.

La configuración vigente pasa a ser: **modelo entrenado sobre la etiqueta de
inicio, con las 29 variables de la matriz preparada más el bloque G del margen
al umbral, operado al presupuesto de alertas del canal endémico medido en la
partición interna, horizonte T+1.** Detecta el 70 %, el 86 % y el 100 % de los
inicios en los tres cortes evaluables, contra el 28 %, 25 % y 44 % del canal
endémico, y con menos falsas alarmas por inicio en los tres. Sigue siendo un
resultado de evaluación y no un sistema de alertas autorizado: la compuerta G5
permanece en `NOT_APPROVED` y el tablero desplegado publica la evaluación
congelada, no este modelo.

**La lección de método, que vale más que el resultado.** El ciclo se había
cerrado correctamente y por las razones correctas: nueve variaciones sobre el
entrenamiento y el umbral, todas sin efecto. Lo que faltaba no era otra
variación: era revisar el inventario de lo que el modelo podía ver. Cuando una
familia entera de intentos no mueve nada, la pregunta siguiente no es cuál
variante falta, sino qué información no está entrando.

No se abren tandas nuevas sin un mecanismo nuevo preinscrito o sin los datos de
la línea E.

**Qué no cuenta como mejora:** ganar AUROC global perdiendo inicios; ganar en
una celda y perder en otras tres; ganar bajando el umbral, que es alertar más y
no detectar mejor; ganar contra la persistencia pero no contra el canal.

**Si nada funciona**, es un resultado. Que cuatro familias de modelos no
superen al canal endémico en la detección de inicios, con este aparato de
validación, es un hallazgo publicable y no un fracaso.
