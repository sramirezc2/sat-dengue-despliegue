# Contrato científico de experimentación y decisión — SAT DENGUE V3

- **Versión:** 1.0.0
- **Estado:** `APROBADO`
- **Fecha de revisión:** 11 de noviembre de 2026 (propuesta inicial: 8 de noviembre)
- **Autoridad:** equipo SAT DENGUE
- **Alcance:** todo experimento científico futuro de V3, sin importar la familia
  de modelo, la arquitectura, los predictores o el volumen de datos.

Este contrato define qué significa producir evidencia válida y qué debe superar
un candidato para contribuir a la respuesta del proyecto de grado. No aprueba
un modelo, no selecciona un campeón y no autoriza alertas operativas.
La aprobación del equipo SAT DENGUE se registra por instrucción humana explícita
del 11 de noviembre de 2026, en el commit exclusivo de reconciliación normativa
de esta versión. Rige prospectivamente y no reclasifica resultados históricos.

El PR #3 reunió la propuesta y su implementación técnica, según el historial de
[plan.md](../../plan.md). La implementación y sus
límites se describen en [evaluación integrada](scientific-evaluation.md).
Esto no aprueba recetas, no cambia el evento y no reclasifica experimentos.

## 1. Jerarquía y alcance normativo

V3, el repositorio `sramirezc2/sat-dengue-despliegue`, es la fuente activa. V2
es antecedente y procedencia histórica. Sus resultados y políticas congeladas
se conservan, pero no sustituyen las reglas de un experimento V3.

Este contrato aprobado es la autoridad científica común. La
especificación de cada experimento podrá hacerlo más estricto, nunca omitirlo o
debilitarlo. Ante una contradicción entre este contrato, una especificación y la
configuración ejecutable, el experimento debe detenerse antes de adquirir datos
o entrenar.

Este contrato no reemplaza:

- el contrato de fuentes crudas y construcción canónica;
- los controles temporales implementados por `TemporalPolicy` y
  `guard_development`;
- el registro, los hashes, los estados y la evidencia de la fábrica;
- el contrato JSON de publicación consumido por la API y el tablero.

La especificación T16-FACTORY-XGB-S53-v1 acreditó reproducibilidad técnica de la
fábrica. No es una política de selección científica y no responde por sí sola la
pregunta de grado.

## 2. Pregunta que debe responder el proyecto de grado

> **En los municipios de Meta y Tolima, ¿puede un procedimiento predictivo que
> utiliza únicamente información disponible al cierre del mes T anticipar, para
> T+1 y T+2, una proporción mayor de nuevos inicios de exceso de dengue que el
> canal endémico condicionado, sobre la misma cohorte evaluable y con un
> presupuesto de alertas comparable y fijado antes de la evaluación, sin aumentar
> la carga de falsas alertas más allá de la tolerancia aprobada?**

La respuesta se debe presentar por horizonte. Es válido concluir, por ejemplo,
“sí para T+1 e inconcluso para T+2”; no se deben promediar los horizontes para
ocultar diferencias.

T+1 es el horizonte primario de decisión porque el mes inmediatamente anterior
al objetivo es T y se conoce al emitir la alerta. T+2 es un horizonte secundario
que debe evaluarse separadamente: el estado de T+1 puede utilizarse después para
determinar el desenlace, pero nunca para elegir la cohorte, construir una alerta
o ajustar una decisión emitida en T.

La pregunta histórica se evalúa explícitamente mediante las condiciones A/B/C
del apartado 10.3. La pregunta ampliada y la regla de utilidad del apartado 11
son reglas contractuales adicionales. Sus resultados deben presentarse por separado:
cumplir la regla nueva no convierte un incumplimiento de A/B/C en cumplimiento
académico. La diferencia entre falsas alertas de exceso e inicio y entre sus
denominadores debe permanecer visible.

## 3. Qué afirmaciones puede producir un experimento

| Nivel | Qué acredita | Qué no acredita |
|---|---|---|
| Técnico | El código corre, los contratos pasan y la ejecución es recuperable. | Utilidad científica. |
| Exploratorio | Una hipótesis predeclarada produce un resultado retrospectivo válido. | Confirmación independiente o campeón. |
| Confirmatorio | Una cohorte no usada para diseñar la receta o la política confirma o refuta la hipótesis. | Eficacia sanitaria o uso operativo. |
| Operativo | Una evaluación adicional demuestra disponibilidad, capacidad, seguridad y gobernanza en uso real. | Efecto causal sobre incidencia o salud pública. |

Solo evidencia confirmatoria puede cerrar afirmativamente la pregunta de grado.
Una ejecución técnica o exploratoria puede aportar aprendizaje y una respuesta
provisional, pero debe nombrarse como tal.

## 4. Unidad de análisis, evento y cohorte

### 4.1 Unidad de predicción

Cada observación corresponde a:

```text
municipio DIVIPOLA + mes de origen T + horizonte h + mes objetivo T+h
```

Las claves deben ser únicas, completas y enlazarse por identidad, nunca por la
posición de una fila.

### 4.2 Definición del evento

Se conserva H5 como definición experimental:

```text
exceso(p) = 1 si los casos de dengue de p superan el P75 histórico
            del municipio para ese mes calendario; 0 en caso contrario

inicio(p) = 1 si exceso(p-1) = 0 y exceso(p) = 1
```

- Para T+1, el inicio objetivo es la transición T → T+1.
- Para T+2, el inicio objetivo es la transición T+1 → T+2.
- Una continuación de un exceso ya iniciado no es un nuevo inicio.
- Si falta el estado anterior o el estado objetivo, la etiqueta es no evaluable;
  nunca se convierte en cero.
