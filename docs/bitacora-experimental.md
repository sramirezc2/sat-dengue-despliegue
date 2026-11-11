# Bitácora experimental

Registro público de la experimentación sobre el sistema de alerta temprana.
Cada tanda deja aquí su hipótesis, lo que se corrió, los resultados y el
veredicto, **incluyendo lo que no funcionó**. Un experimento que no quedó
escrito no cuenta.

Este archivo se actualiza en cada prueba, análisis, resultado y decisión. Es la
trazabilidad del trabajo: si una cifra del informe no se puede rastrear hasta
una entrada de aquí, esa cifra no está sustentada.

---

## 0. Criterio de decisión A/B/C — preinscrito el 10 de noviembre de 2026

> **Esto se fija antes de correr los experimentos de las próximas tres semanas,
> y no se toca después de ver un resultado.** Está arriba del todo porque es lo
> que convierte una corrida en evidencia: sin un criterio escrito antes, cada
> cifra es una anécdota y la discusión se vuelve sobre quién mide mejor.

### Declaración de honestidad, primero

**No elegimos estos umbrales a ciegas, y fingir lo contrario sería peor que no
preinscribir nada.** Cuando se escriben, el proyecto ya conoce los resultados
exploratorios de la tanda 9 sobre el banco propio. La regla 4.8 se cumple aquí
**declarando** esa falta de ceguera, publicando las cifras que ya vimos, y
eligiendo los umbrales por un argumento de utilidad y no por lo que nos da.

Lo que ya sabíamos al escribir esto, T+1 y T+2, banco propio 2018-2024,
647 inicios sobre 6.384 filas evaluables, modelo y canal condicionado al
**mismo presupuesto**:

| Presupuesto | Alertas | T+1 canal | T+1 modelo | T+1 ganancia | T+2 canal | T+2 modelo | T+2 ganancia |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 5 % | 319 | 27,9 % | 26,2 % | **−1,6 pp** | 13,1 % | 16,8 % | **+3,8 pp** |
| 10 % | 638 | 44,2 % | 44,4 % | **+0,2 pp** | 23,3 % | 28,2 % | **+4,8 pp** |
| 15 % | 958 | 56,6 % | 59,5 % | **+2,8 pp** | 31,3 % | 37,8 % | **+6,5 pp** |
| 20 % | 1 277 | 63,1 % | 72,0 % | **+8,9 pp** | 37,2 % | 44,6 % | **+7,4 pp** |
| 25 % | 1 596 | 67,3 % | 79,6 % | **+12,3 pp** | 42,4 % | 49,6 % | **+7,2 pp** |
| 30 % | 1 915 | 69,8 % | 85,3 % | **+15,5 pp** | 45,8 % | 54,8 % | **+9,0 pp** |

**La lectura incómoda y la razón de que este criterio exista:** la ventaja del
modelo depende casi por completo de cuántas alertas se esté dispuesto a emitir.
A presupuestos bajos —los que una secretaría puede atender de verdad— el canal
condicionado va igual o mejor a T+1. Si el umbral se fija después de mirar esta
tabla, lo que se elige no es un criterio: es un resultado.

### 0.1 El presupuesto se fija primero, y por criterio operativo

Todo lo demás cuelga de aquí, así que no se decide por desempeño.

**Presupuesto de referencia: 10 % de los municipios-mes evaluables**, que en
Tolima y Meta son unas **8 alertas al mes sobre 76 municipios**. Es la cifra
que se sostiene frente a quien tiene que responderlas: un equipo
departamental puede visitar, verificar y actuar sobre ocho municipios al mes de
forma sostenida; sobre diecinueve —el 25 %— no, y menos todos los meses del
año.

El veredicto se emite **a ese presupuesto**. La curva completa a 5 %, 10 % y
20 % se publica siempre como evidencia, porque un punto de operación no es una
comparación (tanda 8), pero el que decide es el declarado.

Cambiar el presupuesto de referencia exige una entrada nueva en esta bitácora,
con fecha, motivo y la declaración de si el cambio nació antes o después de ver
un resultado.

### 0.2 Las tres condiciones

Todas se evalúan **sobre las mismas filas** y al mismo presupuesto, por
horizonte y por separado (regla 4.7).

**A — Supera al canal condicionado.** El modelo anticipa más inicios que el
canal condicionado, y el intervalo emparejado de la diferencia **excluye el
cero**. No basta con ganar: hay que ganar fuera del ruido.

**B — Supera a la persistencia.** Solo donde la comparación es informativa. En
la cohorte primaria la persistencia no puede alertar por construcción, así que
B queda **NO_EVALUABLE** y se declara como tal; no cuenta como victoria ni
bloquea el veredicto. En la lectura secundaria de T+2, donde sí puede actuar,
B es obligatoria.

**C — No empeora la carga.** La carga de falsas alertas por 100 municipio-mes
no supera en más de **5** a la del canal condicionado, y el límite superior del
intervalo tampoco. Es una restricción de seguridad, no un objetivo: protege a
quien recibe las alertas, no al modelo.

### 0.3 El umbral de utilidad, y de dónde sale

Un modelo se adopta si **anticipa al menos 5 puntos porcentuales más de inicios
que el canal condicionado, al presupuesto de referencia**, con el límite
inferior del intervalo por encima de cero.

**Por qué 5 y no otro número.** La pregunta correcta no es cuánto alcanzamos a
sacar, sino cuánto hay que ganar para que valga la pena montar, mantener y
gobernar un modelo en vez de usar una regla que no cuesta nada. Cinco puntos
sobre 647 inicios en siete años son unos **32 brotes anticipados que de otro
modo no se habrían anticipado**, repartidos en dos departamentos: entre cuatro
y cinco por año. Por debajo de eso, el costo de operar un modelo —datos,
reentrenamiento, gobernanza, el riesgo de que se degrade sin que nadie lo
note— no se justifica frente a ajustar un umbral y condicionarlo al estado del
municipio, que es gratis y lo puede hacer cualquier secretaría mañana.

**Este umbral no está puesto para que lo pasemos.** Con las cifras de la tabla,
al 10 % de presupuesto **ninguna configuración que hemos medido lo pasa a T+1**
(+0,2 pp) y T+2 queda al borde (+4,8 pp). Se escribe así a propósito: un umbral
calibrado para que el resultado propio pase no mide nada.

### 0.4 Qué pasa si nada lo pasa

**«Ningún modelo supera al canal condicionado al presupuesto que la secretaría
puede atender» es un resultado del proyecto, no un fracaso.** Es, de hecho, el
hallazgo más accionable que podríamos entregar: significa que el camino corto
para mejorar la vigilancia del dengue en Tolima y Meta es **ajustar el umbral
del canal y condicionarlo a que el municipio no esté en exceso**, no desplegar
un modelo. Eso se puede hacer sin datos nuevos, sin tubería y sin gobernanza.

Si eso resulta, se escribe así, con esa claridad, y el trabajo de modelo se
reporta como lo que fue: la evidencia que permitió saberlo.

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

*Corregido el 5 de noviembre, ver la entrada siguiente:* los números del canal
quedaron en 265 alertas y 104 en falso al usar la cuenta de casos correcta, y
el candidato publicado dejó de ser XGBoost.

**5 de noviembre de 2026 — el candidato publicado se elige por criterio y pasa
a ser LightGBM.**

*Origen:* una pregunta de Stevan —por qué está publicado XGBoost si debería
verse el mejor— que resultó tener razón. Se declara el origen porque el cambio
se hizo después de ver los números.

*Primera versión de este diagnóstico, que estaba mal y se corrige acá.* Escribí
que la elección de XGBoost era arbitraria y sin razón escrita. No lo es: XGBoost
encabeza el ranking por **precisión promedio**, que es la métrica de ranking de
la política G5. La elección venía de ahí aunque nadie lo hubiera anotado. Lo que
sigue es el diagnóstico corregido.

*Qué estaba mal, en realidad.* Dos cosas. La primera es de alcance: la propia
política dice que el ranking **solo ordena a los candidatos elegibles**, y
ninguno lo fue —el audit deja las seis combinaciones en `does_not_meet` y el
champion en `not_selected`—. Rankear un conjunto vacío de elegibles es usar la
regla fuera de su alcance.

La segunda es de fondo y vale para el informe: **la métrica de ranking y el
criterio de utilidad eligen modelos distintos.** Por precisión promedio gana
XGBoost; por el criterio que el proyecto declaró desde la tanda 1 —anticipar
más inicios y que cada acierto cueste menos— gana LightGBM:

| T+1 | Inicios | Falsas/acierto | AUROC | AP |
| --- | --- | --- | --- | --- |
| LightGBM | **34/86** | **6,4** | 0,8192 | 0,6689 |
| XGBoost | 22/86 | 8,0 | 0,8189 | **0,6757** |
| GAM | 20/86 | 7,5 | 0,8093 | 0,6448 |

LightGBM domina a los otros dos: más inicios anticipados **y** menos falsas por
acierto. XGBoost gana solo en precisión promedio; en AUROC están empatados en
la tercera cifra.

Que una métrica de ordenamiento global y un criterio de decisión en un punto de
operación no coincidan no es una anomalía: la precisión promedio resume el
ordenamiento sobre todos los umbrales posibles, y la utilidad se mide en el
único umbral al que el sistema va a operar. Es la misma familia de observación
que motivó la propuesta de política v2, y conviene que el informe la discuta:
el proyecto rankea por una cosa y declara que le importa otra.

