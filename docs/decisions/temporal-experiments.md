# Contratos temporales de experimentación V3

Fuente histórica: `j-mauro-r/SAT-Dengue-V2`, commit inmutable
`916a69f3bb73f2ffbb0ec038b8bef887ee91adf1`. Se consultan blobs con `git show`,
sin importar V2, ejecutar notebooks ni acceder a datos o modelos históricos.

## Tarea 8: protocolo mínimo expansivo

`experiments/rolling.py` declara un protocolo JSON con horizonte separado T+1/T+2,
semilla, demora mínima de etiquetas, límite reservado y calendario. Por defecto:
objetivos de entrenamiento desde enero de 2018, primer origen enero de 2019,
último objetivo diciembre de 2024. 2018 es calentamiento, no validación sin
entrenamiento previo. Se crea un fold por mes hasta noviembre de 2024 para T+1
(71 folds) u octubre para T+2 (70). El horizonte se suma por calendario.

En cada fold, el rango objetivo de entrenamiento empieza fijo y acaba en
`origen - 1 - demora`. Además se exige `label_available_period < origen` y
origen de entrenamiento anterior al consumidor. Una demora observada mayor que
la mínima también se respeta. Las ventanas nominales son expansivas; el soporte
efectivo puede excluir ausencias, X incompleto o filas no elegibles, sin imputar
ceros. Se reportan tamaños, máximo objetivo y disponibilidad realmente utilizados.
No se afirma crecimiento estricto de filas si la fuente no aporta nuevos ejemplos
utilizables; la muestra artificial sí demuestra inclusión estricta entre folds.

Claves, X, y y controles se reciben separados, enlazados por índices y claves
municipio/origen/objetivo/horizonte. El puente `from_prepared` consume la salida de
la tarea 7. X conserva el esquema canónico cerrado. La inferencia no recibe y:
las etiquetas de validación permanecen fuera del ejecutor y no se rellenan con 0.
Cada fold exige una instancia nueva no ajustada y entrega copias de sus entradas.
Las predicciones conservan claves y fold, separadas de etiquetas observadas.
La semilla y el calendario contribuyen al digest del protocolo y al ID de fold;
el orden físico de filas y los resultados no los determinan.

La compuerta valida todas las claves antes de consultar etiquetas: origen,
objetivo o disponibilidad desde enero de 2025 provocan rechazo antes de crear
un modelo. No hay selección aleatoria, shuffle, red, persistencia o publicaciones.
La única ejecución de pruebas usa un doble determinista sin valor científico.

## Procedencia, reglas y diferencias

| Blob histórico | SHA-256 | Regla/adaptación |
|---|---|---|
| `src/sat_dengue/training_preparation/temporal.py` | `0949a54c6b7db537e3f89c02875ff4efa05d43b573eb9f3f88b9a4bc6d065d0a` | `select_window`: objetivo exacto, separación y auditoría. V3 usa folds mensuales con entrenamiento expansivo. |
| `src/sat_dengue/model_evaluation/availability.py` | `bf5761effaf0ec8b881523a1590fe681f5137d5285798ecbf71c2a8f26cf6a71` | `availability_transition`: madurez por etiquetas y dependencias, no solo por origen. V3 exige anterioridad estricta. |
| `src/sat_dengue/experiments/onset.py` | `48a186010eba73b61acf4f56766cbe8b9c48ce1e6118d6c9b6985eb038d57285` | Calendario y frontera de predictores; etiquetas/elegibilidad siguen en la tarea 7. No se importa la reserva rígida de 2024. |
| `tests/unit/test_training_temporal.py` | `9b24470378b9cba4525581212c7aa326b16ca4a14bc10c5c042adcdcfb070c8d` | Referencia de pruebas de separación, ocho ventanas y ausencia; V3 añade invariancia futura y digest. |
| `docs/product/stage-4/README.md` | `96c4930d3c9c6af2134411a82d48054c14c745d7044b3023ebdadd385f58ce85` | Límite de evidencia sintética y prohibición de ajuste con 2025; no se reproduce replay privado. |

`NOT_REPRODUCED`: los ocho cortes históricos 2018-12, 2020-12, 2022-12 y
2024-06 por dos horizontes, sus validaciones de seis meses y cohortes originales.
Sus fechas están documentadas en V2, pero no se reconstruyen preparadores, fuentes
privadas, readiness ni selección interna de modelos en esta tarea. El protocolo
mínimo V3 es mensual y no constituye una prueba de equivalencia con esas ventanas.
También difiere la disponibilidad: V2 permite igualdad al cierre mensual;
V3 exige `<` como opción conservadora conforme a la anterioridad solicitada.
No se certifican latencias operativas reales ni paridad exacta con V2.