- H5 no debe presentarse como verdad epidemiológica externamente validada.

### 4.3 Elegibilidad

**Continuidad aprobada con el contrato académico V2:** la cohorte principal
contiene municipios-mes con estado de T observado y sin exceso en T para ambos
horizontes. Se fija antes de evaluar. En T+2 esta restricción define la población
estudiada, no la etiqueta: `inicio(T+2) = [exceso(T+1)=0 y exceso(T+2)=1]`.
No se sustituye por `no exceso en T y exceso en T+2`, que contaría una
continuación iniciada en T+1 como inicio.

La compuerta de emisión es `g_T = 1[exceso(T)=0]`, con estado conocido al cierre
de T. Un estado ausente no habilita alerta. Para T+2 está prohibido seleccionar
filas o alertas usando `g_futura = 1[exceso(T+1)=0]`. El estado de T+1 solo se
lee después del freeze y las predicciones para construir el desenlace; que el
inicio requiera no exceso en T+1 no autoriza a usarlo como compuerta.

En evaluación, la máscara común exige contexto declarado y ambos estados del
desenlace conocidos. Se cuentan las etiquetas ausentes; esa máscara retrospectiva
no puede realimentar entrenamiento, elegibilidad o emisión.

Todos los candidatos y comparadores deben evaluarse sobre exactamente las mismas
claves elegibles y con etiquetas conocidas. Una predicción ausente invalida la
comparación común; no autoriza a reducir silenciosamente la cohorte de un método.

**Contraste con la bitácora, tanda 9, línea Q:** el canal T+2 con compuerta del
origen detectó **209 inicios en 1.190 alertas** (4,69 falsas por acierto); con
compuerta del mes anterior al objetivo detectó **329 en 942** (1,86). Son TP
detectados por dos reglas distintas, no totales de inicios evaluables ni cifras
equivalentes. La bitácora atribuye la diferencia de 120 a información futura.
La segunda regla es un diagnóstico retrospectivo con fuga, inadmisible como
comparador anticipatorio. Este documento cita esos resultados; no los reproduce.

La misma entrada muestra que imponer la compuerta observable al modelo T+2
reduce sus aciertos de **350 a 309**. Por tanto, conservar la cohorte académica
no demuestra que sea la mejor política operativa a dos meses. Se aprueba además
una **lectura secundaria T+2** con todos los estados conocidos en T, tanto
exceso como no exceso, sin esa restricción de emisión para modelo y canal.
Mantiene exactamente el mismo evento T+1 → T+2 y usa soporte común propio,
identificado por separado. Ambas lecturas y sus reglas se predeclaran; no se
elige la favorable después de evaluar. Esta doble lectura debe predeclararse en cada receta; aprobar el contrato no
autoriza una receta o ejecución concreta.

### 4.4 Población primaria

La población primaria de la pregunta académica son los 76 municipios de Meta y
Tolima. Se permite entrenar con información nacional o con fuentes adicionales,
siempre que su disponibilidad y procedencia sean válidas. Los resultados
nacionales u otras geografías son análisis secundarios y no pueden diluir ni
reemplazar el resultado de la población primaria sin una enmienda aprobada antes
de observar la evaluación.

## 5. Regla de información disponible y tratamiento temporal

Una predicción emitida en T solo puede usar variables que habrían estado
disponibles al cierre de T bajo la demora declarada. No basta con que una columna
tenga fecha T: debe demostrarse cuándo la fuente estaba disponible.

Son obligatorios cinco roles separados por **periodo objetivo**, no por posición
de fila:

1. `train`;
2. `calibration_fit`;
3. `calibration_selection`;
4. `threshold_selection`;
5. `evaluation`.

Los roles deben estar ordenados, ser disjuntos y respetar demora y embargo. La
evaluación no puede intervenir en imputación, escalado, selección de variables,
arquitectura, hiperparámetros, early stopping, calibración, selección de
representación, umbral o presupuesto de alertas.

Si un algoritmo requiere una partición adicional —por ejemplo, una red neuronal
con early stopping— debe declararla dentro de los datos de desarrollo antes de
ejecutar. No puede reutilizar `calibration_selection`, `threshold_selection` o
`evaluation` con otro nombre.

El bundle crudo puede contener 2025, pero ninguna observación, origen, objetivo,
etiqueta o transformación aprendida desde `2025-01` puede participar en el
desarrollo. Los resultados de 2025 son evidencia retrospectiva ya consumida; no
son un holdout independiente. Una confirmación futura necesita una cohorte madura
que no haya contribuido a modelos, variables, políticas, umbrales o decisiones.

## 6. Reglas para datos nuevos y preparación

Agregar datos no relaja el contrato. Toda fuente nueva debe declarar y verificar:

- origen, propietario, revisión inmutable, licencia o autorización aplicable;
- esquema, unidad, cobertura, frecuencia, zona horaria y reglas de calidad;
- disponibilidad histórica real, demora, revisiones y riesgo de backfill;
- manifiesto con tamaño y SHA-256;
- transformación exacta hasta la tabla canónica;
- ausencias, duplicados, joins y conservación de conteos;
- riesgo de privacidad y columnas prohibidas.

Kedro debe reconstruir los derivados desde fuentes crudas aprobadas. Una tabla
canónica preparada fuera del pipeline no puede convertirse en fuente científica
por conveniencia. Las transformaciones aprendidas se ajustan únicamente en el
rol autorizado y se aplican congeladas a los roles posteriores.

Un predictor nuevo debe tener semántica, unidad, disponibilidad en T y
procedencia documentadas. Si usa directa o indirectamente el periodo objetivo,
el estado T+1 para predecir T+2, una etiqueta futura o una revisión publicada
después de T, el experimento es inválido aunque sus métricas mejoren.

