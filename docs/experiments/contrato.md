# Contrato científico de experimentación y decisión — SAT DENGUE V3

- **Versión:** 0.1.0-propuesta
- **Estado:** `PROPUESTA_PARA_APROBACION`
- **Fecha:** 8 de noviembre de 2026
- **Autoridad requerida:** equipo SAT DENGUE
- **Alcance:** todo experimento científico futuro de V3, sin importar la familia
  de modelo, la arquitectura, los predictores o el volumen de datos.

Este contrato define qué significa producir evidencia válida y qué debe superar
un candidato para contribuir a la respuesta del proyecto de grado. No aprueba
un modelo, no selecciona un campeón y no autoriza alertas operativas. Mientras
no exista aprobación formal del equipo, este documento es una propuesta
normativa: sirve para revisar y cerrar las decisiones pendientes, pero no
reclasifica resultados históricos.

## 1. Jerarquía y alcance normativo

V3, el repositorio `sramirezc2/sat-dengue-despliegue`, es la fuente activa. V2
es antecedente y procedencia histórica. Sus resultados y políticas congeladas
se conservan, pero no sustituyen las reglas de un experimento V3.

Después de su aprobación, este contrato será la autoridad científica común. La
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

La pregunta histórica —superar al canal endémico y a persistencia sin aumentar
la FAR en más de cinco puntos porcentuales frente al canal— se debe conservar y
reportar para trazabilidad. No puede ser la única regla de decisión: la bitácora
demostró que mezcla sensibilidad de inicio con falsas alarmas de exceso y usa un
denominador que cambia con el número de alertas del candidato.

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

La cohorte principal contiene municipios-mes con estado de T observado y sin
exceso en T. La elegibilidad se decide exclusivamente con información disponible
en T. Para T+2 está prohibido condicionar la cohorte o la alerta con el estado
observado de T+1.

Todos los candidatos y comparadores deben evaluarse sobre exactamente las mismas
claves elegibles y con etiquetas conocidas. Una predicción ausente invalida la
comparación común; no autoriza a reducir silenciosamente la cohorte de un método.

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

Cada especificación debe declarar la ventana, la grilla y la regla exacta del
canal condicionado. No se admite reconstruirlas después de ver los resultados.

### 8.2 Referencias descriptivas obligatorias

También deben reportarse, sobre las mismas claves:

- canal endémico estándar;
- canal con umbral ajustado, si su regla fue predeclarada;
- persistencia;
- prevalencia de entrenamiento cuando exista una probabilidad constante.

Persistencia es una referencia, no el comparador decisivo: en T+1 detecta cero
inicios por construcción. Superarla es necesario para conservar trazabilidad con
la pregunta histórica, pero no demuestra utilidad.

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

## 10. Métricas y denominadores

Sea `N` el número de municipio-mes evaluables comunes, `I` el número de inicios,
`TP` los inicios alertados, `A` las alertas y `FP_inicio = A - TP`.

### 10.1 Métricas decisorias

**Sensibilidad de inicio**

```text
S = TP / I
```

**Carga de falsas alertas de inicio**

```text
B = 100 × FP_inicio / N
```

La carga usa un denominador fijado por la cohorte, no por el candidato. Es la
métrica de seguridad primaria.

### 10.2 Métricas complementarias obligatorias

- inicios detectados, omitidos y reales;
- volumen y fracción de alertas;
- FAR de inicio: `FP_inicio / A`;
- falsas alertas de inicio por inicio detectado: `FP_inicio / TP`;
- AP, AUROC y Brier cuando sean aplicables;
- cobertura, ausencias y soportes por año, departamento y horizonte;
- FAR histórica de exceso: alertas sin exceso / alertas emitidas, solo para
  reproducir y discutir el criterio académico original.

AP y AUROC miden ordenamiento; Brier mide calidad probabilística. Ninguna de las
tres sustituye la utilidad en el punto de operación.

Si el denominador es cero, la métrica se informa como no definida. Nunca se
convierte automáticamente en cero. Las tasas agregadas se calculan desde la suma
de numeradores y denominadores, no promediando tasas de subgrupos.

## 11. Regla propuesta de éxito científico

Los siguientes umbrales proceden de la política v2 propuesta y todavía requieren
aprobación formal del equipo. Se mantienen visibles para que no puedan elegirse
después de observar una nueva evaluación:

- ganancia mínima de sensibilidad frente al canal condicionado: **10 puntos
  porcentuales**;
- aumento máximo de carga de falsas alertas: **5 alertas de inicio falsas por
  cada 100 municipio-mes evaluables**;
- intervalo: **95 %**, 2.000 réplicas y semilla 42, mediante remuestreo por
  bloques de mes objetivo que preserve el emparejamiento de todos los métodos.

Para cada horizonte, un candidato obtiene `CUMPLE` solo si simultáneamente:

1. pasa todas las compuertas de datos, tiempo, soporte, identidad y evidencia;
2. se compara con el canal condicionado sobre las mismas claves y el punto de
   operación fue fijado antes de evaluación;
3. supera a persistencia en inicios detectados;
4. la estimación puntual de `S_modelo - S_canal` es al menos 10 puntos y la cota
   inferior de su intervalo también es al menos 10 puntos;
5. la estimación puntual de `B_modelo - B_canal` no supera 5 y la cota superior
   de su intervalo tampoco supera 5;