*Por qué importaba más de lo que parece:* publicar el peor de los tres inflaba
en pantalla la ventaja del canal endémico por un motivo ajeno a los modelos. La
comparación decía que el canal le ganaba al modelo en los dos ejes, y con el
candidato que el criterio elige la lectura cambia: **el modelo anticipa 34
inicios contra 27 del canal**, pero cada acierto le cuesta 6,4 falsas contra
3,9. Detecta más, pagando más. Esa sí es la tensión real que la secretaría
tendría que resolver, y la anterior era un artefacto de la publicación.

*Qué se cambió:* la elección pasó de bandera a criterio, en
`elegir_candidato()`. Sobre T+1, descartando la línea base, gana el candidato
que domina a los demás; si ninguno domina, el de mayor cobertura, y el empate
se rompe por costo. El script imprime la razón al publicar. Nombrar un
candidato a mano sigue siendo posible pero el script avisa que hay que
justificarlo por escrito.

*Qué no cambia:* el `NOT_APPROVED` de la compuerta G5 y el `NOT_SELECTED` del
champion se conservan con su autoridad. Cambiar qué candidato se muestra no es
aprobar ninguno: los tres siguen en `does_not_meet` y el publicado sigue
viajando con el rol `PROVISIONAL_CANDIDATE`.

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
9. **Separar no es aportar.** Añadida tras la tanda 6. Que una variable nueva
   separe la etiqueta no significa que agregue nada: la separación univariada
   mide si la información existe, no si el modelo ya podía alcanzarla. Antes de
   preinscribir un bloque por su separación, se entrena un modelo con las
   variables vigentes para predecir esa feature; si la predice bien, no agrega.
   Corolario: ninguna diferencia de uno o dos inicios se reporta sin cinco
   semillas detrás.

10. **Una línea base que no puede acertar no es una línea base.** Añadida tras
    la tanda 9. Antes de publicar una comparación hay que preguntarse cuántas
    de las alertas de la línea base caen sobre filas donde acertar es
    imposible por definición de la etiqueta. Si son muchas, la línea base no
    es débil por su método: está mal construida, y la ventaja que se publica
    es de la construcción y no del modelo. La prueba es barata —contar— y
    omitirla nos costó publicar un «+874 %» que no sobrevivió a la primera
    revisión externa. Su reverso: toda restricción que se le ponga a la línea
    base hay que ofrecérsela también al modelo, y reportar las dos lecturas.

11. **Nada de extrapolar en silencio.** Añadida tras la tanda 9. Una curva
    preguntada fuera del rango que se midió tiene que responder «no sé», no el
    valor del extremo. `np.interp` y sus equivalentes hacen lo segundo sin
    avisar, y eso ya produjo una tabla donde tres volúmenes de alerta
    distintos imprimían la misma cifra presentada como tres mediciones.

12. **Una corrida que no midió nada no puede terminar en verde.** Añadida tras
    la tanda 11. El retroanálisis descartó sus 163 orígenes uno por uno, escribió
    tres archivos de resultados vacíos y reportó éxito en 6,3 segundos. La regla
    tiene dos mitades. La primera: todo paso que puede quedarse sin datos declara
    cuántos esperaba y falla si no los tuvo. La segunda, menos obvia: el default
    de una herramienta de medición no puede ser un juguete. Un modo sintético que
    sirve para probar que el código corre no sirve para medir, y si comparten
    comando, alguien va a publicar el juguete.

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

### Tanda 6 — La amplitud de la banda del canal

**De dónde salió la hipótesis.** De mirar la gráfica del canal endémico de
Ibagué en el tablero. La banda entre el P25 y el P75 se comprime unos meses y
se expande otros, y la pregunta fue si esa compresión dice algo sobre el
movimiento siguiente. No salió de un razonamiento previo ni estaba en el plan,
y se registra así porque el origen de una hipótesis cambia cuánto pesa su
resultado.

**Qué dice el inventario.** Igual que en la tanda 5, antes de proponer nada se
revisó qué puede ver el modelo. En las 29 variables de la matriz preparada hay
niveles, cinco rezagos, una media de 3 meses y un cambio de 1 mes. **No hay
ninguna medida de dispersión.** Los bloques G, H e I de la tanda 5 tampoco
agregaron ninguna. Nadie le había dado nunca al modelo una medida de cuánta
variabilidad hay.

**Comprobación de fuga, hecha antes de preinscribir (regla 4.6).** La banda del
mes objetivo se arma con los cinco mismos meses calendario de años
estrictamente anteriores al objetivo, todos previos al mes de referencia. Es el
mismo argumento por el que `p75_t1` ya es columna legítima del panel, y se
verificó numéricamente en vez de darlo por bueno: el P75 del mes objetivo
buscado en `channel_history.csv` coincide con `p75_t*` del panel en **13 376 de
13 376 filas, en los dos horizontes**. `channel_history.csv` trae además el P25
y la mediana de cada mes, que el panel descarta: el proyecto siempre tuvo el
**ancho** de la banda del mes objetivo y nunca lo había extraído.

**Dos bloques preinscritos.** **M1**, la amplitud de la banda: ancho relativo
del mes en curso y del objetivo, su cociente —la compresión—, la holgura hasta
el umbral en anchos de banda y el salto que faltaría para cruzarlo. **M2**, la
volatilidad realizada del municipio: coeficiente de variación a 6 y 12 meses,
su cociente, su cambio a 3 meses y el rango relativo.

#### El sondeo: la señal existe y es nueva

Sobre filas de entrenamiento hasta 2024-06, 11 932 filas con 1 304 inicios, sin
tocar ningún bloque evaluado. AUC de Mann-Whitney sobre inicio contra no-inicio:

| | cruda | dentro del mes | dentro del municipio | dentro del decil de `margen_objetivo` |
|---|---|---|---|---|
| `compresion` | 0,329 | 0,326 | 0,332 | 0,341 |
| `holgura_curso` | 0,599 | 0,599 | 0,587 | 0,673 |
| `amplitud_objetivo` | 0,392 | 0,393 | 0,387 | 0,465 |
| `cv_6m` (M2) | 0,515 | 0,516 | 0,495 | 0,585 |
| `margen_objetivo`, de referencia | 0,534 | 0,536 | — | — |

La compresión separa, y separa más que la mejor variable de la tanda 5. No es
estacionalidad, porque dentro del mes calendario queda en 0,326. No es un
efecto fijo del municipio, porque dentro del municipio queda en 0,332. No es el
bloque G con otro nombre, porque dentro del decil de `margen_objetivo` queda en
0,341 y su correlación de Spearman con esa variable es −0,201. Por cuartiles,
la tasa de inicios va de **19,3 % a 11,2 % a 6,2 % a 3,7 %**, monótona.

M2 ya murió acá: dentro del municipio, `cv_6m` queda en 0,495 y el rango
relativo en 0,494. Lo que parecía señal dentro del decil de margen desaparece
al controlar por municipio, que es el control correcto.

#### Resultados completos, las seis configuraciones en las ocho celdas

Se reportan todas, incluidas las que no funcionaron y las que no se adoptan.
`Gc` es un control de especificación, no una hipótesis: es el bloque G con la
cuenta de casos del canal a los dos lados, y existe por el hallazgo colateral
que se describe más abajo. Alertas, falsas, inicios detectados sobre inicios
reales, y falsas por inicio.

**T+1, el horizonte que decide**

| | 2018-12 · 60 inicios | 2020-12 · 14 inicios | 2022-12 · 57 inicios | 2024-06 · 48 inicios |
| --- | --- | --- | --- | --- |
| Canal endémico | 17 · 1,59 | 1 · 8,00 | 14 · 1,93 | 21 · 2,86 |
| Persistencia | 0 · — | 0 · — | 0 · — | 0 · — |
| Vigente, 29 variables | 33 · 1,09 | 6 · 16,67 | 38 · 1,53 | 48 · 3,12 |
| G | 42 · 0,64 | 8 · 12,25 | 49 · 0,94 | 48 · 3,08 |
| **G+M1** | **44 · 0,57** | 9 · 10,78 | **50 · 0,92** | 48 · 3,10 |
| G+M2 | 43 · 0,60 | 8 · 12,25 | 47 · 1,02 | 48 · 3,10 |
| G+M1+M2 | 43 · 0,60 | 9 · 10,78 | 50 · 0,92 | 48 · 3,10 |
| Gc, control de cuenta | 44 · 0,57 | 9 · 10,78 | 48 · 1,00 | 48 · 3,10 |
| Cupo de alertas | 69 | 106 | 96 | 203 |

**T+2, informativo, línea cerrada desde la tanda 3**

| | 2018-12 · 48 inicios | 2020-12 · 13 inicios | 2022-12 · 41 inicios | 2024-06 · 37 inicios |
| --- | --- | --- | --- | --- |
| Canal endémico | 18 · 0,94 | 1 · 7,00 | 14 · 1,43 | 24 · 2,25 |
| Persistencia | 9 · 2,33 | 0 · — | 11 · 3,09 | 16 · 3,81 |
| Vigente, 29 variables | 10 · 2,30 | 4 · 22,75 | 18 · 1,44 | 23 · 4,13 |
| G | 20 · 0,65 | 8 · 10,62 | 20 · 0,85 | 28 · 3,14 |
| G+M1 | 19 · 0,89 | 7 · 12,29 | 21 · 0,62 | 30 · 2,73 |
| G+M2 | 21 · 0,62 | 9 · 9,33 | 19 · 0,84 | 30 · 2,80 |
| G+M1+M2 | 19 · 0,89 | 8 · 10,50 | 21 · 0,67 | 30 · 2,87 |
| Gc, control de cuenta | 20 · 0,65 | 9 · 9,33 | 20 · 0,80 | 29 · 2,97 |
| Cupo de alertas | 57 | 99 | 71 | 162 |