## 7. Reglas para cualquier familia de modelo

Se permiten árboles, modelos lineales, GAM, redes neuronales, ensambles u otras
familias si cumplen las mismas fronteras. Cada candidato debe declarar antes de
entrenar:

- familia, versión de adaptador y bibliotecas;
- arquitectura completa e hiperparámetros;
- predictores, orden, tipos y preparación;
- semillas y política de determinismo;
- búsqueda de hiperparámetros y espacio de búsqueda, si existe;
- calibración, punto de operación y regla de desempate;
- estrategia de serialización o huella verificable;
- requisitos de hardware que puedan afectar la reproducibilidad.

El modelo debe producir un score o probabilidad por clave y una decisión
derivada de una regla congelada. No se permite cambiar el umbral, elegir una
semilla, descartar filas o retocar la arquitectura después de leer evaluación.

Un artefacto pesado no se versiona en Git. Si conservarlo es necesario, debe
vivir en almacenamiento aprobado con URI inmutable, hash y control de acceso;
de lo contrario, la receta debe permitir reconstruirlo y verificar su identidad.

## 8. Comparadores obligatorios

### 8.1 Comparador primario: canal endémico condicionado

El comparador primario debe usar la misma definición de exceso y la misma cohorte
evaluable que el candidato. Solo puede alertar municipios cuyo estado observable
en T sea no exceso. Su score compara los casos conocidos en T con el P75 del mes
objetivo; la fracción o regla de decisión se selecciona únicamente con datos de
desarrollo y queda congelada antes de evaluación.

Para T+2, el comparador solo puede condicionarse con información observable en T.
Condicionarlo con el estado de T+1 es fuga temporal.

En la cohorte principal del apartado 4.3 se aprueba la decisión
`alerta_canal_h = g_T y [casos(T) > f_h × P75_histórico(T+h)]`, con P75 construido
solo con historia permitida y disponible en T. `f_h`, la grilla, los empates y
el periodo de selección se fijan en desarrollo por horizonte. Modelo y canal
reciben la misma compuerta `g_T`; no se compara modelo sin compuerta contra
canal con ella como si fuera una comparación simétrica. La lectura secundaria
T+2 usa ambos sin `g_T`, con políticas propias predeclaradas. Ninguna usa T+1.

Cada especificación debe declarar la ventana, la grilla y la regla exacta del
canal condicionado. No se admite reconstruirlas después de ver los resultados.

### 8.2 Comparadores históricos y referencias obligatorias

También deben reportarse, sobre las mismas claves:

- canal endémico estándar;
- canal con umbral ajustado, si su regla fue predeclarada;
- persistencia;
- prevalencia de entrenamiento cuando exista una probabilidad constante.

Para A/B/C, el canal es **C0 histórico**, sin fracción ajustada:
`casos(T) > P75_histórico(T+h)`. No se lo sustituye silenciosamente por el canal
condicionado del apartado 8.1. Persistencia es **C1 histórica**:
`alerta_persistencia_h = exceso(T)`, conocida en T para ambos horizontes.
En la cohorte principal sin exceso en T resulta cero siempre; su FAR queda no
definida y el comparador se registra como degenerado por definición de cohorte.
B histórica y la comparación de utilidad frente a persistencia son **no evaluables**;
la decisión aprobada del apartado 11 permite decidir con canal y A/C, sin atribuir
una victoria sobre sus cero aciertos. En una cohorte no restringida, T+1
sigue detectando cero inicios, pero T+2 puede detectar una transición posterior:
no se debe imponer cero por definición a esa lectura.

La validación histórica de fábrica usa `non_excess_persists_no_new_onset`,
de ceros en ambos horizontes. Coincide con C1 solo dentro de la cohorte restringida;
no implementa por sí sola la persistencia histórica para la lectura secundaria.
Persistencia es referencia de la regla nueva y comparador obligatorio de la
**condición B histórica**. La evaluación científica actual usa C1, con B no
exigida en primaria y obligatoria en secundaria T+2. Superarla no acredita
utilidad por sí solo; si no alerta en el soporte secundario, B no es evaluable.

El contrato V2 también conserva C2/R0, C3/G0 regional OFF/ON y C4/G1 nacional.
Solo se citan sus predicciones congeladas si existe identidad y soporte
exactamente comparable; su ausencia se marca NOT_VERIFIED. No sustituyen C0/C1,
no se importan como dependencia y esta revisión no los reentrena ni los aprueba.

### 8.3 Controles negativos

Toda aplicación que pretenda demostrar superioridad debe incluir:

- ranking aleatorio al mismo presupuesto;
- alertar todo;
- canal inflado con alertas aleatorias;
- persistencia.

Si un control negativo satisface la regla de éxito, la aplicación de la política
es inválida y debe revisarse antes de interpretar candidatos.

## 9. Punto de operación y presupuesto de alertas

La comparación primaria se realiza a presupuesto comparable. El presupuesto se
calcula en una partición de desarrollo anterior a la evaluación, mediante una
regla predeclarada vinculada al canal condicionado o a una capacidad operativa
aprobada. El candidato no puede elegir su volumen después de ver los desenlaces.

Se debe publicar la curva de inicios detectados frente a volumen de alertas en
todo el rango común, sin extrapolar puntos inexistentes. Además se debe reportar
el punto predeclarado que decide. Un candidato no mejora por el solo hecho de
bajar el umbral y emitir más alertas.

Si existe una capacidad real de las secretarías de salud, esa capacidad debe
reemplazar el presupuesto proxy mediante una enmienda aprobada antes del
experimento confirmatorio.

