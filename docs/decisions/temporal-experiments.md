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
