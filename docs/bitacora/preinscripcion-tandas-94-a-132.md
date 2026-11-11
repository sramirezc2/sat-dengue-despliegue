# Preinscripción de la búsqueda: tandas 94 a 132 (líneas CY a EK)

Escrita el 11 de noviembre de 2026, **antes de correr nada**. Numerada desde la
tanda 94 porque las tandas 52, 53 y 54 —líneas BH, BI y BJ— ya estaban
preinscritas por otra persona del equipo cuando esta se escribió; se deja dicho
para que el salto de numeración no parezca un hueco. Lo que sigue fija
la pregunta, el diseño, la barra, el criterio de fracaso y la lista completa de
configuraciones que se van a medir. Ninguna se agrega después, y las que se
caigan por tiempo se declaran como no corridas, no se borran de la lista.

---

## 1. Qué es esta preinscripción, y qué no

Es una **búsqueda declarada**, no una tanda confirmatoria. Su producto no es un
veredicto: es una lista ordenada de candidatas y el número exacto de
configuraciones que se probaron para llegar a ella.

Esto hay que decirlo con claridad porque el enunciado natural —«probemos muchas
cosas hasta que el modelo le gane al canal»— es exactamente lo que las reglas
4.8 y 4.3 de esta bitácora prohíben, y por una razón que no es formal. Con 39
configuraciones y un intervalo del 95 %, **alrededor de dos pasan la barra por
puro azar aunque ninguna sirva**. Si corremos 39 y reportamos la que ganó,
estamos reportando ruido con cara de hallazgo, y la primera pregunta de
cualquiera que lea el informe va a ser cuántas se probaron.

El diseño de abajo resuelve eso. No haciendo menos experimentos: haciendo que
el experimento que decide no sea ninguno de los 39.

### Lo que esta búsqueda no puede cambiar

- **La barra.** Está en la sección 0.3 y se queda como está (ver §2).
- **La definición de inicio de brote.** Es la de la propuesta de grado: exceso
  sobre el P75 del canal en `p` sin exceso en `p-1`. Ninguna tanda de esta lista
  la toca. Cambiar qué cuenta como acierto para que el modelo gane es mover el
  arco, y se nota.
- **El bloque de 2025.** Consumido (regla 4.1). No se mide contra él.
- **La tabla canónica.** Ninguna derivada entra al artefacto; todas se
  construyen en preparación, como hasta ahora.

### Lo que sí se reporta pase lo que pase

El informe va a decir, en el cuerpo y no en un anexo: **se probaron 39
configuraciones en búsqueda, de las cuales N pasaron, y M sobrevivieron a la
confirmación.** Si N es 0, se escribe que es 0. La sección 0.4 ya tiene
redactado qué significa eso y por qué es un resultado y no un fracaso.

---

## 2. La barra, y por qué esta y no la otra

Hubo durante varias tandas una ambigüedad entre «5» y «10» que conviene dejar
cerrada por escrito, porque no eran dos valores candidatos de lo mismo:

| | Barra de la sección 0.3 | Compuerta G5 (`champion_decision_policy_v1.json`) |
| --- | --- | --- |
| Línea base | **Canal condicionado** | Persistencia |
| Ganancia mínima | **5 pp**, cota inferior sobre cero | 10 pp sobre la cota inferior |
| Techo de falsas | +5 por 100 municipio-mes | +5 pp sobre la razón, cota superior |
| Estado | **Vigente para el veredicto del proyecto** | Documentada como estructuralmente insatisfacible para un detector de inicios |

La G5 compara contra la persistencia, que en T+1 detecta **cero inicios por
construcción** y por eso mismo tiene una razón de falsas baja. La bitácora ya
dejó la prueba de que esa compuerta no mide lo que dice medir: **el canal
endémico la pasa en los tres cortes**, con aumento de falsas negativo, porque
alerta donde el exceso ya está. Un detector de inicios tiene que alertar donde
el exceso todavía no está, y eso le sube la razón de falsas mecánicamente.

El veredicto de este proyecto corre contra la barra de la sección 0.3. La G5
queda citada como lo que es: una compuerta del artefacto, ya analizada, que no
aplica a la pregunta.

---

## 3. Diseño: búsqueda y confirmación reservada

**Fase de búsqueda (esta noche).** Las 39 configuraciones se miden con
`ultimo_objetivo: 2022-12`. Los orígenes de 2023 y 2024 **no se tocan**: no se
miran, no se grafican, no se usan para decidir nada.

**Fase de confirmación (después, una sola vez).** Las configuraciones que pasen
la barra en búsqueda se vuelven a medir con `ultimo_objetivo: 2024-12`, y ese
resultado es el que va al informe. Una medición por candidata, sin ajustes
entre una y otra.