De 2020-12 no sale ninguna conclusión: 14 y 13 inicios, por debajo del mínimo
de 30 que fija la regla de tamaño de muestra. Se reporta como chequeo de
dirección y no vota, igual que en las tandas anteriores.

La persistencia detecta **cero inicios en los cuatro cortes de T+1**, como
corresponde: alerta donde el exceso ya está, y un inicio a un mes exige que no
esté. No es un desempeño malo, es una imposibilidad aritmética, y es la razón
por la que la barra de esta tanda se puso contra el canal y no contra ella.

#### Verificación contra las reglas de método, una por una

| Regla | Cómo se cumplió en esta tanda |
| --- | --- |
| **4.1** Bloque de 2025 consumido | No se tocó. El sondeo usó filas de entrenamiento hasta 2024-06; la tanda corrió sobre los cortes de validación. Ninguna medición contra el bloque congelado. |
| **4.2** El umbral no se elige sobre los datos con que se mide | El cupo de alertas se fija con la fracción del canal medida en la **partición interna del entrenamiento**, los últimos 12 meses, y se aplica tal cual a validación. Se reportan alertas y falsas realizadas. |
| **4.3** Consistencia entre cortes | Se reportan las ocho celdas y las seis configuraciones, no la mejor. El veredicto exige 2 de 3 cortes utilizables, que es la forma que toma la regla cuando 2020-12 queda fuera por 4.4. |
| **4.4** Tamaño de muestra declarado | Cada celda lleva su denominador. De 2020-12, con 14 y 13 inicios, no se concluye nada. Las diferencias entre configuraciones se midieron contra su propia dispersión, cinco semillas, y resultaron indistinguibles. |
| **4.5** La prevalencia cambia entre periodos | El cupo se recalcula por corte a partir del canal de ese corte, no se fija un valor absoluto. Por eso va de 69 alertas en 2018-12 a 203 en 2024-06. |
| **4.6** Fuga por la etiqueta | Verificado numéricamente antes de preinscribir: el P75 del mes objetivo coincide con `p75_t*` del panel en 13 376 de 13 376 filas. M2 solo usa ventanas que terminan en el mes de referencia. |
| **4.7** Las dos líneas base sobre las mismas filas | **Corregido después de la corrida.** `compresion.py` reportaba solo el canal. La persistencia se calculó aparte, sobre exactamente las mismas filas evaluables, y está en las tablas de arriba. |
| **4.8** Preinscripción antes de mirar | La hipótesis, la métrica, la barra y el criterio de fracaso se escribieron antes de entrenar. El sondeo univariado es anterior a la preinscripción y **se declara como tal**: midió si la información existía y si era nueva, no si el modelo mejoraba. |

Dos desviaciones que conviene dejar escritas y no esconder. La primera es la de
4.7, corregida arriba. La segunda es que esta verificación regla por regla
**no se había hecho en las tandas anteriores**, aunque el protocolo la pide;
esta es la primera que la trae. Las tandas 1 a 5 cumplen las reglas —se puede
comprobar en sus entradas— pero no dejaron la comprobación escrita.

#### Resultado: la señal no se convierte en nada

**M1 no aporta sobre el bloque G, y la línea se cierra.**

Con una sola semilla parecía haber ventaja: en 2018-12, G detecta 42 inicios a
0,64 falsas por inicio y G+M1 detecta 44 a 0,57. No sobrevive al cambio de
semilla. Sobre **15 celdas**, tres cortes por cinco semillas:

| G+M1 contra G | efecto |
| --- | --- |
| Inicios detectados | **+0,00 ± 1,67** (5 a favor, 4 en contra, 6 empates) |
| Falsas por inicio | **+0,008 ± 0,069** (6 a favor, 7 en contra) |

Cero exacto. La corrida que parecía buena era la semilla 7.

El veredicto preinscrito lo cierra igual por el otro lado. M1 pasa la barra del
canal en 2 de 3 cortes, pero el vigente **sin ninguna variable nueva** también
pasa 2 de 3, y G pasa exactamente los mismos dos. La condición de fracaso
estaba escrita antes de correr: *pasar solo en los cortes donde G ya pasaba*.

#### La lección, que vale más que el resultado

`compresion` separa de verdad y aun así no aporta. Las dos cosas son
compatibles y conviene entender por qué, porque es un error que se puede
repetir.

La separación univariada mide **si la información existe**. No mide **si el
modelo ya podía alcanzarla**. Un árbol con el bloque G puede reconstruir buena
parte de la compresión combinando `margen_objetivo`, `pos_banda` y la
estacionalidad que ya tiene. La tanda 5 funcionó porque el margen al umbral
abría una dimensión que no era alcanzable desde ninguna combinación de las 29
variables; la amplitud de la banda sí lo era.

**Regla nueva, barata, que sale de acá:** antes de preinscribir un bloque por
su separación univariada, comprobar si un modelo con las variables vigentes ya
predice esa feature. Si la predice bien, no agrega aunque separe.

Y se corrió esa prueba sobre el caso que la motivó, porque si no la explicación
de arriba sería una historia y no un hallazgo. Se entrenó un regresor con el
vigente más el bloque G para predecir cada variable de M1, y se midió el R²
fuera de muestra en los cuatro cortes:

| Variable de M1 | R² medio | AUC cruda |
| --- | --- | --- |
| `holgura_curso` | **0,958** | 0,599 |
| `compresion` | **0,783** | 0,329 |
| `salto_objetivo` | 0,771 | 0,474 |
| `amplitud_curso` | 0,541 | 0,547 |
| `amplitud_objetivo` | 0,272 | 0,392 |

La explicación queda confirmada y además afinada: **las variables que más
separan son precisamente las que el modelo ya podía reconstruir.** La
compresión, que era la apuesta, se predice con R² 0,78 desde variables que el
modelo ya tenía. La única que el vigente no reconstruye bien, `amplitud_objetivo`
con R² 0,27, es también la que menos separa una vez controlado el margen.

Esto es lo que la tanda 6 aporta de verdad, y es un resultado de método que el
informe final puede usar: una prueba de dos minutos que decide si vale la pena
montar un bloque de features.

#### Dos cosas que quedaron a la vista y no se adoptan

Se anotan porque callarlas sería elegir qué reportar.

`G+M1+M2` da 43,4 ± 0,8 inicios en 2018-12 y 50,6 ± 0,8 en 2022-12, contra 42,2
y 48,6 de G: la mejor de las seis variantes en los dos cortes que deciden. **No
se adopta.** Es una variante elegida después de ver el cuadro, entre seis, con
una diferencia de un sigma. Si interesa, se preinscribe y se corre con semillas
nuevas.

En 2024-06, **todas** las variantes detectan 48 de 48 inicios con desviación
0,0. El cupo del canal en ese corte es de 162 alertas sobre 304 filas: la
detección está saturada y la comparación se reduce al costo, donde el canal
gana 2,86 contra 3,09. Ese corte no discrimina entre modelos a ese presupuesto,
y eso explica por qué ninguna variante gana nunca ahí.

#### Hallazgo colateral: la cuenta de casos del canal

Encontrado al construir M, no buscado. El canal del proyecto se arma sobre
`dengue_notifications_count`: `channel_history.current_count` coincide con esa
columna en el **100 %** de las filas y con `total_notifications_count` solo en
el **89 %**, porque `total = dengue + grave`.

El bloque G calcula su margen con `total_notifications_count` contra un P75
construido sobre dengue solo, y la propia línea base del canal en el banco de
evaluación hace lo mismo. El canal contra el que se venía midiendo no era
exactamente el canal del proyecto.

*Tamaño del error.* Una variante de control con la cuenta del canal a los dos
lados da 43,6 ± 1,4 inicios contra 42,2 ± 1,3 en 2018-12 y 48,8 contra 48,6 en
2022-12: dentro del ruido. **Ninguna conclusión de las tandas 1 a 6 cambia.**

*En el tablero publicado.* La fila del canal pasa de 266 a 265 alertas en T+1,
con los mismos 27 inicios, y de 44 inicios con 291 alertas a 43 con 287 en T+2.
No cambia ninguna lectura, pero el número publicado debe ser el del canal real
y se corrige.

*Y una incoherencia visible, que es lo que de verdad obligaba a corregir.* El
tablero graficaba los casos **totales** contra bandas construidas solo con
dengue. En el periodo publicado eso dejaba un municipio-mes dibujado por encima
de su P75 cuya zona no era exceso: la gráfica y la etiqueta decían cosas
distintas sobre la misma fila. Se pasó toda la publicación a la cuenta del
canal —la cifra del mes, la serie, la zona y la fila de comparación— y esa
incoherencia queda en cero en los 22 archivos. Las cifras visibles cambian poco:
Ibagué en enero de 2025 pasa de 203 casos a 198.

---

### Tanda 7, línea N — Repartir el trabajo entre el canal y el modelo

**Hipótesis.** El canal confirma un brote en curso: alerta cuando los casos ya
cruzaron el umbral, de modo que sus alertas se concentran donde un inicio es
imposible o poco probable. El modelo anticipa. Repartirlos en vez de
enfrentarlos debería detectar más inicios al mismo cupo de alertas.