La muestra construye directamente 166/164 filas artificiales para T+1/T+2,
dos municipios ficticios de Meta y Tolima, con una ausencia de X y otra de y.
No procede del CSV local de 426 MB. Las pruebas normales bloquean acceso a V2,
red, app y publicaciones. La reproducción con release público sigue pendiente
en tarea 15, y la revisión científica independiente no se sustituye por estas
pruebas. CI remota y ruleset conservan DEC-006.

## Tarea 9: contrato neutral de adaptadores

`models/adapters.py` define `ModelAdapter`, `AdapterSpec`, registro explícito y
`CheckedAdapter`. La identidad contiene familia, versión, JSON canónico y semilla;
el candidato incluye su digest. El registro está vacío por defecto y rechaza
reemplazos silenciosos, identidades diferentes o instancias previamente ajustadas.
`run_candidate` reutiliza exactamente el arnés de tarea 8 y comprueba también
que un constructor no reutilice el backend dentro de wrappers distintos.

`fit(X, y)` exige esquema canónico completo/ordenado, ambas clases, índices
alineados y valores finitos. La inferencia acepta exclusivamente X con tipos
congelados, sin y, controles ni claves. Cada llamada entrega copias y detecta
mutaciones del backend. Se rechazan probabilidades ausentes, no numéricas, no
finitas, fuera de [0,1] o con índice/longitud incorrectos. La salida común contiene
municipio, origen, objetivo, horizonte, fold, candidato y `raw_probability`;
las etiquetas permanecen en el objeto separado de entrada. La procedencia registra
implementación, configuración, semilla, esquema y estado ajustado.

| Blob histórico | SHA-256 | Regla/adaptación |
|---|---|---|
| `src/sat_dengue/model_training/contract.py` | `c8b7527f92c6cb5807c0f49f5ab9f8133abec229b610dce68d93f52663d85d9a` | Fallo cerrado ante contrato inválido; V3 usa ValueError y configuración explícita, sin autoridad JSON histórica implícita. |
| `src/sat_dengue/model_training/candidate_families.py` | `0b96f5069cc805e9ad274b1eba91c36e6a62280433b95bc9394792ef8d47e77e` | Despacho compartido de familias e interfaz fit/predicción; V3 usa Protocol y registro vacío sin importar frameworks. |
| `src/sat_dengue/model_training/candidate_preparation.py` | `7c7a328e84370da8e196d56f610d44d710625e0fdec580595f931cb13b2ca78c` | Alineación, ambas clases y exclusión de controles retrospectivos. No se migra preparación/ablation de estimadores. |
| `src/sat_dengue/model_training/reference_workflow.py` | `92e0c57f86f7adeb31f84b327c4839eedb05898d8b2fd78342386d09dd017a2a` | Enlaces ventana/municipio/origen/objetivo/horizonte y probabilidad separada; sin métricas o publicación heredadas. |
| `tests/unit/test_model_training.py` | `a081ddc0a6e31f25df8749a9ade019a7189523ccdca2eec3f77f5c41c30e56b1` | Pruebas de alineación y columnas futuras; V3 añade mutación, backend nuevo y contratos de probabilidad. |

Sin dependencias nuevas. Dos familias de dobles viven exclusivamente en tests,
sin interpretación científica. `NOT_REPRODUCED`: adaptadores XGBoost/LightGBM/GAM,
representaciones, búsquedas, ablations, formatos nativos y replay de componentes
históricos. No se agrega adaptador genérico de estimadores sin una necesidad
concreta, ni se afirma paridad de predicciones con modelos V2. Los cuatro miembros
pueden implementar el mismo Protocol sin incorporar calendarios, calibración,
umbrales o métricas en sus adaptadores.

## Tarea 10: decisiones anteriores a evaluación

`experiments/roles.py` exige exactamente `train`, `calibration_fit`,
`calibration_selection`, `threshold_selection`, `evaluation`, ordenados por
objetivo y sin solapamientos. Cada ventana debe contener los meses declarados;
el mínimo de ingeniería es dos meses y una fila por clase en cada rol de
ajuste/selección, configurable al alza mediante el contrato. Las filas deben
ser elegibles y completas, sin convertir ausencias en ceros ni reducir cohortes
silenciosamente. No se leen etiquetas de evaluación para validar clases.