Por qué así y no con una corrección de multiplicidad: una corrección de Holm
sobre 39 pruebas nos deja una barra efectiva tan alta que nada va a pasarla, y
además castiga igual a una familia de seis variantes de la misma idea que a
seis ideas distintas. La reserva temporal es más honesta y más barata: la
candidata tiene que volver a ganar en años que nunca vio, y si lo hace, el
número de cosas que probamos antes deja de importar.

**Qué pasa si una candidata pasa en búsqueda y falla en confirmación:** se
reporta así, con las dos cifras. Es información, no un experimento perdido.

**Qué pasa si ninguna pasa la búsqueda:** no hay fase de confirmación, y el
veredicto es el de la sección 0.4.

---

## 4. Endpoint primario y criterio de fracaso

**Primario.** Al presupuesto de referencia (10 % de los 76 municipios por mes de
origen, sección 0.1), diferencia en puntos porcentuales de inicios detectados
frente al canal condicionado, con intervalo del 95 % por **bloques de mes de
origen**. T+1 y T+2 se reportan por separado y ninguno sustituye al otro.

**Pasa la búsqueda** si la diferencia es ≥ 5 pp **y** la cota inferior está
sobre cero, en al menos uno de los dos horizontes.

**Restricción de seguridad (C).** La carga de falsas alertas por 100
municipio-mes no supera en más de 5 a la del canal, ni su cota superior. Una
configuración que falle C no pasa aunque gane en detección.

**Secundarios, declarados ahora para que no se elijan después:** la curva de
presupuesto completa (5, 10, 20 %), el año por año, y la lectura por
departamento. Son descriptivos y no deciden nada.

**Criterio de fracaso de una línea:** si el efecto es menor a 2 pp o el
intervalo contiene el cero, la línea se cierra y no se reabre con otra variante
de la misma idea sin un mecanismo nuevo escrito.

---

## 5. La lista

Receta de referencia para todo lo que sigue: **la logística con clima**
(`conf/retroanalisis/noche/log_conclima.yml`), que es la configuración que
quedó de la tanda 50. Donde una línea diga «sobre la mínima», es
`conf/retroanalisis/noche/logc_minima.yml`: la mínima de cinco variables de la
tanda 17 más las nueve de clima de la tanda 22. No confundirla con
`log_minima.yml`, que es la mínima **sin** clima.

### Familia 1 — Cómo se reparte el presupuesto (tandas 94 a 100)

El cupo son ~8 alertas al mes asignadas por un ranking único sobre los 76
municipios, así que Tolima y Meta compiten en la misma lista. La tanda 25 dice
que en T+1 toda la ventaja del modelo es de Tolima (+22) y en Meta empata (+2);
la tanda 43 dice que los dos departamentos no son intercambiables. Si el ranking
global le está dando cupos a Meta que no convierte, repartirlo cambia qué
alertas salen **al mismo costo total**. Es la primera familia que ataca la
asignación y no el score. **Ninguna de estas siete reentrena nada**: se calculan
sobre las predicciones ya producidas.

| Tanda | Línea | Mecanismo | Predicción preinscrita |
| --- | --- | --- | --- |
| 94 | CY | Cupo por departamento proporcional a municipios (47/29) | Si el cupo mal repartido ata a T+1, ≥ 5 pp; si el problema es el score, < 2 pp y se cierra |
| 95 | CZ | Cupo por departamento proporcional a inicios históricos | Igual que CY pero con el reparto que iguala oportunidad, no tamaño |
| 96 | DA | Cupo mensual adaptativo: más alertas en temporada alta, mismo total anual | La concentración estacional de inicios (tanda 47) se traduce en ≥ 5 pp |
| 97 | DB | Tope por municipio al año: ningún municipio consume más de k cupos | Evita que pocos municipios endémicos se coman el presupuesto; ≥ 5 pp o se cierra |
| 98 | DC | Mitad del cupo por ranking global, mitad por departamento | Intermedio entre CY y el actual; sirve para saber si el efecto es monótono |
| 99 | DD | Umbral absoluto de probabilidad en vez de cupo | El total de alertas deja de ser fijo; se reporta contra el canal al mismo número realizado |
| 100 | DE | Cupo reservado para municipios con cero casos en el mes de origen | La tanda 46 dice que ahí es donde el modelo gana; reservarles cupo debería amplificarlo |

### Familia 2 — Reglas desplegables (tandas 101 a 107)

La tanda 41 encontró algo que no se llevó al veredicto de la sección 0: con
umbrales fijados con el año anterior, el modelo **detecta más con menos
alertas** (T+2 con clima: 169 con 557 frente a 141 con 601). Eso es ganar en los
dos ejes a la vez, y está sin medir contra la barra. Tampoco reentrenan.

