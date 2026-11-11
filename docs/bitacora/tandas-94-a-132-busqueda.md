# Tandas 94 a 132, líneas CY a EK — Resultado de la búsqueda declarada

> Corrida el 11 de noviembre de 2026 sobre el release operacional
> (`de49b11b…`, 76 municipios de Tolima y Meta, 2007-2024). La preinscripción
> está en [`preinscripcion-tandas-94-a-132.md`](preinscripcion-tandas-94-a-132.md)
> y se escribió antes de correr nada.
>
> Estado: **23 de las 39 configuraciones corridas.** Tres pasaron la búsqueda,
> **una sobrevivió a la confirmación.** Las 16 que no corrieron se listan con
> su número en la sección 7; ninguna se reemplazó por otra.

## 1. Lo que hay que saber primero

**Sí hay margen, y es enorme.** La tanda 131 midió el techo: un oráculo que ve el
mes objetivo, emitiendo exactamente las mismas 7,5 alertas al mes que el canal,
detecta **344 de 408 inicios en T+1** donde el canal detecta 173. En T+2,
264 de 306 contra 95. En puntos, el margen disponible al presupuesto de
referencia es de **+41,9 pp en T+1 y +55,2 pp en T+2**.

Esto cambia la lectura de todo el proyecto: **el presupuesto del 10 % no es la
restricción.** Hay cupo de sobra para atrapar casi todos los inicios; lo que
falta es ordenarlos. La tanda 132 lo ancla por abajo: alertar al azar con el
mismo cupo da −26,2 pp, así que el canal tampoco es una línea base boba.

Contra ese telón, el modelo vigente captura **4,4 de los 42 puntos disponibles
en T+1 y 6,9 de los 55 en T+2**.

| Método, al 10 % de presupuesto | T+1 | T+2 |
| --- | --- | --- |
| Piso: alerta aleatoria (tanda 132) | −26,2 pp | −16,0 pp |
| Canal condicionado | referencia | referencia |
| `log_conclima` | +4,4 pp | +6,9 pp |
| Techo: oráculo (tanda 131) | **+41,9 pp** | **+55,2 pp** |

## 2. Los controles negativos pasan (tandas 128 y 129)

Antes de interpretar nada había que descartar que la ventaja del modelo viniera
de algo que no debería estar ahí.

**Tanda 128, línea EG: etiquetas permutadas dentro del mes de origen.** Se
entrena contra etiquetas revueltas y se evalúa contra las verdaderas, que salen
del panel y no del arnés. Tres semillas declaradas de antemano:

| Semilla | T+1 | T+2 |
| --- | --- | --- |
| 11 | −23 | −25 |
| 23 | −40 | −33 |
| 37 | −52 | −37 |

**Tanda 129, línea EH: predictores intercambiados entre municipios del mismo
mes.** Conserva entera la estructura temporal y destruye el vínculo
municipio-predictor:

| Semilla | T+1 | T+2 |
| --- | --- | --- |
| 11 | −101 | −32 |
| 23 | −101 | −47 |
| 37 | −104 | −49 |

Las doce celdas por debajo del canal. No hay fuga.

**Una lectura que conviene dejar escrita para que nadie la malinterprete
después.** En la tanda 128 el modelo nulo detecta 129-158 inicios, bastante por
encima del azar, que a ese presupuesto daría unos 74. Eso **no** es fuga: la
permutación es *dentro* del mes, así que conserva intacto cuántos inicios tiene
cada mes, y el modelo todavía aprende «en los meses que se ven así hay más
brotes». La tanda 129 lo confirma por el otro lado, con 74-91 detecciones, que es
justo el azar. La descomposición queda:

| Qué sabe el modelo | Inicios detectados, T+1, 486 alertas |
| --- | --- |
| Nada (azar) | ~74 |
| Solo en qué mes está | 77-80 |
| El mes, con predictores reales y etiquetas ruido | 129-158 |
| Canal condicionado | 181 |
| El modelo real | 201 |

### Desviación: las dos tandas se corrieron dos veces

La primera corrida tenía un defecto de implementación en el arnés local: el
envoltorio que permuta leía la función original en el momento de crearse, de
modo que la segunda semilla envolvía a la primera y la tercera a las dos
anteriores. Las permutaciones se componían.

El resultado seguía siendo válido como nulo —componer permutaciones uniformes
dentro del mes da otra uniforme dentro del mes, así que eran tres extracciones
legítimas— y las seis celdas salían negativas igual. Pero **las semillas
declaradas no correspondían a lo que había corrido**, y un control que no se
puede reproducir por su semilla no sirve como control. Se arregló y se repitió.
La prueba de que el diagnóstico era correcto: al repetir, la semilla 11 dio
exactamente lo mismo que antes (−23 y −25), porque era la primera vuelta y nunca
estuvo anidada; las que cambiaron fueron la 23 y la 37. Las cifras de arriba son
las de la corrida reproducible.