Además de `max(objetivos anteriores) < min(objetivos siguientes)`, se comprueba
`max(disponibilidad de etiquetas productoras) + embargo < min(orígenes consumidores)`.
El embargo adicional es explícito y no se asigna a entrenamiento. Los huecos
necesarios por horizonte también quedan fuera de los roles. Las cinco entradas
pasan la compuerta de claves/soporte antes de invocar cualquier lector de y o
constructor. `RoleBatch.read_y` difiere la lectura hasta la etapa que la consume;
el callback de evaluación no se llama durante ajuste, selección ni inferencia.

Un candidato predeclarado se ajusta una sola vez en train. No se seleccionan
hiperparámetros ni candidatos. Sus predicciones alimentan los tres roles siguientes,
sin refit. `LogisticRegression(solver="lbfgs", max_iter=1000, C=1, random_state=seed)`
ajusta una sigmoide sobre la probabilidad original exclusivamente en
calibration_fit. Se rechazan ausencia de clases, soporte insuficiente o falta
de convergencia. Se retienen solo coeficiente/intercepto numéricos. En
calibration_selection se elige sigmoide únicamente si mejora Brier en más de
1e-12; en empate o sin mejora se conserva original. Estos Brier son estadísticas
de selección, no una implementación de las métricas finales de tarea 11.