| Tanda | Línea | Mecanismo | Predicción preinscrita |
| --- | --- | --- | --- |
| 101 | DF | La regla de la tanda 41 medida contra la barra de la sección 0.3 | Si el resultado de la 41 es real, ≥ 5 pp en T+2 |
| 102 | DG | Umbral fijado con los dos años anteriores en vez de uno | Más estable, menos reactivo; se cierra si no mejora la varianza entre años |
| 103 | DH | Histéresis: alertar sobre X, mantener la alerta hasta Y < X | Reduce alertas intermitentes sobre el mismo municipio sin perder inicios |
| 104 | DI | Persistencia: alertar solo con dos meses seguidos sobre el umbral | Sube precisión a costa de anticipación; se cierra si pierde más de 10 inicios |
| 105 | DJ | T+1 y T+2 en una sola lista operativa (extiende la tanda 37) | La 37 leyó 353 de 641 frente a 327 del canal; medirlo contra la barra |
| 106 | DK | Umbral por departamento, fijado con el año anterior de ese departamento | Combina DF con lo que dice la tanda 43 sobre no intercambiarlos |
| 107 | DL | Umbral fijado con la partición interna del entrenamiento, no con el año calendario | Cumple 4.2 de otra forma; sirve de control de DF |

### Familia 3 — Estratificar por tipo de municipio (tandas 108 a 115)

La tanda 46 es el hallazgo más fuerte sin explotar: la mitad de los inicios no
los anticipa nadie, la mitad de esos arranca con cero casos, y **el modelo gana
sobre todo inicios desde cero casos**. Un solo modelo para los 76 municipios
tiene que servir a dos regímenes distintos a la vez. Estas sí reentrenan.

| Tanda | Línea | Mecanismo | Predicción preinscrita |
| --- | --- | --- | --- |
| 108 | DM | Modelo separado para filas con cero casos en el origen | ≥ 5 pp, concentrado en los inicios desde cero que la 46 identificó |
| 109 | DN | Modelo separado por terciles de endemicidad histórica | Igual que DM con una partición continua en vez de binaria |
| 110 | DO | Un modelo, con indicador de cero casos y sus interacciones | Captura lo mismo sin partir la muestra; control de DM |
| 111 | DP | Interacción cero casos × clima | La 39 dice que del clima pesa el rocío; probar si pesa distinto según régimen |
| 112 | DQ | Modelo separado por zona del canal en el origen | La zona ya es predictor; estratificar por ella es otra forma de la misma idea |
| 113 | DR | Reponderar el entrenamiento hacia los inicios desde cero casos | Sin partir la muestra ni agregar variables |
| 114 | DS | Pesos por inverso de la frecuencia de inicios del municipio | Evita que los endémicos dominen el ajuste |
| 115 | DT | Dos etapas: probabilidad de salir de cero, y de superar el P75 | Descompone el problema en los dos eventos que la 46 separó |

### Familia 4 — Vecindad, no departamento (tandas 116 a 121)

La línea BG (tanda 51) cerró la presión regional **a escala de departamento**:
gana 21 y pierde 24. El mecanismo declarado ahí era que un departamento entero
es demasiado grueso para que el contexto diga algo del municipio. Esa es una
hipótesis sobre la **escala**, no sobre la idea, y se puede falsar bajando la
escala. Si a escala de vecindad tampoco aporta, la idea se cierra entera y eso
también es un resultado.

| Tanda | Línea | Mecanismo | Predicción preinscrita |
| --- | --- | --- | --- |
| 116 | DU | Presión epidémica de los municipios adyacentes | ≥ 5 pp; si no, la idea de contexto espacial se cierra para toda escala |
| 117 | DV | Presión de los k vecinos más cercanos por distancia entre cabeceras | Variante de DU sin depender de la tabla de adyacencia |
| 118 | DW | Exceso del municipio más poblado del departamento | Hipótesis de difusión desde el centro urbano |
| 119 | DX | Casos del departamento vecino con rezago de uno y dos meses | Difusión entre departamentos, no dentro |
| 120 | DY | Vecindad × cero casos | Dónde debería aparecer el contexto si aparece: donde el municipio no tiene señal propia |
| 121 | DZ | Velocidad de la presión de vecindad, sin el nivel | Separa tendencia de estado, como se hizo en G |

### Familia 5 — Robustez de lo que ya gana (tandas 122 a 127)

No son hipótesis nuevas: son el precio de poder afirmar algo. Si la logística
con clima va al informe, tiene que resistir el cambio de semilla, de partición y
de remuestreo.