## 3. Familia 1, tandas 94 a 100: el reparto del presupuesto no es el problema

Siete reglas que no cambian el modelo ni el número de alertas, solo a quién le
tocan, al mismo costo por mes. Medidas contra el canal al 10 %, con
`log_conclima`:

| Tanda | Línea | Regla | T+1 | T+2 |
| --- | --- | --- | --- | --- |
| — | — | *Reparto actual (ranking único)* | *+4,4* | *+6,9* |
| 94 | CY | Cupo por departamento, proporcional a municipios | +0,5 | +3,6 |
| 95 | CZ | Cupo por departamento, proporcional a inicios históricos | +0,7 | +3,3 |
| 96 | DA | Cupo mensual adaptativo | +0,7 | +4,9 |
| 97 | DB | Tope de 4 alertas por municipio al año | +3,9 | +6,9 |
| 98 | DC | Mitad ranking global, mitad por departamento | +2,7 | +6,9 |
| 99 | DD | Umbral absoluto en vez de cupo | −2,5 | −1,3 |
| 100 | DE | Un tercio del cupo reservado a municipios con cero casos | +0,2 | +3,9 |

**Ninguna mejora sobre el reparto de hoy.** Las siete líneas se cierran. Es
consistente con el techo: si el cupo alcanzara para 344 inicios, redistribuirlo
no es donde está el problema.

### Desviación: el criterio preinscrito no discriminaba

La preinscripción fijó como endpoint primario la diferencia contra el canal, y
para esta familia eso **no distingue una regla que mejora de una que no hace
nada**: DB y DC heredan el +6,9 del reparto actual y pasarían el criterio sin
haber aportado. Es la regla 9 —«separar no es aportar»— y esta vez la pisó quien
redactó el endpoint. El criterio correcto para la Familia 1 es la comparación
contra el reparto actual, y con ese criterio no pasa ninguna. Se declara el
cambio y se publican las dos lecturas, como se hizo con la tanda 33.

## 4. Familia 2, tandas 101 a 107: aquí sí hay candidatas

Reglas desplegables: el umbral del modelo **y** la fracción del canal se fijan
con información estrictamente anterior y se aplican al año siguiente. Es la
comparación de la tanda 41, nunca medida contra la barra. Los números no son
comparables con los de la Familia 1, porque allá el canal miraba el año que se
evaluaba y aquí no.

Búsqueda, 2018-2022, con `log_conclima`:

| Tanda | Línea | Regla | T+1 | T+2 |
| --- | --- | --- | --- | --- |
| 101 | DF | Umbral del año anterior | +3,2 | +6,6 (IC −0,9 a 14,1) |
| 102 | DG | Umbral de los dos años anteriores | +5,5 (IC −1,0 a 11,4) | **+10,6 (IC 3,5 a 17,6)** |
| 103 | DH | Histéresis | +4,2 | **+8,4 (IC 0,9 a 15,4)** |
| 104 | DI | Persistencia: dos meses seguidos | −36,7 | −28,6 |
| 105 | DJ | Los dos horizontes en una lista | **+6,8 (IC 3,3 a 10,5)** | |
| 106 | DK | Umbral por departamento | +2,3 | +3,5 |
| 107 | DL | Umbral móvil de doce meses | +2,6 | +4,8 |

**Tres pasan la búsqueda: DG y DH en T+2, y DJ.**

Dos patrones valen más que las cifras sueltas. **DG le gana a DF de forma
consistente**: dos años de historia para fijar el umbral son mejores que uno, y
la tanda 41 solo había probado con uno. Y **DI es un desastre interpretable**:
exigir dos meses seguidos sobre el umbral destruye justo lo que se quiere
detectar, porque un inicio *es* una transición. Es un negativo que explica un
mecanismo.

## 5. La confirmación en la reserva: DJ sobrevive, DG y DH no

Las tres candidatas se midieron **una sola vez** sobre 2023-2024, que no se
había tocado. Denominadores de la reserva: 207 inicios en T+1 sobre 22 meses,
**125 en T+2 sobre 21 meses**.

| Candidata | Búsqueda | Confirmación | Veredicto |
| --- | --- | --- | --- |
| DG, T+2 | +10,6 (IC 3,5 a 17,6) | **−1,6 (IC −11,2 a 8,8)** | **No confirma** |
| DH, T+2 | +8,4 (IC 0,9 a 15,4) | +7,2 (IC −2,4 a 17,6) | **No confirma** |
| DJ, `log_conclima` | +6,8 (IC 3,3 a 10,5) | **+7,5 (IC 1,2 a 14,3)** | **Confirma** |
| DJ, `logc_minima` | +5,1 (IC 1,7 a 8,5) | **+10,6 (IC 4,3 a 17,4)** | **Confirma** |