**Regla aprobada por el equipo:** para asignar el
cupo del canal, ordenar solo las filas elegibles por exceso absoluto descendente,
`casos(T) − fracción × P75_histórico(T+h)`, con desempate por código municipal
ascendente. Usar la fracción propia del canal (1 para el estándar; la congelada
para el condicionado), tanto al seleccionar en desarrollo como al evaluar, sin
consultar etiquetas de evaluación para fijar la regla. P75=0 no excluye ni da
prioridad automática. Se conservan la elegibilidad y el cupo por departamento y
mes; C0 histórico para A/B/C mantiene su punto sin cupo.

## 10. Métricas y denominadores

Sea `N` el número de municipio-mes evaluables comunes, `I` los inicios reales de
ese soporte, `TP_m` los inicios alertados por el método `m`, `L_m` sus alertas,
`FP_inicio_m = L_m - TP_m` y `FP_exceso_m` sus alertas sin exceso en el objetivo.
Cada salida identifica cohorte, horizonte, corte, territorio y digest de claves.

### 10.1 Métricas de la regla contractual adicional

**Sensibilidad de inicio**

```text
S_m = TP_m / I
```

**Carga de falsas alertas de inicio**

```text
carga_FA_inicio_100mm_m = 100 × FP_inicio_m / N
```

La carga usa un denominador fijado por la cohorte. Se adopta como seguridad de
la regla adicional del apartado 11; no es la condición B académica y no la
reemplaza. El símbolo aislado `B` queda reservado a **B — superar persistencia**.

### 10.2 Métricas complementarias obligatorias

- inicios detectados, omitidos y reales;
- volumen y fracción de alertas;
- FAR de inicio: `FP_inicio_m / L_m`;
- falsas alertas de inicio por inicio detectado: `FP_inicio_m / TP_m`;
- AP, AUROC y Brier cuando sean aplicables;
- cobertura, ausencias y soportes por año, departamento y horizonte;
- FAR histórica de exceso: `FAR_exceso_m = FP_exceso_m / L_m`, obligatoria para
  evaluar la condición C del contrato académico original.

AP y AUROC miden ordenamiento; Brier mide calidad probabilística. Ninguna de las
tres sustituye la utilidad en el punto de operación.

Si el denominador es cero, la métrica se informa como no definida. Nunca se
convierte automáticamente en cero. Las tasas agregadas se calculan desde la suma
de numeradores y denominadores, no promediando tasas de subgrupos.

### 10.3 Evaluación histórica obligatoria A/B/C