**Observación que la motivó, y que no cuenta como evidencia.** Sobre el bloque
congelado de 2025, de 86 inicios el canal atrapa 10 que el modelo pierde y el
modelo 17 que el canal pierde; juntos llegan a 44. Eso se calculó sobre
**evidencia consumida**, de predicciones ya publicadas. Sirve para formular la
hipótesis, no para elegir la regla. La elección se hizo en desarrollo.

**El cupo es la parte que había que hacer bien.** Una unión libre detecta más
porque alerta más, y eso no es una mejora. Todos los arms que compiten se miden
al mismo cupo que el canal emite según la partición interna. La unión libre se
reporta como techo, no como competidor.

#### Un error de diseño, encontrado por auditoría antes de concluir

La primera versión de esta tanda probó dos arms: gastar todo el cupo entre los
municipios que el canal alerta, y gastarlo todo entre los que no. Ninguno le
ganó al modelo, y la conclusión iba a ser que repartir no sirve.

**Eran los dos extremos del reparto, no el reparto.** En la parametrización por
la fracción *f* del cupo que se gasta en el lado del canal, esos arms son
*f* = 1 y *f* = 0. El interior —que es literalmente lo que la hipótesis
llamaba repartir— no se probó nunca. Una auditoría independiente del código lo
detectó y mostró que una interpolación entre los dos arms existentes superaba
al modelo en varias celdas.

Se rehizo con un arm `reparto` cuya fracción **se elige en la partición interna
del entrenamiento**, con un modelo entrenado sin ver esa partición, y se aplica
tal cual a validación. Es la regla 4.2 aplicada a un parámetro nuevo: no se
escoge sobre los datos con que se mide. Las fracciones elegidas fueron 0,2 y
0,3 en T+1.

La auditoría encontró además que el arm `modelo` se comparaba contra sí mismo
—siempre falso, y las filas leían como evidencia— y que las cinco semillas
estaban declaradas pero nunca se usaban. Las dos cosas quedaron corregidas.

#### Resultado: el reparto no agrega sobre el modelo

Inicios detectados y falsas por inicio, media y desviación sobre cinco semillas:

| T+1 | Canal | Modelo | Reparto |
| --- | --- | --- | --- |
| 2018-12, 60 inicios | 17 · 1,59 | 42,2 ± 1,3 · 0,64 | 41,6 ± 1,9 · 0,66 |
| 2022-12, 57 inicios | 14 · 1,93 | 48,6 ± 1,0 · 0,96 | 49,0 ± 0,9 · 0,94 |
| 2024-06, 48 inicios | 21 · 2,86 | 48,0 ± 0,0 · 3,09 | 48,0 ± 0,0 · **2,94** |

En una sola semilla el reparto daba 50 contra 49 en 2022-12 y parecía un
hallazgo. Con cinco semillas la diferencia desaparece: 49,0 ± 0,9 contra
48,6 ± 1,0. Es exactamente lo que la regla 4.9 obliga a comprobar, y es la
segunda vez en dos tandas que una diferencia de un inicio resulta ser ruido.

**La línea se cierra** por la condición preinscrita: ninguna regla de reparto
supera al modelo en 2 de 3 cortes.

**Lo que sí es real, y es chico.** En 2024-06 el reparto alcanza la misma
detección que el modelo —los 48 inicios, con desviación cero— a **2,94 falsas
por acierto contra 3,09**, y los rangos de las cinco semillas no se solapan. Un
5 % menos de falsas al mismo rendimiento. No alcanza la barra, que exige
detectar *más*, pero es reproducible y vale anotarlo.

**Por qué falló, que es lo informativo.** La contrahipótesis preinscrita
acertó: el modelo ya aprendió a no gastar alertas donde un inicio es imposible,
porque la etiqueta de inicio se lo enseña. Forzarlo a repartir con el canal no
le agrega información; en el mejor caso le ahorra unas pocas falsas.

Y explica por qué la observación de 2025 no se replicó: ahí el modelo publicado
**no tenía el bloque G**. La complementariedad que se veía era la debilidad del
modelo, no una virtud del canal. Una vez que el modelo ve el margen al umbral,
el canal no aporta nada que el modelo no tuviera ya.

**Dos puntos de operación que quedan anotados y no se adoptan.** La
intersección de las dos reglas detecta poco —16, 13 y 21 inicios— pero a 0,31,
0,30 y 1,06 falsas por acierto, muy por debajo de todo lo demás. Y `canal
primero` detecta lo mismo que el canal a la mitad del costo. Son candidatos
para una secretaría con muy poca capacidad de respuesta, no mejoras del
procedimiento, y elegir uno después de ver este cuadro sería selección a
posteriori.

---

### Tanda 7, línea O — Banco de evaluación de origen móvil

**Qué motivó la línea.** El banco vigente decide con tres cortes de seis meses
de validación, unos 165 inicios en total, y la heterogeneidad entre años es
grande: la tasa de exceso va de 9,0 % en 2021 a 62,9 % en 2019. Concluir desde
tres ventanas cortas es frágil, y un compañero del equipo planteó
independientemente la misma objeción sobre otro modelo del proyecto.

**Diseño.** Ventana expansiva. Para cada año objetivo se entrena con todas las
filas evaluables cuyo objetivo cae hasta diciembre del año anterior, y se
predicen los doce meses del año. Un reentrenamiento por año. El cupo de alertas
se mide con la tasa del canal en los doce meses previos al primer origen del
año, nunca sobre el año que se evalúa. **2025 no se toca**: es evidencia
consumida y su medición es de un solo tiro.

Esto lleva la evaluación de ~165 inicios en tres cortes a **647 inicios en
siete años**.

#### Resultado: el instrumento funciona y confirma el bloque G con mucha más evidencia

Acumulado 2018–2024, T+1, inicios detectados y falsas por inicio:

| | Inicios | Cobertura | Falsas/acierto |
| --- | --- | --- | --- |
| Canal endémico | 181 de 647 | 28 % | **2,92** |
| Persistencia | 0 de 647 | 0 % | — |
| Vigente, 29 variables | 388 de 647 | 60 % | 3,72 |
| **Vigente + bloque G** | **467 de 647** | **72 %** | **2,92** |

**El modelo con G anticipa 2,6 veces más inicios que el canal, al mismo costo
por acierto.** Con tres semillas: 465, 466 y 467 inicios, con costo 2,92 a
2,94. La diferencia no es ruido.

Y el bloque G aporta de verdad sobre el vigente —467 contra 388 inicios **y**
2,92 contra 3,72 de costo—, que es lo que la tanda 5 había medido sobre tres
cortes y ahora se sostiene sobre siete años.

Año por año en T+1, el modelo con G supera al canal **en inicios los siete
años**, y en los dos ejes a la vez en cuatro de siete:

| Año | Inicios reales | Canal | Vigente + G |
| --- | --- | --- | --- |
| 2018 | 91 | 20 · 3,20 | **43 · 1,79** |
| 2019 | 118 | 32 · 2,50 | **84 · 0,93** |
| 2020 | 69 | 18 · 5,44 | 68 · 6,96 |
| 2021 | 52 | 10 · 3,50 | 33 · 6,64 |
| 2022 | 89 | 24 · 3,08 | **31 · 1,03** |
| 2023 | 125 | 35 · 2,20 | **105 · 1,16** |
| 2024 | 103 | 42 · 2,40 | 103 · 3,53 |

**Dónde pierde, y conviene mirarlo.** En 2020 y 2021 detecta mucho más pero
paga más por acierto. Son los dos años de pandemia, con la vigilancia
distorsionada y el cupo del canal disparado —541 y 252 alertas—. En 2024
también paga más, aunque detecta 103 de 103.

**T+2, informativo.** El modelo con G detecta 345 de 647 contra 258 del canal,
pero a 3,25 falsas por acierto contra 2,51. Detecta más, pagando más. La línea
L sigue sin la evidencia que pedía.

#### Qué no demuestra esto

El banco es un arnés propio de experimentación, **no el pipeline del
proyecto**: reconstruye la ventana expansiva sobre la matriz preparada
publicada, con el bloque G calculado desde el panel. Que un tercero corra la
misma validación sobre el pipeline real es el control que falta, y es el que
convierte esto en un resultado del proyecto y no en un resultado nuestro.

Tampoco toca el bloque congelado de 2025. La medición contra ese bloque sigue
siendo de un solo tiro y sigue sin hacerse.

**Línea O: confirmada como instrumento.** El banco nuevo reproduce en signo las
conclusiones de las tandas 1 a 6 y las sostiene con ocho veces más inicios. No
las invierte, que era el riesgo declarado al preinscribirla.

---

### Tanda 8, línea P — El canal con umbral ajustado, y una métrica sesgada propia

**Origen.** Una crítica de un integrante del equipo al retroanálisis de la
tanda 7, al día siguiente de compartir el repositorio. Sostuvo que buena parte
de la ventaja del modelo venía del volumen de alertas, que la línea base
correcta era un canal con el umbral ajustado, y que la ventaja real estaba más
cerca del 10–17 % que del 2,6×.

**Lo primero que hay que decir: replicó la etiqueta de forma independiente** y
obtuvo 644 inicios contra nuestros 647, y 180 detectados por el canal contra
nuestros 181. Esa coincidencia es la mejor evidencia de que el arnés de
evaluación está bien construido, y vale más que cualquier discusión posterior.

#### Tenía razón en lo que importa

Ajustar el umbral del canal —alertar a una fracción del P75, elegida sobre el
año anterior— lo lleva de **181 a 365 inicios anticipados de 647** en T+1. Más
del doble, con la misma regla y sin modelo.