**DG no se queda corta: cambia de signo.** La candidata más fuerte de la
búsqueda era ruido, y eso es exactamente lo que la reserva existía para
averiguar. DH se queda con el intervalo cruzando el cero.

**DJ es el resultado del proyecto hoy.** Los dos horizontes en una sola lista
operativa, con umbrales fijados el año anterior, pasan la barra y la restricción
C en las dos recetas. Con una advertencia que hay que publicar: emite 297
alertas contra 248 del canal y la carga sube +3,42 por 100 municipio-mes —
dentro del techo de 5, pero parte de la ganancia viene de alertar más. Las
alertas adicionales convierten al 43 %, contra el 47 % promedio del canal.

### Lo que la reserva mostró y no vamos a reportar como hallazgo

En la confirmación, **DG y DH pasan en T+1** con +11,6 (IC 4,3 a 19,3) y +8,7
(IC 1,9 a 16,4), en las dos recetas. T+1 es el horizonte que no ha pasado nada
en todo el proyecto, así que la tentación de reportarlo es grande.

**No se reporta como confirmación.** Las candidatas se inscribieron por lo que
hicieron en T+2 y en T+2 se cayeron; quedarse con el T+1 de la misma mirada es
elegir el horizonte después de ver el resultado. Se publican las cifras —están
arriba— y se declara su estatus: son observaciones nuevas sobre datos que ya se
miraron, no confirmaciones, y **la reserva ya quedó gastada para ellas**. Para
afirmar algo de DG en T+1 harían falta datos que no tenemos.

### Advertencia sobre la potencia en T+2

Con 125 inicios, 5 pp son seis brotes y los intervalos de T+2 miden ±10 pp. «DG
no se confirma en T+2» es en parte una afirmación sobre potencia: con esa
muestra no distinguiríamos +10,6 de cero aunque fuera real. Eso no rescata a DG
—su punto estimado se fue a negativo— pero quien lea esto tiene que saberlo.

### Nota sobre la limpieza de la reserva

La reserva **no estaba limpia para `log_conclima`**: las tandas 33, 44 y 45 ya
midieron esa receta sobre la ventana completa. Lo que nunca se había medido en
ninguna ventana son las reglas DF a DL, que son el objeto nuevo y no se
eligieron mirando 2023-2024. La confirmación de DJ se sostiene sobre esa
distinción, y el que la lea debe poder juzgarla: por eso se escribe.

## 6. Familia 3, tandas 108, 70 y 73: partir la muestra tampoco aporta

Tres estratificaciones, un modelo por estrato, los scores unidos en una sola
lista. Ningún origen omitido en ninguna, y el techo salió idéntico en las tres
(344 y 264), así que las tres uniones cubren exactamente las mismas filas que el
modelo único.

| Tanda | Línea | Estratos | T+1 | T+2 |
| --- | --- | --- | --- | --- |
| — | — | *Modelo único* | *+4,4* | *+6,9* |
| 108 | DM | Cero casos / positivo en el origen (5 571 / 10 845 filas) | +3,2 | +7,2 |
| 109 | DN | Terciles de endemicidad 2012-2017 | +3,2 | +7,2 |
| 112 | DQ | Zona del canal: EXITO-SEGURIDAD / ALERTA-EXCESO | +4,2 | +5,9 |

El mejor caso es +7,2 contra +6,9: **un inicio de 306**. Las tres líneas se
cierran.

**Un dato que refuerza la conclusión en vez de debilitarla.** DM y DN dan
exactamente los mismos conteos (186 y 117) siendo estratificaciones distintas.
Se verificó que no es el mismo modelo: las probabilidades difieren en las 6 358
filas, con diferencia máxima 0,67, y las listas de alertas solo coinciden en 338
de 435 en T+1. Es decir, **se puede cambiar casi una cuarta parte de a quién se
alerta y detectar los mismos inicios**. La capacidad no está en el corte.

Se declara también el supuesto que esta familia necesitaba: los scores de
modelos distintos se ordenan en una sola lista, lo que supone que son
comparables entre sí. El supuesto se apoya en la tanda 42, que encontró las
probabilidades bien calibradas en los dos horizontes.

## 7. Familia 5 parcial, tandas 126 y 127: el efecto no vive en una ventana

| Variante | T+1 | T+2 |
| --- | --- | --- |
| Base: piso 2012, primer origen 2018 | +4,4 | +6,9 |
| Tanda 126 (EE), piso 2014 | +3,4 | +5,9 |
| Tanda 126 (EE), piso 2016 | +1,5 | +4,2 |
| Tanda 127 (EF), primer origen 2019 | +3,9 | +8,4 |

