# Evaluación emparejada posterior al freeze

La tarea 11 evalúa únicamente después de verificar `FrozenDecisions` y su digest.
`evaluate_procedure` verifica inferencia/calendario antes de invocar el lector de
evaluation.y. El cálculo recibe claves, y, probabilidades, decisiones, controles
y estratos separados. Cada tabla debe contener exactamente las mismas claves
municipio/origen/objetivo/horizonte/fold/candidato; las uniones son uno a uno por
esas claves, no por posición. Se comprueba la cohorte contra el recibo congelado,
el umbral, la prevalencia train-only y la referencia sin nuevo inicio. Se rechaza
cualquier origen, objetivo o disponibilidad de 2025 antes de consultar etiquetas.

## Soporte y denominadores

El soporte único es contexto explícitamente evaluable y etiqueta de inicio
conocida. Se cuentan por separado exclusiones por contexto y por etiqueta
ausente dentro de contexto válido. No se imputan ceros. La unión de predicciones
ausentes de candidato y referencias permanece en ese soporte: invalida las
métricas aplicables de los tres métodos, sin eliminar inicios del denominador.
No se calcula una versión complete-case distinta por método.

- AP no interpolada: entran juntos los empates de score; suma incrementos de
  recall por precisión en cada grupo. Exige ambas clases.
- AUROC: pares positivo/negativo, medio crédito para empate. Numerador = crédito
  de pares, denominador = positivos × negativos. Exige ambas clases.
- Brier: suma de errores cuadrados / población evaluable; solo probabilidades.
- Sensibilidad: alertas verdaderas / todos los inicios conocidos del soporte.
- FAR: falsas alertas / alertas emitidas; sin alertas permanece indefinido.
- Volumen: conteo absoluto de alertas y fracción sobre población evaluable.

Cada registro expone valor, estado/evaluabilidad, numerador/denominador, soporte,
clases, ausencias, candidato/referencia, horizonte y estrato. Persistencia es un
score determinista para ranking, sin Brier; prevalencia no tiene política de
alertas, por lo que sus métricas de decisiones son no aplicables, no ceros.
Las diferencias candidato–referencia usan exactamente el mismo soporte/digest de
claves. Se declara dirección de mejora (mayor/menor) o carácter descriptivo del
volumen. No se selecciona campeón ni se declara superioridad.

## Estratos y diagnósticos

Se reciben departamentos mediante tabla explícita enlazada por claves. Se
reportan global, vista por horizonte y departamentos como partición sin pérdidas;
no se suman vistas global/horizonte/departamento entre sí. El departamento de
cada municipio debe ser consistente. Cada vista incluye total/evaluables,
positivos/negativos, municipios, meses, exclusiones y suficiencia de clases.
Las curvas sobre la grilla predeclarada reportan alertas, TP, FP, sensibilidad,
FAR y volumen relativo con `diagnostic_only=true`. No retornan un nuevo umbral,
no calibran y no modifican el recibo congelado.

## Bootstrap municipal

Se sortean con reemplazo municipios completos de la cohorte de cada estrato,
conservando todos sus meses, incluso ausencias de etiquetas. Un solo calendario
de sorteos se comparte por candidato y referencias. La semilla es explícita;
los códigos se ordenan antes de sortear. Se exponen digests de sorteos y
estadísticas agregadas de cada réplica, nunca códigos municipales en el reporte.
El mínimo configurable se cuenta con municipios con soporte conocido: por
defecto cinco; la muestra de dos municipios devuelve `INSUFFICIENT_CLUSTERS`.

Los intervalos de diferencias son percentiles 2,5/97,5 por defecto, interpolación
lineal tipo 7. Solo se emiten si hay suficientes conglomerados y todas las
réplicas solicitadas son evaluables. Una réplica indefinida se conserva como tal,
se cuenta y no se reemplaza; los límites quedan nulos con `UNDEFINED_REPLICATES`.
Se preserva la estimación puntual válida, separada de `interval_evaluable`.
Todos los intervalos son descriptivos, sin garantía de cobertura calibrada.
La cohorte artificial adicional de seis municipios solo prueba el algoritmo.

## Procedencia histórica

Repositorio `j-mauro-r/SAT-Dengue-V2`, commit
`916a69f3bb73f2ffbb0ec038b8bef887ee91adf1`, blobs leídos mediante git show:

| Archivo | SHA-256 | Regla y adaptación/exclusión |
|---|---|---|
| `src/sat_dengue/metrics.py` | `ebc375bbb9932ec2c6d06e4047e397fe2d3547c989f904a3675bbac27739f862` | AP agrupada, AUROC con empates, Brier y denominadores explícitos; V3 ya recibe etiquetas de inicio, usa soporte común y añade volumen. |
| `src/sat_dengue/model_assessment/comparison.py` | `9b91197ff3388b9c9f8dd125184f13ccc4cc4a38e56c0da85c35a3eef3a543bf` | Diferencias realmente emparejadas, intervalos descriptivos y réplicas indefinidas visibles. Bootstrap de cuatro ventanas NOT_REPRODUCED; se implementa el municipal solicitado. |
| `src/sat_dengue/model_assessment/policy.py` | `38a396906fe4015174527810ae42e5780ef2f8329c5f9fb38de43441a6278cd2` | Frontera temporal y evidencia insuficiente; utilidad, ranking, calendario final/2025 y campeón excluidos. |
| `tests/unit/test_model_metrics.py` | `190871b08fe49856e83076d0d774985cc4f48d3161217c741354b3d5b3e22c91` | Ejemplos independientes, empates, ausencias y denominadores. V3 prueba valores manuales exactos y uniones por claves. |
| `tests/unit/test_model_assessment.py` | `7ec1d85f2cca5f32374bf3dd5dd7be97c4c346cdcc293210b74c167e106ebcc2` | Medio crédito AUROC y no ocultar soporte; no se migran artefactos científicos históricos. |
| `docs/product/stage-5/model_evaluation_contract_v1.json` | `77222e8a2159f6bf68f32541c867e80b497a78fc2a8676950a923ebd91ed38a3` | Mismo soporte y límites retrospectivos; media de cuatro ventanas, incertidumbre temporal reservada y evaluación de 2025 NOT_REPRODUCED. |

No se afirma paridad con V2: hay pruebas manuales exactas de reglas individuales,
no reproducción de sus cohortes o resultados. Son adaptaciones explícitas el
bootstrap municipal, el soporte por etiqueta conocida/contexto y los numeradores
de pares AUROC. Persistencia sigue adaptada a no nuevo inicio según tarea 10.
Las pruebas bloquean red/V2/app/publicaciones y usan solo datos artificiales
hasta 2024. No se leyó el CSV de 426 MB ni datos científicos reales/2025.
La tarea 15 y revisión científica independiente siguen pendientes.