Es un hallazgo del proyecto y no una nota al margen: **buena parte de lo que le
falta al canal endémico no es el método, es que su umbral está puesto para
confirmar un brote en curso y no para anticipar uno nuevo.** Para una
secretaría de salud eso es accionable mañana, sin modelo, sin pipeline y sin
gobernanza.

El canal ajustado pasa a ser la tercera línea base publicada, junto al canal
estándar y la persistencia.

#### Y destapó, por otra vía, un defecto nuestro

La tanda 7 reportó «2,92 falsas por acierto» tanto para el canal como para el
modelo y lo presentó como empate al mismo costo. Esa cifra cuenta las falsas
contra **exceso**, no contra **inicio**: una alerta sobre un municipio que ya
está en exceso cuenta como acertada aunque no anticipe nada, y el canal alerta
justamente ahí.

**Es el tercer defecto que la propuesta de política v2 de este mismo
repositorio le señala a la compuerta G5, colado en nuestra propia
comparación.** Con las dos cuentas, T+1 acumulado:

| | Falsas por acierto, contra exceso | Contra inicio |
| --- | --- | --- |
| Canal endémico | 2,92 | **11,15** |
| Canal con umbral ajustado | 3,76 | **8,02** |
| Modelo sin el margen | 3,72 | **3,77** |
| Modelo con el margen | 2,92 | **2,97** |

La métrica sesgada favorecía al canal y aun así empataba. Corregida, la
distancia es de 2,97 contra 11,15. El tablero pasa a publicar la cuenta contra
inicio y conserva la otra en el contrato para poder compararse con la corrida
congelada.

#### Donde la crítica no se sostiene, y por qué los dos teníamos razón

Su conclusión era que la ventaja real ronda el 10–17 %. Las cifras discrepaban
porque cada uno medía en un **punto de operación distinto**, no porque alguno
midiera mal. La comparación honesta no es un punto sino la curva entera.

Inicios anticipados a igual volumen de alertas, T+1, 647 inicios reales:

| Alertas | Canal | Modelo sin G | Modelo con G | Ventaja sobre el canal |
| --- | --- | --- | --- | --- |
| 1 000 | 41 | 278 | **399** | +874 % |
| 1 852 | 121 | 445 | **547** | +352 % |
| 2 200 (canal de hoy) | 181 | 492 | **578** | +220 % |
| 3 294 (canal ajustado) | 390 | 587 | **622** | +60 % |
| 4 000 | 446 | 615 | **635** | +42 % |

**A igual volumen el modelo queda por encima del canal en todo el rango.** La
ventaja se encoge al subir el volumen —al final todo converge, porque alertar
sobre todo detecta todo— pero no desaparece: +42 % incluso a 4 000 alertas. Y
el modelo alcanza la detección del canal ajustado con cerca de un tercio de las
alertas.

También queda claro que el volumen no explicaba la ventaja original: el modelo
emitía **1 852 alertas contra 2 200 del canal**, menos y no más.

#### Lecciones de método

**Una métrica que uno mismo declaró defectuosa no deja de serlo porque la use
uno.** La política v2 le achaca a la compuerta G5 medir el acierto contra
exceso mientras mide la sensibilidad contra inicio. Escribimos eso y después lo
repetimos en nuestra propia comparación. Revisar los artefactos propios contra
las críticas que uno le hace a los ajenos debería ser parte del cierre de cada
tanda.

**Un punto de operación no es una comparación.** Dos personas midiendo el mismo
modelo a volúmenes distintos sacan conclusiones distintas y las dos tienen
razón en su punto. Lo que se publica ahora es la curva.

**La revisión externa encontró en un día lo que nosotros no vimos en siete
tandas.** Es el tercer caso en dos días en que una revisión independiente
—primero un auditor sobre el código, ahora un integrante sobre el método—
encuentra un defecto real. Lo que no lo encontró nunca fue releer el propio
trabajo.

> **Corregido en la tanda 9.** La curva de esta tanda compara contra un canal
> que gasta buena parte de sus alertas en municipios ya en exceso, donde
> acertar un inicio es imposible por definición. Las ventajas de la tabla de
> arriba —en particular el «+874 %» a 1 000 alertas— son de esa construcción y
> no del modelo. La comparación vigente es contra el **canal condicionado** de
> la tanda 9, y en el punto de operación publicado la ventaja real es de
> +22 %. Esta sección se conserva sin reescribir porque el error también es
> parte del registro.

### Tanda 9, línea Q — El canal condicionado, y una línea base que no podía acertar

**Origen.** Segunda crítica del mismo integrante, ahora sobre la curva que la
tanda 8 publicó. Su argumento: en esa curva el canal gasta buena parte de sus
alertas en municipios que **ya están en exceso**, y con la métrica corregida
—falsas contra inicio— esas alertas le cuentan todas como falsas, mientras que
el modelo aprendió a no alertar ahí. La línea base correcta sería un canal que
además solo alerte donde el municipio **no** está en exceso: misma regla, sin
modelo, y con la misma información que el modelo tiene en X. Reportó que así,
a 1 000 alertas, el canal anticipa 369 inicios y el modelo 403.

**Tenía razón, y el número era aún más grande de lo que él calculó.**

#### Qué mide el canal condicionado

Alertar solo donde el municipio no está en exceso y los casos pasan una
fracción del P75, elegida por F1 sobre los doce meses anteriores. T+1,
acumulado 2018-2024, 647 inicios:

| Regla | Inicios | Alertas | Falsas por acierto |
| --- | --- | --- | --- |
| Canal endémico | 181 | 2 200 | 11,15 |
| Canal con umbral ajustado | 365 | 3 294 | 8,02 |
| **Canal condicionado** | **328** | **838** | **1,55** |
| Modelo sin el margen | 388 | 1 852 | 3,77 |
| Modelo con el margen | 467 | 1 852 | 2,97 |

**El canal condicionado acierta más barato que el modelo publicado**: 1,55
falsas por acierto contra 2,97, con menos de la mitad de las alertas. Que una
regla sin modelo haga eso es el resultado más incómodo —y más útil— que ha
producido el proyecto.

A igual volumen, con el modelo bajo la **misma** condición:

| Alertas | Canal condicionado | Modelo | Ventaja |
| --- | --- | --- | --- |
| 250 | 148 | 141 | −5 % |
| 500 | 239 | 234 | −2 % |
| 1 000 | 373 | 399 | +7 % |
| 1 500 | 430 | 502 | +17 % |
| 1 852 (el punto publicado) | 448 | 546 | +22 % |

Nuestra réplica de su cifra: 373 contra 399, donde él reportó 369 contra 403.
Es la segunda vez que dos implementaciones independientes coinciden al dígito.

**El «+874 % a 1 000 alertas» de la tanda 8 no sobrevive.** No porque el modelo
sea peor, sino porque la línea base contra la que se midió estaba gastando su
presupuesto en filas donde anticipar un inicio es imposible por definición. De
ahí sale la regla 4.10.

#### Lo que sí queda a favor del modelo

**El canal condicionado tiene techo y el modelo no.** La condición solo deja
pasar 2 411 filas de alerta posibles en T+1, y con todas ellas anticipa como
mucho 461 de 647 inicios. El modelo llega a 646. La ventaja del modelo es de
escala: aparece cuando una secretaría puede atender más alertas, y a volúmenes
bajos —unos cientos de alertas al mes— hoy no hay caso para el modelo en T+1.

**Y darle la misma condición al modelo no lo cambia:** 467 contra 467 en T+1,
con el costo bajando de 2,97 a 2,90. El modelo ya sabía dónde no alertar; la
condición es información que ya tenía en `zona_canal_t`.

#### Donde la crítica no se sostiene: T+2 es fuga

El inicio exige exceso en el objetivo viniendo de un mes sin exceso. A T+1 ese
mes anterior es el mes de origen y se conoce al emitir. **A T+2 es un mes que
todavía no ha ocurrido.** Medido con las dos compuertas, T+2:

| Compuerta | Inicios | Alertas | Falsas por acierto |
| --- | --- | --- | --- |
| Exceso del mes de origen (observable) | 209 | 1 190 | 4,69 |
| Mes anterior al objetivo (no observable) | 329 | 942 | 1,86 |

**120 inicios de diferencia: ese es el tamaño de la fuga.** Con la compuerta
observable el modelo queda por encima en todo el rango de T+2 (+17 % a +27 %
en la lectura simétrica), y darle esa compuerta al modelo lo **empeora**, de
350 a 309, que es exactamente lo que se espera si la restricción es la
equivocada a ese horizonte.

#### Lo que encontró el auditor en nuestra primera versión

La v1 de esta tanda se auditó antes de concluir, y la auditoría encontró seis
defectos reales. Se registran porque el punto de la bitácora es que el error
quede, no que quede bonito:

1. **La curva extrapolaba en silencio.** `np.interp` devuelve el valor del
   extremo fuera del rango medido, y como el barrido de fracciones terminaba
   en 3,00 el canal no podía bajar de ~1 040 alertas: las filas de 500 y 838
   reimprimían el mismo punto con tres etiquetas distintas. Regla 4.11.
2. **Un volumen de la tabla salió de la propia corrida**, en un archivo que se
   declaraba preinscrito antes de mirar resultados. Regla 4.8.
3. **El assert que decía verificar la aritmética de índices no podía fallar**:
   comparaba dos expresiones que a T+1 son la misma por construcción. Es el
   segundo test vacuo del proyecto. Se reemplazó por la comprobación contra la
   definición primitiva —exceso del mes `m` ⟺ casos\[m\] > P75 del mes `m`—,
   que sí falla si el desplazamiento está mal: 12 388 de 12 388 filas.