**La tanda 127 pasa limpio**: mover el primer origen evaluado no cambia el
resultado, así que el efecto no vive en 2018.

**La tanda 126 encuentra algo que importa para el informe**: el efecto se degrada
de forma monótona al acortar la historia de entrenamiento —6,9 → 5,9 → 4,2 en
T+2— y con el piso en 2016 **cae por debajo de la barra**. O sea que el
resultado del proyecto depende de tener la historia larga, y por lo tanto del
release operacional 2007-2024 y no del histórico. Es un argumento concreto a
favor de la decisión de panel que se tomó en la tanda 11.

Los denominadores de la tanda 127 son distintos (308 y 227 inicios, con el techo
en 41,9 y 59,9), así que de ella se lee el signo y el orden de magnitud, no la
cifra exacta.

## 8. Lo que no se corrió, con su número

Dieciséis de las 39. Ninguna se reemplazó por otra y ninguna se retiró.

| Tandas | Líneas | Por qué no corrieron |
| --- | --- | --- |
| 71, 72 | DO, DP | Necesitan columnas nuevas en la matriz —indicador de cero casos y sus interacciones— y el catálogo de derivadas es cerrado: es cambio de repositorio |
| 74, 75 | DR, DS | Necesitan pesos por muestra, y el adaptador exige `class_balancing: false` como parte de la identidad autorizada. La forma correcta es un bloque `pesos:` declarado en la receta, que también es cambio de repositorio |
| 115 | DT | Modelo de dos etapas: familia de candidato nueva |
| 77 a 82 | DU a DZ | Familia 4 entera: el bloque de presión de vecindad no existe todavía |
| 83 a 86 | EA a ED | Robustez de semillas y remuestreo; faltó tiempo |
| 130 | EI | El canal condicionado contra sí mismo con otra fracción; faltó tiempo |

## 9. Verificación contra las reglas de método

| Regla | Cómo se cumplió |
| --- | --- |
| **4.1** Bloque de 2025 consumido | No se tocó. La búsqueda llegó a 2022-12 y la confirmación a 2024-12 |
| **4.2** El umbral no se elige sobre los datos con que se mide | Toda la Familia 2 fija umbral y fracción con años estrictamente anteriores. El primer año evaluado no emite y se descuenta de los denominadores |
| **4.3** Consistencia entre cortes | Se reportan las 23 corridas, no la mejor. Las tandas 126 y 127 son la verificación explícita |
| **4.4** Tamaño de muestra declarado | Cada celda con su denominador. La advertencia de potencia de T+2 en la reserva está en la sección 5 |
| **4.5** La prevalencia cambia entre periodos | El cupo se recalcula por mes de origen; las reglas desplegables, por año |
| **4.6** Fuga por la etiqueta | Medida directamente en la tanda 128 |
| **4.7** Las dos líneas base sobre las mismas filas | Verificado en la Familia 3 con el techo idéntico, y exigido por el arnés en el resto |
| **4.8** Preinscripción antes de mirar | La preinscripción tiene fecha anterior a la primera corrida |
| **4.9** Separar no es aportar | La desviación de la sección 3 es precisamente esta regla, declarada |
| **4.12** Una corrida que no midió nada no puede terminar en verde | `verificar_panel` aborta si el panel no es el declarado; el arnés local fuerza el corte de la reserva; y en la Familia 2 se descartan las fracciones del canal que no emiten ninguna alerta, que habrían dado una comparación vacua en verde |

**Multiplicidad.** 23 configuraciones medidas en búsqueda, tres pasaron, una
sobrevivió a una confirmación reservada. El número de configuraciones probadas
se reporta en el cuerpo del informe, no en un anexo.

## 10. Qué significa todo junto

El techo dice que hay 42 y 55 puntos disponibles. Repartir el presupuesto de
otra forma no los alcanza (Familia 1). Partir la muestra por régimen tampoco
(Familia 3). Lo único que replicó fue DJ, que **no cambia el modelo**: cambia
cómo se usan sus dos horizontes.

La lectura es que la limitación no está en cómo ordenamos ni en cómo troceamos,
sino en la información que traen las variables. Eso es coherente con la tanda 46
—la mitad de los inicios no los anticipa nadie— y señala hacia dónde valdría la
pena mirar: variables que hoy no están en el panel, no recombinaciones de las
que ya están.

Y sobre la pregunta que decide el proyecto: al presupuesto de referencia, con la
regla confirmada, el modelo supera al canal condicionado por **+7,5 pp con la
cota inferior en 1,2** en la reserva. Pasa la barra de la sección 0.3. En T+1
sigue sin pasar nada que se pueda afirmar.