Procedencia: [contrato académico V2, versión propuesta 1.0, estado Aprobado](https://github.com/j-mauro-r/SAT-Dengue-V2/blob/447ef9fd85303de61848d2b01733d25c8ad8a935/docs/product/experiments/contrato.md),
apartados 3–8. Se consultó el archivo de ese commit; SHA-256:
`e966bdecac08b2b54e597391cb716a20195ea1a09abacf9ad737f8cd063d4607`.
Ese estado histórico es independiente de la aprobación actual de V3.

Por cada horizonte, sobre exactamente el mismo soporte para modelo, C0 y C1:

| Condición histórica | Cálculo | Denominador y límite |
|---|---|---|
| **A — superar canal C0** | `TP_modelo > TP_canal_C0` | Conteos absolutos; comparar sensibilidades es equivalente solo con el mismo `I > 0`. Sin margen nuevo. |
| **B — superar persistencia C1** | `TP_modelo > TP_persistencia_C1`, solo si el comparador es informativo | Mismo `I > 0`; no evaluable cuando la cohorte primaria obliga a emitir cero alertas. |
| **C — margen de FAR de exceso** | `FAR_exceso_modelo - FAR_exceso_canal_C0 <= 0,05` | Cada FAR divide por las alertas del propio método `L_m`, sobre soporte común. Son cinco puntos porcentuales, no 5 % relativo. |

Las tres deben cumplirse simultáneamente para `ABC_HISTORICA_CUMPLE`.
Si falla una condición definida, se informa `ABC_HISTORICA_NO_CUMPLE`; si falta
un denominador necesario y no hay fallo definido, `ABC_HISTORICA_NO_EVALUABLE`.
Cada condición conserva su estado y numeradores/denominadores, incluso cuando
otra ya falla. Con `I = 0`, A y B quedan no evaluables, aunque los TP sean cero;
con `L_m = 0` la FAR de ese método permanece no definida. Un soporte inválido
invalida la evaluación común. Con `0 < I < 30` se reportan los cálculos
descriptivos y soporte insuficiente, sin conclusión científica ni voto de
consistencia, según el apartado 13.

La persistencia degenerada se identifica con `degenerate: true` y causa
`DEGENERATE_PRIMARY_COHORT`. B queda `null` con estado `NO_EVALUABLE`, aun con
`I > 0` y TP del modelo positivos. A y C conservan sus cálculos y sus posibles
incumplimientos definidos; nunca se emite `ABC_HISTORICA_CUMPLE` apoyándose en B
degenerada. No se reescriben los resultados históricos de T16 o EXP001/EXP002.

Se conservan los puntos de operación históricos al describir resultados previos.
Una evaluación nueva predeclara los suyos; no retoca umbrales para hacer pasar
A/B/C. Una reconstrucción sobre otra cohorte se identifica como nueva lectura,
sin atribuirle los números originales. La lectura secundaria T+2 lleva otro
identificador de soporte y no se combina con la principal para mejorar A o B.

A/B/C mezcla sensibilidad de inicio con FAR de exceso: una continuación alertada
puede reducir la FAR sin anticipar un inicio. Además `L_m` cambia por método.
Estos límites se discuten, pero no autorizan borrar C ni reemplazar B por carga.
El cumplimiento es descriptivo; no prueba significación, anticipación operativa,
eficacia sanitaria ni aprobación de G5/champion. Los resultados ya consumidos,
incluido 2025, permanecen históricos y fuera del desarrollo.

### 10.4 Procedencia del cambio de carga de falsas alertas

La carga por 100 municipio-mes procede de la
[propuesta de política v2 del 4 de noviembre de 2026](../politica-de-decision-v2.md)
y de sus campos `burden`, `utility.threshold_warning` y `evidence_status` en
[el JSON asociado](../politica-de-decision-v2.json). Se propuso **después de
conocer la tanda 5**, además de la evaluación congelada de octubre: persistencia
253 alertas, 151 verdaderas de exceso y cero inicios; en 2018-12, canal 208
alertas/27 falsas de exceso y candidato 69/27. La aplicación exploratoria ya
mostraba G con 3/3 cortes T+1 favorables bajo v2 frente a 0/3 bajo v1, y T+2
sin aprobación por precisión insuficiente. No fue una elección ciega.

La bitácora había agregado también el 4 de noviembre, a partir de la tanda 2,
**falsas por inicio detectado**. Esa razón usa `TP_m` como denominador y no es
la carga poblacional, que usa `N`. Ambas se agregan al reporte; ninguna borra
la FAR histórica. La propuesta V3 inicial del 8 de noviembre incorporó la
carga; esta revisión explicita su procedencia y la separa de A/B/C.

En términos de inicio, cuando `L_m > 0`:
`carga_FA_inicio_100mm_m = 100 × (L_m/N) × FAR_inicio_m`.
No es una transformación equivalente de `FAR_exceso_m`: cambian el evento y
el denominador. Tampoco cinco puntos de FAR equivalen a cinco falsas por 100
municipio-mes. La política v2 heredó el número **5,0**, sin calibrarlo para esa
nueva unidad, y **10,0** para ganancia de sensibilidad. Se adoptan prospectivamente en esta versión, sin reajustarlos tras conocer
resultados. Una futura calibración con capacidad sanitaria requiere enmienda
aprobada antes de observar la evaluación independiente.

## 11. Regla contractual adicional de utilidad

Los siguientes umbrales proceden de la política v2 y quedan aprobados
prospectivamente por el equipo. Se fijan antes de observar una nueva evaluación:

- ganancia mínima de sensibilidad frente al canal condicionado: **10 puntos
  porcentuales**;
- aumento máximo de carga de falsas alertas: **5 alertas de inicio falsas por
  cada 100 municipio-mes evaluables**;
- intervalo: **95 %**, 2.000 réplicas y semilla 42, mediante remuestreo por
  bloques de mes objetivo que preserve el emparejamiento de todos los métodos.

Para cada horizonte, la salida separada `UTILIDAD_PROPUESTA` obtiene `CUMPLE`
solo si simultáneamente:

1. pasa todas las compuertas de datos, tiempo, soporte, identidad y evidencia;
2. se compara con el canal condicionado sobre las mismas claves y el punto de
   operación fue fijado antes de evaluación;
3. en secundaria T+2 supera a persistencia en inicios detectados con comparador
   informativo; en primaria se aplica la excepción aprobada que sigue;
4. la estimación puntual de `S_modelo - S_canal` es al menos 10 puntos y la cota
   inferior de su intervalo también es al menos 10 puntos;
5. la estimación puntual de `carga_FA_inicio_100mm_modelo - carga_FA_inicio_100mm_canal`
   no supera 5 y la cota superior de su intervalo tampoco supera 5;
6. ningún control negativo obtiene `CUMPLE`;
7. el resultado no depende de ocultar un año, departamento o grupo con soporte
   suficiente; toda heterogeneidad material queda reportada.

Esta salida no modifica `ABC_HISTORICA`: un resultado puede cumplir una regla y
fallar la otra, y debe decirlo. La respuesta afirmativa exige utilidad
y las condiciones históricas aplicables (A/C en primaria; A/B/C en secundaria),
además de consistencia y evidencia confirmatoria; esa
articulación queda aprobada en esta versión. Ningún umbral, comparador
o condición cambia a posteriori para resolver una discrepancia favorablemente.

**Decisión aprobada del equipo:** en la lectura primaria B se informa
`NO_EVALUABLE`, causa `DEGENERATE_PRIMARY_COHORT`, y queda fuera del voto. La
utilidad se decide por el canal condicionado, los márgenes de sensibilidad y
falsas alertas, sus intervalos y las demás compuertas; A y C siguen siendo
obligatorias en el voto histórico aplicable. Un `CUMPLE` primario significa que
se superaron esas condiciones, **no** que se superó persistencia. El recibo
expone B, su causa y la base exacta de decisión junto al veredicto.
`ABC_HISTORICA` conserva B `null` y su estado histórico no evaluable si A/C
cumplen; `applicable_abc_status` separa `AC_CUMPLE`, `AC_NO_CUMPLE` o
`AC_NO_EVALUABLE` para votar en primaria, sin simular `ABC_HISTORICA_CUMPLE`.
`INVALIDO` conserva precedencia también en esta proyección.

En la lectura secundaria T+2, B y la comparación de utilidad con persistencia
siguen siendo obligatorias. Si persistencia no emite alertas en el soporte
evaluado, se informa `NO_EVALUABLE` con causa `NO_PERSISTENCE_ALERTS`; no se
convierte una comparación vacía en éxito. Los defectos de validez siguen siendo
`INVALIDO`. La aprobación global del contrato no reinterpreta evidencia previa ni aprueba
modelos, recetas, conclusiones, campeón o uso operativo.

## 12. Veredictos y respuesta final

| Veredicto | Regla |
|---|---|
| `CUMPLE` | La estimación puntual y las dos cotas satisfacen todos los criterios. |
| `NO_CUMPLE_POR_EFECTO` | La estimación puntual ya falla una condición decisoria. |
| `PRECISION_INSUFICIENTE` | La puntual cumple, pero una cota no; se necesita más evidencia. |
| `INVALIDO` | Existe fuga, cambio posterior, soporte incomparable, control negativo aprobado o evidencia inconsistente. |
| `NO_EVALUABLE` | El evento, denominador o soporte no permite calcular la regla. |

La tabla anterior se refiere solo a `UTILIDAD_PROPUESTA`. Se reportan además
`ABC_HISTORICA`, consistencia, soporte y nivel de evidencia, sin un veredicto
global que esconda desacuerdos. La conclusión del proyecto requiere decisión humana y se redacta por horizonte:

- **Sí:** existe un resultado confirmatorio con `UTILIDAD_PROPUESTA: CUMPLE`,
  condiciones aplicables satisfechas (`AC_CUMPLE` en primaria, con B no evaluable
  explícita; `ABC_HISTORICA_CUMPLE` en secundaria) y consistencia según el apartado 13.
- **No con la evidencia evaluada:** una evaluación confirmatoria válida obtiene
  incumplimiento definido de una regla exigida, con soporte suficiente.
- **Inconcluso:** la evidencia es exploratoria, imprecisa, inválida o no
  evaluable.

Un resultado positivo no selecciona automáticamente un campeón. La elección de
modelo requiere revisión humana de estabilidad, cobertura, reproducibilidad,
seguridad, costo, mantenibilidad y disponibilidad operativa.

## 13. Incertidumbre, estabilidad y reproducibilidad

Las referencias **bitácora §4, reglas 3, 4 y 9** (abreviadas históricamente como
**bitácora 4.3, 4.4 y 4.9**) son reglas de método. No son los apartados 4.3
(elegibilidad) y 4.4 (población) de este contrato V3.

**Consistencia — bitácora 4.3.** La regla original exige mejora en al menos
3 de 4 cortes del mismo horizonte; la tanda 6 explicita 2 de 3 utilizables al
excluir 2020-12 por soporte. Se reportan todos los cortes y configuraciones,
incluidos empates, deterioros y resultados no evaluables. La mejora y su regla
de decisión se predeclaran, no se elige el mejor corte o el agregado favorable.

Para otro número de cortes se aprueba prospectivamente **mayoría estricta
de cortes utilizables**, `floor(K/2) + 1`, con al menos **K = 3**. Reproduce
3/4 y 2/3; por ejemplo, exige 4/6 o 4/7. Esta generalización no estaba fijada
para todo K en la bitácora. La especificación debe congelar calendario, K
previsto, regla y qué constituye mejora antes de evaluar; informa después K
utilizable, votos y exclusiones. No se traslada el voto entre horizontes o
territorios ni se cuentan semillas como cortes. Con menos de tres utilizables,
la consistencia queda insuficiente. Un cambio de K previsto requiere nuevo
protocolo aprobado; no se agregan o eliminan cortes tras ver su rendimiento.
No se interpreta como una conversión única del 75 % histórico ni se aplica
retroactivamente a resultados conocidos; la extensión aprobada conserva separada la lectura histórica.

**Soporte — bitácora 4.4.** Cada celda horizonte × corte (o año exterior) ×
territorio declarado necesita **al menos 30 inicios reales evaluables `I`** para
sustentar una conclusión, no 30 filas, alertas o TP. Las celdas menores se
reportan con numeradores/denominadores y estado de soporte insuficiente, sin
votar consistencia ni declarar superioridad o fracaso científico. La bitácora
ejemplifica 14/13 inicios en 2020-12. La exclusión por soporte se predeclara y
no permite descartar un corte suficiente que salió mal; una predicción ausente
es un fallo del soporte común, no una excusa para quitar el corte. Una suma
global puede describirse, pero no valida celdas pequeñas ni oculta heterogeneidad.

**Semillas — corolario de bitácora 4.9.** Ninguna diferencia de **uno o dos
inicios** se presenta como aporte sin la comprobación con **cinco semillas**
predeclaradas para ambos procedimientos estocásticos, mismas particiones y
soporte por par. Se informan las cinco diferencias, dispersión y cambios de
signo; si no está hecha, la diferencia queda descriptiva, con estabilidad
NOT_VERIFIED. La tanda 6 pasó de aparentes 42 frente a 44 a diferencia media
0,00 ± 1,67. Cinco semillas no aumentan I, no sustituyen cortes ni equivalen a
cinco cohortes independientes. Se aplica por celda aunque cambie K.

Los intervalos se calculan sobre diferencias emparejadas entre candidato y
comparador, nunca restando intervalos independientes. Deben conservarse juntos
todos los métodos y desenlaces de cada bloque remuestreado.

Todo candidato estocástico que aspire a sustentar la conclusión debe evaluarse
con al menos cinco semillas predeclaradas. Se reportan distribución, dirección y
casos en que la conclusión cambia; no se escoge la mejor semilla. Un algoritmo
determinista debe demostrarlo con ejecuciones aisladas.

**Agregación entre semillas — regla aprobada prospectivamente.**
Para cada combinación de horizonte, lectura, brazo, población y territorio se
conserva primero la mayoría estricta de cortes utilizables **dentro de cada
semilla**, con mínimo de tres cortes y el voto predeclarado que exige utilidad
y A/C en primaria o A/B/C en secundaria T+2. Un corte secundario con B no
evaluable no aporta voto afirmativo y conserva su causa; la falta en un corte
con soporte suficiente mantiene la consistencia no evaluable. T+1, T+2 primario
y T+2 secundario producen resúmenes separados; tampoco
se mezclan poblaciones nativas/comunes, brazos con/sin clima o vistas territoriales.
Las vistas anuales no se añaden como cortes extra a la consistencia de todos los años.

El resumen exige **exactamente las cinco identidades predeclaradas** en la receta:

| Estado del resumen bajo contrato aprobado | Condición |
|---|---|
| `CUMPLE_BAJO_CONTRATO_APROBADO` | Las cinco semillas tienen soporte y políticas válidos y cada una obtiene `CUMPLE` en su consistencia entre cortes. |
| `NO_EVALUABLE` | Falta una semilla/corrida/corte declarado, no hay cinco identidades predeclaradas, falta una política o denominador necesario, o alguna semilla no alcanza tres cortes utilizables. |
| `INCONCLUSO_POR_INESTABILIDAD` | Los cinco resultados son válidos y evaluables, pero no todos obtienen `CUMPLE`; en particular, 4/5 no basta. |
| `INVALIDO` | Hay una corrida inválida o evidencia inconsistente: duplicados, semilla ajena o soportes no emparejados entre semillas. Tiene precedencia sobre la falta de soporte y no se excluye para mejorar el voto. |

Un corte pequeño predeclarado conserva su exclusión dentro de cada semilla:
2/3 utilizables puede cumplir; no se exige soporte suficiente en todos los cortes
previstos, pero sí el mínimo de tres en cada semilla. Se conservan los cinco
resultados individuales, votos, cortes, exclusiones, diferencias y dispersión;
una semilla ausente lleva un resultado explícito `NO_EVALUABLE`. La agregación
no selecciona la mejor semilla, no suma sus observaciones para aumentar soporte
y no cuenta semillas como cortes independientes. Una mezcla válida **nunca se
convierte en `NO_CUMPLE_POR_EFECTO`**: ese estado pertenece a la regla de utilidad
por celda. Incluso sin ninguna semilla que cumpla, este resumen conservador solo
descarta estabilidad afirmativa; una conclusión de efecto requiere su evidencia
y revisión propias. Los veredictos individuales no se reclasifican.

La justificación es exigir estabilidad de la conclusión frente a la aleatoriedad
del ajuste, evitando que una mayoría de semillas o una selección favorable oculte
una inversión de resultado. La mayoría de cortes evalúa consistencia temporal;
la unanimidad de semillas agrega una comprobación de sensibilidad algorítmica,
sin crear cinco cohortes independientes ni una prueba inferencial adicional.
Es una **decisión prospectiva aprobada**, no una regla histórica ni una regla
elegida por rendimiento observado de EXP004. Se implementó con resultados
artificiales, sin usar 2025 ni ajustar umbrales a resultados reales. Sustituye
el bloqueo técnico `PENDING_SEED_AGGREGATION_RULE`. Cada receta V3 fija el hash del contrato; su cambio requiere identidad y
aprobación nuevas, sin reinterpretar evidencia previa.

Un candidato finalista requiere además una reproducción E2E N=3 con datos,
código, lock, configuración y protocolo fijados. Cuando la plataforma permite
igualdad exacta se comparan bytes y hashes; cuando no la permite, la tolerancia
numérica y la estabilidad del veredicto deben predeclararse. Una corrida
exploratoria puede usar una semilla o una ejecución, pero no cerrar la pregunta.

## 14. Registro y evidencia obligatoria

Antes de ejecutar deben existir y estar aprobados:

- un ID nuevo de experimento;
- `SPECIFICATION.md` con hipótesis, pregunta, único cambio principal, población,
  roles, comparadores, métricas, regla de éxito y limitaciones;
- configuración ejecutable cerrada;
- manifiesto de datos y hashes;
- hashes de protocolo y configuración;
- estado `APPROVED` en el registro;
- revisión científica pre-ejecución.

Después de ejecutar se deben conservar:

- configuración efectiva, código, lock, datos y linaje identificados;
- soportes, exclusiones, decisiones congeladas y métricas agregadas;
- inventario íntegro de evidencia;
- conclusiones con resultado `POSITIVE`, `NEGATIVE` o `INCONCLUSIVE`;
- revisión científica posterior independiente.

Cambiar datos, predictores, semilla, arquitectura, umbral, población, comparador
o criterio crea un experimento nuevo. No se sobrescribe una identidad cerrada ni
se eliminan resultados desfavorables.

## 15. Prohibiciones de interpretación

Está prohibido afirmar superioridad, éxito del proyecto, campeón o utilidad
operativa cuando ocurra cualquiera de estas situaciones:

- se usó 2025 como evaluación independiente;
- faltan el canal condicionado o el soporte común;
- la conclusión se basa solo en AP, AUROC, Brier o exactitud;
- el punto de operación se eligió con evaluación;
- una fuente o predictor no estaba disponible en T;
- se usó T+1 para decidir una alerta T+2;
- se compararon periodos, geografías o cohortes diferentes como si fueran pares;
- se ocultaron denominadores, predicciones ausentes o resultados negativos;
- se interpretó asociación retrospectiva como efecto sanitario causal;
- se confundió reproducibilidad de software con validez científica.

Que ningún modelo supere al comparador es un resultado académico válido. No
autoriza a relajar la política después de observar resultados.

## 16. Compatibilidad con la fábrica V3 actual

| Componente | Estado actual | Consecuencia |
|---|---|---|
| Evento T+1 → T+2 y elegibilidad sin exceso en T | Reutilizados por recetas V3 | Lectura primaria y secundaria T+2 separadas; compuertas solo en T. |
| Cinco roles, calibración y umbral congelado | Implementado | Compatible. |
| Soporte emparejado, AP/AUROC/Brier/sensibilidad/FAR | Implementado | Compatible, con FAR referida a inicio. |
| Registro, hashes, evidencia, conclusiones y comparación | Implementado | Compatible. |
| Canal condicionado y presupuesto | Etapa `scientific_evaluation` de `experiment_run`, recetas V3 | Exige grilla, regla y cupo predeclarados; null detiene la utilidad dependiente. |
| C0/C1 históricos, FAR de exceso y A/B/C | Implementados por horizonte y soporte común | C1 histórica usa exceso en T, también en lectura secundaria. |
| Carga por 100 municipio-mes | Implementada con nombre separado de condición B | Resultado bajo contrato aprobado, sin reemplazar A/B/C. |
| 2.000 bloques emparejados por mes objetivo | Implementados en recetas V3, con réplicas indefinidas visibles | No confiere carácter confirmatorio a datos consumidos. |
| Controles negativos de la política | Implementados, con invalidación si un control cumple | Las conclusiones científicas requieren decisión humana. |
| Cortes y cinco semillas | Ejecutables dentro de una receta V3 | Unanimidad aprobada de cinco consistencias; conserva resultados individuales. |
| Reproducción E2E de eventual finalista | Pendiente | La certificación del canónico no equivale a N=3 de modelos. |
| Consistencia y mínimo de 30 inicios por celda | Aplicados bajo las reglas aprobadas y el voto predeclarado | Celdas pequeñas se reportan sin voto ni conclusión científica. |
| Con/sin clima y horizonte/año/territorio | Implementados en V3, con poblaciones nativas y comunes | Población común en los cinco roles para comparar brazos; cobertura adicional separada. |

Por lo anterior, la fábrica está preparada para ejecutar y preservar
experimentos, pero **ninguna corrida actual puede declarar que respondió
afirmativamente la pregunta de grado**. La implementación se comprueba con fuentes
artificiales; la cohorte confirmatoria y la reproducción finalista continúan pendientes;
las conclusiones científicas y recetas requieren aprobaciones propias. Las evidencias de
T16, EXP001/EXP002 y recetas V1/V2 conservan sus bytes y significado. Las recetas
V3 fijan predictores, población y ausencias antes de ejecutar; la cobertura nativa
adicional no se atribuye al aporte climático medido sobre población común.

## 17. Aprobación y cambios al contrato

El equipo SAT DENGUE aprueba la versión 1.0.0 mediante la instrucción humana
explícita del 11 de noviembre de 2026. Incluye población, doble lectura T+2,
comparadores, A/C primaria y A/B/C secundaria, umbrales de utilidad, soporte,
consistencia y unanimidad de las cinco semillas. La cohorte confirmatoria futura
y cada receta necesitan protocolo y aprobación propios. El commit exclusivo de
reconciliación registra esta decisión; no se inventan nombres o actas adicionales.

**Regla histórica frente a regla contractual.** Los 5 puntos de ganancia de
sensibilidad de la bitácora §0.3 describen una regla histórica y no gobiernan
futuras conclusiones del proyecto. Para contribuir a un resultado afirmativo,
la ganancia frente al canal condicionado y la cota inferior de su IC deben ser
ambas **al menos 10 puntos porcentuales**, además de todas las condiciones
aplicables. Cinco puntos no sustituyen esta regla. Los 5 puntos de FAR de exceso
de C histórica y las 5 falsas por 100 municipio-mes son restricciones distintas,
con sus propias unidades; permanecen intactas.

Las salidas estructuradas nuevas usan `contract_status: APPROVED`; la
documentación muestra `APROBADO`. Recibos, resultados y contratos congelados
anteriores conservan su estado normativo original. Aprobar este contrato no
aprueba ninguna receta, modelo, `scientific_conclusion`, `champion_status` ni
autorización operativa.

La aprobación debe registrar nombres o rol de los aprobadores, fecha y commit.
Toda modificación posterior requiere Pull Request, justificación, análisis de
impacto y aprobación antes de observar los resultados que evaluará. Las versiones
anteriores permanecen en Git; no se reescriben decisiones históricas.

---

### Fuentes revisadas que sustentan el contrato

- [Bitácora experimental](../bitacora-experimental.md): reglas de método §4,
  tanda 6 (3/4, 2/3, soporte y semillas) y tanda 9, línea Q (209 frente a 329).
- [Contrato académico V2](https://github.com/j-mauro-r/SAT-Dengue-V2/blob/447ef9fd85303de61848d2b01733d25c8ad8a935/docs/product/experiments/contrato.md):
  cohorte, comparadores y A/B/C; antecedente versionado, no autoridad de ejecución V3.
- [Política v2 propuesta](../politica-de-decision-v2.md): corrección de la política y sus
  umbrales históricos; la adopción prospectiva V3 se registra aquí.
- `docs/reviews/scientific-review.md`: límites verificados de la fábrica actual.
- `pipeline/src/sat_dengue_pipeline/domain/onset.py`: evento y elegibilidad.
- `pipeline/src/sat_dengue_pipeline/domain/temporal.py`: frontera temporal.
- `pipeline/src/sat_dengue_pipeline/experiments/roles.py`: cinco roles y soporte.
- `pipeline/src/sat_dengue_pipeline/evaluation/metrics.py`: métricas actuales.
- `pipeline/src/sat_dengue_pipeline/evaluation/paired.py`: soporte común e
  incertidumbre descriptiva actual.
- `docs/experiments/manual_pipeline.md`: gobernanza y operación de experimentos.