4. **La columna de ventaja comparaba el modelo sin compuerta contra el canal
   con compuerta.** A T+2 eso casi duplicaba la ventaja. Ahora se publican las
   dos lecturas y la simétrica va primero.
5. **El «volumen máximo alcanzable» era el máximo del barrido**, no el de la
   regla, y truncaba la tabla justo donde la línea base se satura, que es el
   argumento más fuerte a favor del modelo.
6. **Faltaban** la persistencia (regla 4.7), la tasa de falsas alarmas (la
   métrica nueva se agrega, no reemplaza), las cinco semillas del corolario de
   la regla 4.9 y el desglose por año (reglas 4.3 y 4.4).

#### Un hallazgo sobre los datos, encontrado al corregir

**153 de las 912 filas de un año tienen P75 = 0**: municipios donde el
percentil histórico es cero y cualquier caso es exceso. En esas filas
`casos > f · P75` es `casos > 0` para **cualquier** f, de modo que la fracción
no las mueve, y con una rejilla suficientemente amplia la regla deja de ser
«una fracción del P75» y se vuelve «solo los municipios con P75 = 0». En 2020 a
T+2 eso hizo que la elección por F1 se fuera a f = 59,00 con F1 = 0,2151 contra
0,2149 de f = 0,10: dos diezmilésimas decidiendo entre dos reglas
completamente distintas. Por eso la rejilla de **selección** llega hasta 3,00 y
la de **dibujo** se extiende: en la segunda no se elige nada, se describe.

#### Lecciones de método

**Una línea base mal construida exagera al modelo más que cualquier error de
medición.** Las tandas 7 y 8 corrigieron la métrica y seguían comparando contra
una regla que no podía acertar. La corrección de la métrica hizo ver mejor al
modelo; la corrección de la línea base lo pone en su sitio.

**Tres revisiones externas, tres defectos reales.** Un auditor sobre el código
en la tanda 7, un integrante sobre la métrica en la 8 y el mismo integrante
sobre la línea base en la 9. Releer el propio trabajo no encontró ninguno de
los tres. La conclusión práctica: la auditoría va **antes** de concluir, no
después de publicar.

---

### Tanda 10, línea R — Retroanálisis con datos reales y regresión logística

Documentada en detalle en [tanda-10-retroanalisis.md](bitacora/tanda-10-retroanalisis.md).

**Origen.** Llevar la línea G a datos reales y a la evaluación del contrato. El
modelo de la tanda es una regresión logística (`logistic_onset`) construida
sobre el bloque de margen de G: usa el margen contra el umbral del mes objetivo
y el del mes en curso, el cambio del umbral, la tendencia de casos y si hubo
casos.

**Resultado.** Con el release `satd-raw-173d5856` (2007-2024), en siete cohortes
de 2018 a 2024 (593 inicios en T+1 y 431 en T+2), frente al canal condicionado
de la línea Q y con el mismo presupuesto de alertas:

| Combinación | T+1: Δ sensibilidad (IC 95 %) | T+2: Δ sensibilidad (IC 95 %) |
| --- | --- | --- |
| Logística con clima | +3.4 pp (0.5 a 6.2) | +8.1 pp (4.2 a 11.8) |
| Logística sin clima | +2.7 pp (−0.2 a 5.9) | +7.7 pp (3.7 a 11.8) |
| XGBoost con clima | −0.5 pp (−3.6 a 2.6) | +1.9 pp (−3.2 a 6.6) |

La logística le gana a XGBoost en los dos horizontes, pero ninguna combinación
llega a la meta de 10 puntos del contrato. En T+1 la ganancia viene de picos de
un mes; en brotes sostenidos el canal sigue igual o mejor. Encadenar el puntaje
T+1 con el T+2 no ayuda. Son cifras exploratorias, calculadas con una
evaluación local fuera del registro; la cifra oficial saldrá de EXP003 con la
evaluación científica del contrato.

### Tanda 11, línea S — El retroanálisis sobre la base común, y G que no reproduce

**Origen.** Antes de que el equipo empiece a correr experimentos comparables,
el retroanálisis del pipeline tenía que reproducir el banco de la línea O sobre
el panel que produce el contrato. No lo hacía, y las tres razones por las que no
lo hacía son más instructivas que el resultado.

#### Defecto 1: la corrida reportaba éxito sin medir nada

`kedro run --pipelines retroanalisis` terminaba con
«Pipeline execution completed successfully in 6.3 sec» y escribía
`resumen.csv`, `por_anio.csv` y `curva.csv` **vacíos**. Los 163 orígenes
—82 en T+1 y 81 en T+2— quedaban registrados uno por uno en `omitidos.csv`
con el motivo «Fold sin soporte de entrenamiento o predicción», y el nodo
seguía adelante.

La causa: `conf/base/parameters.yml` declara `canonical.mode: synthetic`, así
que el pipeline reconstruía el panel **artificial** —dos municipios ficticios y
84 meses desde 2018-01— en vez del panel real. Con ese panel ningún fold tiene
soporte, porque los percentiles del canal se comen los cinco años anteriores.

Lo grave no es el modo por defecto, que es razonable para una prueba de humo:
es que una medición que no midió nada terminara en verde y dejara tres archivos
que alguien podía leer como resultado. Ahora el nodo verifica el panel antes de
empezar —la receta declara `cobertura_desde` y `municipios_minimos`, y el
mensaje de error nombra `canonical.mode`— y aborta si un horizonte se queda sin
folds, dejando el `omitidos.csv` para el diagnóstico.

#### Defecto 2: el piso de entrenamiento estaba quemado en 2018-01

`ExperimentSpec.train_target_start` tenía `"2018-01"` como valor y como piso
duro. Venía del release histórico, que empezaba en 2011-06. Con el release
operacional, que cubre desde 2007-01, ese piso **dejaba fuera seis años de
entrenamiento disponibles** y hacía imposible reproducir el banco, que entrena
desde 2011-05. También explica el reporte de 541 inicios desde 2019 que trajo un
integrante: su primer fold entrenaba con un año de historia.

El piso nuevo es `TRAIN_FLOOR = "2012-01"`, y no es arbitrario: el P75 del canal
se construye con el mismo mes calendario de los cinco años anteriores, así que
2012 es el primer año completamente evaluable con datos desde 2007. Además dejó
de estar quemado: es el parámetro `retroanalisis.primer_entrenamiento`.

#### Defecto 3: la línea G no se podía correr por esta ruta

El bloque de margen estaba cableado solo en la fábrica (`factory/engine.py` y el
adaptador XGBoost). El retroanálisis no pasa por ahí: arma su matriz con
`prepare_horizon` y la entrega al arnés, que exigía que X fuera exactamente el
contrato canónico. Y el adaptador logístico —el que usa la receta del
retroanálisis— rechazaba `variables_g` de plano.

Es decir: **la única mejora confirmada del proyecto no se podía ejecutar por la
ruta que el equipo iba a usar para comparar.** Quedó cableada en los tres
puntos: el arnés acepta derivadas declaradas, el adaptador logístico las
proyecta crudas —son márgenes con signo, log1p no está definido en los
negativos— y el bloque se adjunta en el retroanálisis igual que en la fábrica.

De paso apareció un cuarto: la rama de G en el adaptador XGBoost usaba
`MARGIN_COLUMNS` sin importarlo. Ninguna receta versionada enciende
`variables_g`, así que la rama no se ejecutaba nunca y la primera corrida con G
habría fallado con `NameError`. Lo encontró el linter, no las pruebas; ahora hay
una prueba que construye el adaptador con el bloque declarado.

Y un quinto, que solo apareció en la **primera corrida real** con G: los 82
orígenes de T+1 se omitieron con «Esquema de características inválido». El
envoltorio `CheckedAdapter` valida la matriz por su cuenta, aparte del
adaptador, y no recibía las derivadas: el bloque estaba bien construido, bien
declarado y bien proyectado, y lo rechazaba la frontera. Ninguna de las pruebas
nuevas lo vio porque todas paraban antes del arnés. La que faltaba —y que ahora
existe— entra por `run_candidate` con el adaptador real de la receta G y
reproduce exactamente ese error cuando se desactiva el arreglo.

La lección, otra vez de método: **una prueba que se detiene antes de la frontera
no prueba la frontera.** Cuatro pruebas del bloque pasaban en verde mientras la
corrida real fallaba en todos sus folds.

#### El banco queda reproducido

Contando inicios sobre el panel real (release `satd-raw-173d5856`, Tolima y
Meta, 76 municipios, 2007-01 a 2024-12) con la definición de la línea O:

| Año objetivo | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | Total |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Banco (línea O) | 91 | 118 | 69 | 52 | 89 | 125 | 103 | **647** |
| Panel del contrato | 91 | 118 | 69 | 52 | 89 | 125 | 103 | **647** |

Año por año, idéntico. El retroanálisis evalúa 641 de esos 647, y los 6 que
faltan están contados: son el objetivo 2018-01, que necesitaría un origen
anterior al primero evaluado (2 inicios), y el objetivo 2024-12, cuya etiqueta
solo estaría disponible en 2025-01, dentro del periodo reservado (4 inicios).
No es una discrepancia: es el calendario del protocolo.

#### Una decisión de diseño: el conjunto de filas es común, con G o sin G