Se agregan scikit-learn 1.7.2 y SciPy 1.18.1, las versiones del pyproject V2 fijado
(huella ya registrada en la decisión de migración). scikit-learn evita programar
un optimizador de calibración propio; SciPy, dependencia necesaria de sklearn,
se declara también directamente porque se usa `special.expit` para inferencia
numérica estable con parámetros congelados. Dependencias transitivas nuevas:
joblib 1.6.0, threadpoolctl 3.8.0 y cloudpickle 3.1.2; no se usa persistencia pickle.
Referencias de API:
[LogisticRegression 1.7.2](https://scikit-learn.org/1.7/modules/generated/sklearn.linear_model.LogisticRegression.html)
y [SciPy expit](https://docs.scipy.org/doc/scipy/reference/generated/scipy.special.expit.html).

`ThresholdPolicy` requiere una tupla ordenada y única con límites 0/1 y una cota
absoluta FAR explícita, sin valor científico implícito. La muestra usa décimas y
cota 1 solo como ejemplo artificial, no como política de alertas aprobada.
Solo threshold_selection selecciona: máxima sensibilidad de inicio entre umbrales
con `FP/alertas <= cota`; empates por menos falsas alertas, menor FAR y mayor
umbral. Cero alertas mantiene FAR ausente y no puede ser factible. Si no existe
umbral factible, se rechaza; no hay sustitución manual, fallback ni ajuste al
evaluar. La representación probabilística ya está congelada antes de esa etapa.

Las referencias comparten exactamente las claves y horizonte del candidato:
prevalencia constante calculada solo con y_train, y persistencia de no exceso
observado en T. Esta última predice **sin nuevo inicio** para ambos horizontes;
es determinista, no una probabilidad calibrada. En la cohorte elegible es una
referencia degenerada de ceros, consecuencia explícita de mantener el estado
sin transición. Estado desconocido o exceso en T no se admite como elegible.
La prevalencia se entrega como probabilidad sin inventar una decisión binaria
con el umbral del candidato. No se coerciona FAR de persistencia sin alertas a 0.

`FrozenDecisions` guarda parámetros, representación, política/grilla, umbral,
prevalencia, disponibilidad, procedencia, auditoría y digests de las entradas
de ajuste/selección. No incluye y ni valores X de evaluación. JSON y SHA-256
permiten roundtrip verificado; el objeto es inmutable y `predict_frozen` exige
el digest esperado, sin parámetro de override. Se conserva un único modelo
ajustado en memoria, sin serializarlo ni versionarlo. La salida separa claves,
probabilidad original, representación seleccionada, decisión y referencias.
`fold_id=procedure-<digest>` enlaza la evaluación de ese plan congelado, distinto
de los folds mensuales de prueba del arnés. Cada candidato/horizonte puede
declarar su plan, sin duplicar calendarios o selección en el adaptador.

La evaluación posterior conserva todas las claves declaradas; sus etiquetas
siguen separadas, incluso si son ausentes. La futura tarea 11 deberá aplicar
la misma máscara de evaluabilidad a candidato y referencias, contar ausencias
y calcular métricas sin realimentar decisiones. Aquí no se calcula ese reporte.

### Fuentes adicionales consultadas

| Blob histórico | SHA-256 | Regla/adaptación o exclusión |
|---|---|---|
| `src/sat_dengue/model_training/references.py` | `e6434f0cdc069e1f22380a8d9176865e0dfc7b4cba750defe10f4a786baf4445` | Prevalencia solo train; persistencia de exceso adaptada explícitamente a persistencia sin inicio en cohorte no exceso. |
| `src/sat_dengue/model_evaluation/calibration.py` | `4e9824befde37530e9929c6ff5b9b50440ffd29fd58d1d82637bf52b8c7bbf95` | `_fit_sigmoid`, aplicación numérica, elección por Brier y orden de desempates de umbral; solo reglas mínimas, no módulo completo. |
| `src/sat_dengue/model_evaluation/contract.py` | `df818f8244079410dc85dec7bbb1b74b06da0a63a71672bd88ca445fc3de52e8` | Roles/soporte/disponibilidad previos; V3 usa cinco roles y anterioridad estricta. |
| `src/sat_dengue/model_evaluation/decision_policy.py` | `61a784b46cd59968f62cfcb9135e51afbb024e25e57924c9c0e9a645117d8aa4` | No override silencioso ni autorización automática; no se migran ranking/knobs humanos/G5. |
| `docs/product/stage-4/model_engineering_contract_v1.json` | `70f2d1e8a5fe8dd950b3be9bd453fc953b07187f5a092e692c3dfe8918e21862` | Definiciones de referencias y fronteras de contexto; grillas de familias y métricas completas excluidas. |
| `docs/product/stage-5/README.md` | `a5042f29b8000de3c283ea7d510019fafa0149472aa9906ea304ceffc0d69d3e` | Disponibilidad por etiquetas y separación de roles; no se ejecutan procedimientos históricos o replay privado. |
| `docs/product/stage-5/probability_calibration_thresholds_contract_v1.json` | `9ec4be02eee61bf546ed3127755dbcc78ab5a0511342d88165dbee3018a41bb3` | Original/sigmoide, funciones de roles y congelación. Adaptación mínima de soporte y grilla explícita. |
| `docs/product/stage-5/model_evaluation_contract_v1.json` | `77222e8a2159f6bf68f32541c867e80b497a78fc2a8676950a923ebd91ed38a3` | Disponibilidad y mismo soporte de referencias; métricas completas, incertidumbre y bloque reservado excluidos. |
| `docs/product/stage-5/champion_decision_policy_v1.json` | `29b5d6d7924c74d0c0b1f3cd2e588d1ab587a22c3f59b64d385469246f7a4ec8` | Contexto histórico de utilidad humana y no aprobación; no se adoptan valores como defaults V3. |
| `tests/unit/test_model_evaluation.py` | `9529848f2e4652b9f7c1e5c983c59160ed36f1e599228f2817788d70db453fb0` | Tests de disponibilidad, denominadores y desempate; V3 añade lectores/consumidores espía y freeze sin evaluación. |

`NOT_REPRODUCED`: calendarios internos/externos exactos V2, búsqueda y refit
externo, calibración por bins soportados y desempate por gap, grilla derivada de
probabilidades redondeadas y utilidad relativa a persistencia con knobs humanos.
La persistencia de exceso no es la etiqueta de inicio; su versión de inicio
es una adaptación explícita y su FAR sin alertas no define una cota relativa.
Por eso V3 exige una cota absoluta declarada por el llamador y no atribuye paridad
a las decisiones. El soporte mínimo artificial no sustituye los mínimos de bins
históricos ni prueba suficiencia científica. No se reproducen componentes o
resultados reales, no se leen observaciones/etiquetas científicas de 2025 y no se
autoriza un modelo, un umbral operativo o un campeón.

Los tests de ingeniería usan solo filas artificiales hasta 2024 y verifican
ambos horizontes, fronteras por origen, clases, soporte, callbacks de evaluación
prohibidos, ajustes únicos, estabilidad ante futuro, referencias, JSON y digest.
No se agrega un pipeline operativo ni persistencia; `synthetic` permanece igual.
Los JSON publicados solo intervienen en las regresiones de producto autorizadas
(DEC-009), nunca como datos científicos. Tarea 15, revisión independiente, CI
remota y ruleset siguen pendientes.