| Tanda | Línea | Mecanismo | Predicción preinscrita |
| --- | --- | --- | --- |
| 122 | EA | La logística con clima, cinco semillas | El efecto no cambia de signo en ninguna |
| 123 | EB | La mínima con clima, cinco semillas | Igual; la 17 dice que la mínima no pierde más de 5 puntos |
| 124 | EC | Remuestreo con 10 000 réplicas en vez de 2 000 | Los intervalos no se mueven más de 1 pp |
| 125 | ED | Remuestreo por municipio y por mes reportados juntos en todas las candidatas | Ya se hace en `veredicto.py`; dejarlo como requisito |
| 126 | EE | Sensibilidad al piso de entrenamiento (2012 contra 2014 y 2016) | El efecto no depende de cuánta historia se use |
| 127 | EF | Sensibilidad al primer origen evaluado (2018 contra 2019) | Control de que el resultado no vive en un año |

### Familia 6 — Controles negativos (tandas 128 a 132)

Si ninguna de las cinco familias anteriores produce nada, estas cinco dicen si
el problema es el modelo o es la pregunta. Son las que hacen que un resultado
negativo sea publicable en vez de simplemente decepcionante.

| Tanda | Línea | Mecanismo | Predicción preinscrita |
| --- | --- | --- | --- |
| 128 | EG | Etiquetas permutadas dentro de cada mes de origen | El efecto debe ser 0 ± ruido. Si no, hay fuga y todo lo anterior se cae |
| 129 | EH | Predictores permutados entre municipios del mismo mes | Control de que la ventaja no viene de la estructura temporal sola |
| 130 | EI | El canal condicionado contra sí mismo con otra fracción | Calibra cuánto se mueve la métrica sin cambiar de método |
| 131 | EJ | Techo: un oráculo que ve el mes objetivo, al mismo cupo | Cuánto hay disponible para ganar; si el techo está cerca del canal, no hay nada que buscar |
| 132 | EK | Piso: alerta aleatoria al mismo cupo | Ancla inferior de la escala de la métrica |

La tanda 131 es la que más me interesa de esta familia y conviene correrla
**primero**, antes que las 38 restantes: si un oráculo con información perfecta
al 10 % de presupuesto apenas le saca unos pocos puntos al canal condicionado,
entonces el margen que estamos buscando no existe, y eso cambia qué vale la pena
correr esta noche.

---

## 6. Orden de la corrida y costo

El orden no es arbitrario: va de lo que puede invalidar lo demás, a lo que
depende de que lo demás siga en pie.

| Paso | Qué | Reentrena | Costo estimado |
| --- | --- | --- | --- |
| 0 | Predicciones de referencia con `log_conclima.yml` y `logc_minima.yml`, T+1 y T+2, hasta 2022-12 | sí | ~40 min |
| 1 | Tandas 131 y 132 (techo y piso) | no | minutos |
| 2 | Tandas 128 y 129 (controles negativos) | sí | ~40 min |
| 3 | Familias 1 y 2 completas (tandas 94 a 107) | **no** | ~20 min las catorce |
| 4 | Familia 3 (tandas 108 a 115) | sí | el grueso de la noche |
| 5 | Familia 4 (tandas 116 a 121) | sí | lo que quede |
| 6 | Familia 5 (tandas 122 a 127) | sí | mañana si no alcanza |

Las catorce tandas de las familias 1 y 2 no reentrenan nada: se calculan sobre
las predicciones del paso 0. Por eso valen la pena primero — catorce hipótesis
por el precio de veinte minutos.

**Si la noche no alcanza**, se corren en este orden y las que queden sin correr
se declaran como no corridas en la bitácora, con su número. No se reemplazan por
otras ni se silencian.

---

## 7. Verificación contra las reglas de método

| Regla | Cómo se cumple aquí |
| --- | --- |
| **4.1** Bloque de 2025 consumido | No se toca. La búsqueda llega a 2022-12 y la confirmación a 2024-12 |
| **4.2** El umbral no se elige sobre los datos con que se mide | Las tandas 101 a 107 fijan umbrales con el año anterior o con la partición interna, nunca con el año que miden |
| **4.3** Consistencia entre cortes | Se reportan las 39, no la mejor. El año por año es secundario declarado |
| **4.4** Tamaño de muestra declarado | Cada celda con su denominador; con menos de 20 inicios no se concluye |
| **4.5** La prevalencia cambia entre periodos | El cupo se recalcula por mes de origen, no se fija absoluto |
| **4.6** Fuga por la etiqueta | La tanda 128 lo mide directamente con etiquetas permutadas |
| **4.7** Las dos líneas base sobre las mismas filas | Canal condicionado y persistencia sobre el conjunto común, como ya hace `conjunto_comun` |
| **4.8** Preinscripción antes de mirar | Este documento, con fecha, antes de correr |
| **4.9** Separar no es aportar | Toda la familia 4 lo necesita: BG separaba y no aportaba |
| **4.12** Una corrida que no midió nada no puede terminar en verde | `verificar_panel` aborta si el panel no es el declarado |

**Multiplicidad.** Declarada: 39 configuraciones en búsqueda, confirmación
reservada en 2023-2024, y el número de configuraciones probadas se reporta en el
cuerpo del informe.