6. ningún control negativo obtiene `CUMPLE`;
7. el resultado no depende de ocultar un año, departamento o grupo con soporte
   suficiente; toda heterogeneidad material queda reportada.

La FAR histórica con margen de cinco puntos porcentuales se reporta en paralelo
para responder el contrato académico original, pero no invalida por sí sola un
resultado que cumple la regla coherente de inicio y carga poblacional. Cualquier
decisión distinta debe aprobarse como enmienda antes de ejecutar.

## 12. Veredictos y respuesta final

| Veredicto | Regla |
|---|---|
| `CUMPLE` | La estimación puntual y las dos cotas satisfacen todos los criterios. |
| `NO_CUMPLE_POR_EFECTO` | La estimación puntual ya falla una condición decisoria. |
| `PRECISION_INSUFICIENTE` | La puntual cumple, pero una cota no; se necesita más evidencia. |
| `INVALIDO` | Existe fuga, cambio posterior, soporte incomparable, control negativo aprobado o evidencia inconsistente. |
| `NO_EVALUABLE` | El evento, denominador o soporte no permite calcular la regla. |

La conclusión del proyecto se redacta por horizonte:

- **Sí:** existe al menos un resultado confirmatorio `CUMPLE`.
- **No con la evidencia evaluada:** una evaluación confirmatoria válida obtiene
  `NO_CUMPLE_POR_EFECTO`.
- **Inconcluso:** la evidencia es exploratoria, imprecisa, inválida o no
  evaluable.

Un resultado positivo no selecciona automáticamente un campeón. La elección de
modelo requiere revisión humana de estabilidad, cobertura, reproducibilidad,
seguridad, costo, mantenibilidad y disponibilidad operativa.

## 13. Incertidumbre, estabilidad y reproducibilidad

Los intervalos se calculan sobre diferencias emparejadas entre candidato y
comparador, nunca restando intervalos independientes. Deben conservarse juntos
todos los métodos y desenlaces de cada bloque remuestreado.

Todo candidato estocástico que aspire a sustentar la conclusión debe evaluarse
con al menos cinco semillas predeclaradas. Se reportan distribución, dirección y
casos en que la conclusión cambia; no se escoge la mejor semilla. Un algoritmo
determinista debe demostrarlo con ejecuciones aisladas.

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
| Evento de inicio, elegibilidad y guard temporal | Implementado | Compatible. |
| Cinco roles, calibración y umbral congelado | Implementado | Compatible. |
| Soporte emparejado, AP/AUROC/Brier/sensibilidad/FAR | Implementado | Compatible, con FAR referida a inicio. |
| Registro, hashes, evidencia, conclusiones y comparación | Implementado | Compatible. |
| Canal endémico condicionado | No implementado en `experiment_run` | Bloquea una afirmación de superioridad académica. |
| Carga de falsas alertas por 100 municipio-mes | No implementada como métrica decisoria | Bloquea aplicar la regla propuesta. |
| Intervalo confirmatorio de 2.000 bloques por mes objetivo | No implementado; V3 usa bootstrap municipal descriptivo | Bloquea un veredicto confirmatorio. |
| Controles negativos de la política | No implementados en la salida científica | Bloquea validar la compuerta. |
| Cinco semillas y reproducción finalista | No automatizados por una sola receta | Deben organizarse como experimentos registrados. |

Por lo anterior, la fábrica está preparada para ejecutar y preservar
experimentos, pero **ninguna corrida actual puede declarar que respondió
afirmativamente la pregunta de grado**. Primero deben implementarse y aprobarse
los comparadores y métricas decisorias anteriores, sin modificar la evidencia
cerrada de T16, EXP001 o EXP002.

## 17. Aprobación y cambios al contrato

Antes de convertir esta propuesta en norma, el equipo debe aprobar explícitamente:

1. la redacción de la pregunta central y que T+1 sea primario;
2. Meta y Tolima como población primaria, aunque se entrene con datos nacionales;
3. el canal condicionado como comparador decisivo;
4. los umbrales de 10 puntos de sensibilidad y 5 falsas por 100 municipio-mes;
5. el método de incertidumbre, las cinco semillas y la reproducción N=3;
6. la cohorte futura que podrá considerarse confirmatoria.

La aprobación debe registrar nombres o rol de los aprobadores, fecha y commit.
Toda modificación posterior requiere Pull Request, justificación, análisis de
impacto y aprobación antes de observar los resultados que evaluará. Las versiones
anteriores permanecen en Git; no se reescriben decisiones históricas.

---

### Fuentes internas que sustentan esta propuesta

- `docs/bitacora-experimental.md`: pregunta, errores descubiertos y comparadores.
- `docs/politica-de-decision-v2.md`: corrección propuesta de la política y sus
  umbrales aún no aprobados.
- `docs/reviews/scientific-review.md`: límites verificados de la fábrica actual.
- `pipeline/src/sat_dengue_pipeline/domain/onset.py`: evento y elegibilidad.
- `pipeline/src/sat_dengue_pipeline/domain/temporal.py`: frontera temporal.
- `pipeline/src/sat_dengue_pipeline/experiments/roles.py`: cinco roles y soporte.
- `pipeline/src/sat_dengue_pipeline/evaluation/metrics.py`: métricas actuales.
- `pipeline/src/sat_dengue_pipeline/evaluation/paired.py`: soporte común e
  incertidumbre descriptiva actual.
- `docs/experiments/manual_pipeline.md`: gobernanza y operación de experimentos.