El bloque de margen no se puede completar en todas las filas. La velocidad y la
aceleración necesitan el mes anterior, y `p75_canal_t` no existe antes de 2012.
En el release operacional eso son **152 filas** —los meses 2012-01 y 2012-02 de
los 76 municipios—, todas de entrenamiento y ninguna evaluada.

Descartarlas solo cuando G está encendida habría hecho que la corrida con G y la
corrida sin G entrenaran sobre conjuntos distintos, y entonces la diferencia
entre las dos ya no sería atribuible al bloque. Por eso el filtro **se aplica
siempre**, también sin G: el retroanálisis fija un conjunto evaluable común y lo
único que cambia entre recetas son las columnas que cada una declara. El conteo
queda auditado en `conjunto.csv`.

Es la regla 7 —«las líneas base van sobre las mismas filas»— aplicada a la
comparación entre recetas, que es donde no la teníamos escrita.

#### Un error silencioso en el propio bloque

Las velocidades se calculaban con `shift(1)` sobre la historia ordenada, es
decir contra la **fila** anterior. Con un hueco de calendario eso resta contra
un mes que no es el anterior, sin avisar. El panel canónico es una rejilla
completa y por eso nunca se notó, pero la definición decía una cosa y el código
hacía otra. Ahora el mes anterior se busca por su nombre y un hueco produce una
ausencia, que es la respuesta correcta.

#### La medición comparativa: sin clima contra G, sobre todo lo mismo

Dos recetas en la misma corrida, mismo panel, mismos folds y **las mismas filas**
—7 612 en T+1 y 7 572 en T+2, idénticas para las dos, verificado en
`conjunto.csv`—, cero orígenes omitidos. T+1, 641 inicios evaluados:

| Línea base | Alertas | Canal | Sin clima | Con bloque G |
| --- | --- | --- | --- | --- |
| Canal P75 | 315 | 177 | 176 (−1; −17 a 17) | 176 (−1; −17 a 16) |
| Canal ajustado | 1 128 | 360 | 391 (+31; 0 a 66) | **396 (+36; 7 a 70)** |
| Canal condicionado | 817 | 323 | 347 (+24; 1 a 50) | **349 (+26; 2 a 53)** |

T+2, 459 inicios evaluados:

| Línea base | Alertas | Canal | Sin clima | Con bloque G |
| --- | --- | --- | --- | --- |
| Canal P75 | 378 | 99 | 117 (+18; −0 a 37) | **120 (+21; 3 a 40)** |
| Canal ajustado | 1 147 | 206 | 246 (+40; 14 a 68) | 247 (+41; 17 a 68) |
| Canal condicionado | 1 158 | 207 | 248 (+41; 14 a 70) | 250 (+43; 17 a 70) |

El modelo le gana a las dos líneas base fuertes en los dos horizontes, con los
intervalos excluyendo el cero. Contra el canal P75 al mismo presupuesto no
aporta en T+1 y sí en T+2.

**Y el bloque G no cambia nada.** La diferencia entre las dos recetas es de 0,
+5 y +2 inicios en T+1 y de +3, +1 y +2 en T+2, sobre 641 y 459. La regla 9
dice expresamente que ninguna diferencia de uno o dos inicios se reporta sin
cinco semillas detrás, y estas están en ese orden de magnitud. **No es una
mejora.**

#### Por qué G no aporta aquí, cuando en la tanda 5 fue la única mejora confirmada

No es que el bloque esté mal construido ni mal cableado: es que **este modelo ya
lo tenía**. La receta aplica `log1p` a los conteos y a los umbrales, y después
estandariza. Una logística sobre esas columnas puede formar el margen como una
resta de logaritmos con coeficientes de signo opuesto, que es exactamente lo que
hace: sus dos coeficientes más grandes son `p75_h5_t1` en −2,83 y
`total_notifications_count` en +1,29.

La medición que lo cierra: la correlación de rangos entre `margen_objetivo` y
`log1p(casos) − log1p(p75_objetivo)` —una resta que el modelo puede construir
con lo que ya tiene— es de **0,999**. Como la comparación ordena dentro de cada
mes de origen, un orden idéntico es información idéntica. El bloque recibe peso
(1,48 de 12,53 en suma de coeficientes absolutos, casi todo en `pos_banda`),
pero no mueve las detecciones.

En la tanda 5 el bloque se midió sobre **XGBoost**, y ahí sí aportaba. La
diferencia no es el dato: es la familia. Un árbol tiene que aproximar un
cociente con cortes sucesivos en dos variables, y eso es caro; un modelo
log-lineal lo obtiene con dos coeficientes. **G no es una mejora del proyecto:
es una mejora de los árboles.**

Esto es la regla 9 —«separar no es aportar»— un paso más allá. Su procedimiento
pregunta si las variables vigentes **predicen** la feature nueva. Aquí la
pregunta que hacía falta es más barata y más directa: si el modelo puede
**construirla** con lo que ya tiene y la métrica solo mira el orden, no agrega,
y da igual cuánto separe. La respuesta depende de la familia del modelo, así que
una línea confirmada sobre una familia no está confirmada sobre otra.

#### Lo que queda preinscrito para la tanda siguiente

Correr esta misma comparación con **XGBoost**, que es donde G ganó su
confirmación, sobre esta base común y estas mismas filas. Es la receta `EXP001`
con `variables_g: true` y las seis columnas al final de la matriz. Decide lo
mismo que decidió la tanda 5: inicios detectados al mismo presupuesto. Si G no
aporta tampoco ahí, la línea G pasa de «confirmada» a «confirmada solo en los
tres cortes de la tanda 5, no reproducida sobre el banco», que es un resultado
publicable y bastante más honesto que el que veníamos cargando.

#### Una discrepancia pendiente con la tanda 10

La entrada de la tanda 10 describe su logística como «construida sobre el bloque
de margen de G». La receta versionada que el pipeline ejecuta,
`conf/retroanalisis/logistica_sin_clima.yml`, declara `variables_g: false` y sus
predictores son los canónicos: los umbrales crudos, no los márgenes. Las dos
descripciones no pueden ser del mismo artefacto. Como la tanda 10 dice
explícitamente que sus cifras salieron de «una evaluación local fuera del
registro», lo más probable es que ese script sí construyera los márgenes y la
receta del repositorio sea otra cosa. Queda anotado para resolverlo con quien
corrió la tanda, antes de comparar sus cifras con las de aquí.

#### Lección de método

Tres de los cuatro defectos tienen la misma forma: **el código hacía algo
razonable y silencioso en vez de fallar.** El pipeline medía sobre el fixture,
el piso se quedaba en 2018, la velocidad restaba contra la fila anterior. Nada
de eso produce un error; produce un número. Y un número que nadie puede
distinguir de uno bueno es peor que una excepción, porque viaja.

### Tanda 13, línea U — El bloque G sustituía las columnas de umbral

Documentada en detalle en [tanda-13-linea-U.md](bitacora/tanda-13-linea-U.md).

**Origen.** La tanda 12 dejó 127 inicios de distancia sin explicar entre el
banco de la línea O y el retroanálisis, con tres diferencias juntas: insumos,
cadencia de reentrenamiento y reparto de alertas. Esta tanda las separa.

**Corrida 1, la cadencia: no explica nada.** Con reentrenamiento anual en vez de
mensual el brazo sin bloque pasa de 515 a 520 inicios en T+1 a 1 866 alertas. El
criterio preinscrito pedía 452 o menos, y subir era la condición de fracaso
declarada. Siete reentrenamientos al año producen prácticamente el mismo modelo
que ochenta y dos.

**Corrida 2, los insumos: explican el gap y además explican G.** El
`features.csv` del replay que el banco consume no trae **ninguna** de las siete
columnas de umbral del canon: ve `zona_canal_t`, que es la decisión ya tomada,
pero nunca el número. Quitárselas al modelo del pipeline lo lleva de 515 a
**411** inicios, y volver a ponerle el bloque G lo sube a **527**. Con los
umbrales presentes, el bloque suma +4.

| T+1, 641 inicios, 1 866 alertas | Inicios |
| --- | --- |
| Con umbrales, sin bloque | 515 |
| Con umbrales, con bloque | 519 |
| Sin umbrales, sin bloque | **411** |
| Sin umbrales, con bloque | **527** |

**El bloque G no es una mejora: es el sustituto de una columna faltante.**
Recupera casi exactamente lo que quitar los umbrales destruye —283 → 388 al
presupuesto del canal ajustado, contra los 385 del modelo que sí los tiene—, no
agrega información nueva. Las tandas 5 y 7 midieron bien sobre un modelo ciego
al umbral; lo que no era válido era extrapolar ese aporte a un modelo que los
ve, y el contrato canónico los tiene.

Las dos predicciones de la corrida 2 quedaron declaradas antes de medir, y el
razonamiento sobre el reparto de alertas quedó corregido en el mismo archivo
tras leer `top_cupo`: el banco concentra más que el pipeline, no menos, así que
el reparto predecía el signo contrario y no podía explicar nada.

## 6. Estado de las líneas de trabajo

| Línea | Estado |
| --- | --- |
| Objetivo de entrenamiento sobre el inicio | Confirmada en ordenamiento; insuficiente por sí sola |
| A. Umbral por tasa en vez de valor | **Cerrada**: rechazada en la tanda 2 |
| F. Presupuesto de alertas | **Resuelta**: confirmada en T+1, rechazada en T+2 |
| B. Entrenar sin las variables del canal | **Cerrada**: rechazada en la tanda 4; esas variables son necesarias |
| C. Modelo en dos etapas | **Cerrada**: rechazada en la tanda 3; el modelo ya estratifica solo |
| D. Costo asimétrico en el entrenamiento | **Cerrada**: rechazada en la tanda 4 |
| G. Margen continuo al umbral del canal | **Cerrada con explicación en la tanda 13**: no es una mejora, es el sustituto de las siete columnas de umbral que el modelo del banco no tenía. Sobre el contrato canónico, que sí las tiene, suma +4 inicios de 641. Las tandas 5 y 7 midieron bien sobre un modelo ciego al umbral; extrapolarlo a uno que lo ve no era válido |
| H. Presión epidémica regional | **Cerrada**: rechazada en la tanda 5 con esta forma de medirla |
| I. Memoria y agotamiento de susceptibles | **Cerrada**: rechazada en la tanda 5 |
| J. Regresión sobre el margen | **Cerrada**: no aporta sobre la clasificación |
| E. Variables demográficas y sociales | Abierta, en curso por otro integrante |
| K. Versión mínima de G (una sola variable) | Preinscrita para la tanda 6 |
| L. Reapertura de T+2 con el margen | Preinscrita para la tanda 6 |
| M1. Amplitud de la banda del canal | **Cerrada**: rechazada en la tanda 6; separa pero no aporta sobre G |
| M2. Volatilidad realizada del municipio | **Cerrada**: rechazada en la tanda 6; no separa dentro del municipio |
| N. Repartir el trabajo con el canal | **Cerrada**: rechazada en la tanda 7; el modelo con G ya no necesita al canal |
| O. Banco de evaluación de origen móvil | **Confirmada** en la tanda 7; sostiene G sobre 647 inicios en siete años |
| P. Canal con umbral ajustado como línea base | **Confirmada** en la tanda 8; lleva al canal de 181 a 365 inicios y pasa a ser línea base publicada |
| Q. Canal condicionado a no estar en exceso | **Confirmada** en la tanda 9 a T+1 y **rechazada a T+2 por fuga**; pasa a ser la línea base principal y reduce la ventaja publicada del modelo a +22 % en el punto de operación |
| R. Retroanálisis con datos reales y logística | Confirmada en la tanda 10 como exploratoria; su receta versionada no enciende G (ver tanda 11) |
| S. Base común del retroanálisis | **Confirmada** en la tanda 11: el banco queda reproducido (647 inicios, año por año) y las recetas corren sobre el mismo panel, los mismos folds y las mismas filas |
| T. Reproducir G sobre la base común | **Resuelta en la tanda 12 y con resultado negativo**: ni G ni el banco reproducen. La logística sin bloque le gana a XGBoost con bloque en todos los presupuestos |
| U. Diferencia de instrumento con el banco | **Cerrada en la tanda 13**: la cadencia no explica nada; las siete columnas de umbral ausentes explican el nivel (515 → 411) y el aporte de G (+116 al quitarlas, +4 al tenerlas) |
| V. Ensamble de rangos logística + XGBoost del banco | **Cerrada** en la tanda 14: el ensamble no supera a la logística; XGBoost pierde con las cinco semillas y la 53 era la más favorable |
| W. Clima sobre la base común | **Sin efecto** en la tanda 15 (+12 en T+1, IC −4 a 28), pero a favor en seis de siete años; sigue en la tanda 22 |
| X. Regularización y escala log1p de la logística | **Cerrada** en la tanda 16: C ≥ 1 no cambia nada; sin log1p pierde 43 inicios en T+1 y G recupera la mayor parte, lo que confirma el mecanismo de la tanda 11 |
| Y. Versiones reducidas de la logística | **Aceptada** en la tanda 17: la mínima de cinco variables no pierde más de 5 puntos en ningún horizonte (−8 y −3 inicios) |
| Z. Entrenar con todo el país, evaluar en Tolima y Meta | Preinscrita para la tanda 18 |
| AA. Lectura por nivel de transmisión del año | **Leída** en la tanda 19: la ventaja de la logística en T+1 es igual en años altos y bajos; la de la mínima y la de XGBoost está en los años altos; en T+2 la ventaja es mayor en años bajos |
| AB. Ajustes de XGBoost sobre la base común | **Cerrada** en la tanda 20: ninguna variante supera a la logística; profundidad 6 empeora (−25 en T+1); profundidad 2 queda cerca (+4) y pasa a cinco semillas |
| AC. Ventana de entrenamiento móvil | **Cerrada** en la tanda 21: ninguna ventana supera a la expansiva; la de 3 años empeora |
| AD. Qué parte del clima aporta | **Cerrada** en la tanda 22: ninguna forma del clima cambia más de 4 inicios; sobre la mínima el clima suma +15 en T+1, seis años a favor |
| AE. Ensambles entre logísticas | **Cerrada** en la tanda 23: el ensamble queda entre sus componentes, sin superar a la logística con clima |
| AF. El mes como ciclo en la logística | **Cerrada** en la tanda 24: sin efecto, con y sin clima |
| AG. Lectura por departamento | **Leída** en la tanda 25: en T+1 la ventaja de la logística es de Tolima (+22) y empata en Meta (+2); con clima gana en Meta (+16) |
| AH. Un modelo por departamento, con y sin clima | **Cerrada** en la tanda 26: empeora; con clima pierde 18 inicios en T+2 (IC −31 a −5) y Meta pierde la ganancia del clima |
| AI. Un solo modelo con indicador de departamento | Preinscrita para la tanda 27 |
| AJ. Excluir 2020 del entrenamiento | Preinscrita para la tanda 28 |
| AM. XGBoost de profundidad 2 con cinco semillas | Preinscrita para la tanda 31 |
| AN. El clima con otro remuestreo | **Cerrada** en la tanda 32: con bloques de mes el clima en T+1 excluye el cero (+15, IC 1 a 30 sobre la mínima), unos 2 puntos, lejos de la barra |
| AO. Veredicto de la sección 0 para las mejores recetas | **Cerrada** en la tanda 33 (corregida): al 10 %, en T+2 las cuatro recetas pasan la barra (+5,9 a +7,2 pp); en T+1 ninguna, y con clima se cumple A (+3,1 pp) |
| AP. El veredicto de T+2 año por año | **Cerrada** en la tanda 34: consistente; cada logística gana en cinco o seis de siete años en T+2 y ningún año pierde más de un inicio |
| AQ. Qué inicios gana el modelo al 10 % | **Leída** en la tanda 35: el modelo gana donde el canal no ve (pocos casos frente al umbral, municipios poco endémicos) y pierde 13 a 24 inicios donde el canal está seguro |
| AR. Repartir el presupuesto entre el canal y el modelo | **Cerrada** en la tanda 36: ninguna regla supera al modelo solo; dejar al canal las alertas seguras empeora en T+2 (−5 a −6 pp) |
| AS. Anticipación con los dos horizontes juntos | **Leída** en la tanda 37: con las dos listas al 10 %, la logística con clima avisa 353 de 641 inicios frente a 327 del canal |
| AT. El canal como ranking, con cupo fijo por mes | **Cerrada** en la tanda 38: es una línea base más débil que el condicionado; contra ella el modelo pasa la barra en T+2 y, con clima, en T+1 |
| AU. Qué aprende la logística con clima | **Leída** en la tanda 39: el modelo es el margen en escala log; del clima pesa el punto de rocío (+0,42 en T+1), con signo positivo |
| AV. El punto de rocío como único clima | Preinscrita para la tanda 40 |
| AW. Reglas desplegables: umbrales fijados con el año anterior | **Cerrada** en la tanda 41: con umbrales fijados el año anterior, el modelo detecta más con menos alertas (T+2 con clima: 169 con 557 frente a 141 con 601) |
| AX. Las probabilidades como riesgo | **Leída** en la tanda 42: bien calibradas en T+1 y en T+2 (decil alto 0,55/0,53 y 0,35/0,33); T+2 ya no subestima |
| AY. Transferir el modelo de un departamento al otro | Preinscrita para la tanda 43 |
| AZ. Todas las recetas al presupuesto de referencia | **Leída** en la tanda 44: al 10 %, en T+2 pasan 25 de 36 recetas, todas las logísticas con log1p; en T+1 ninguna |
| BA. La curva de presupuesto completa | **Leída** en la tanda 45: en T+2 el modelo pasa la barra desde el 10 %; en T+1, desde el 20 % con clima y el 25 % sin clima |
| BB. Los inicios que nadie anticipa | **Leída** en la tanda 46: la mitad de los inicios no los anticipa nadie y la mitad de esos arranca con cero casos; el modelo gana sobre todo inicios desde cero casos |
| BC. En qué meses del año gana el modelo | **Leída** en la tanda 47: en T+2 gana en todos los trimestres, más en el primer semestre; en T+1 empata en enero-marzo |
| BD. El clima de los meses anteriores | Preinscrita para la tanda 48 |
| BE. El punto de rocío distinto en Meta | Preinscrita para la tanda 49 |

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

## Infraestructura experimental V3 — tarea 17

V3 incorpora un [registro versionado y un ejecutor independiente](experiments/README.md)
para futuros experimentos aprobados, con protocolos/configuraciones congelados,
evidencia agregada inmutable, conclusiones obligatorias y comparación reproducible.
La validación histórica de fábrica T16 conserva su propósito de ingeniería y sus
identidades. Los dos fixtures de aceptación de esta infraestructura son pruebas
técnicas; no se incorporan como resultados científicos ni modifican los hallazgos
anteriores de esta bitácora. No hay selección de campeón ni autorización operativa.
