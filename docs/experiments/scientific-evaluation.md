# Evaluación integrada bajo contrato propuesto

El pipeline `experiment_run` incorpora la evaluación como etapa Kedro y conserva
el lifecycle, registro, tracking e inventario existentes. Las recetas V1/V2
siguen siendo legibles y ejecutables bajo sus controles previos; la evaluación
nueva es explícita en recetas **V3**, sin reinterpretar evidencia histórica.
El [contrato](contrato.md) continúa en `PROPUESTA_PARA_APROBACION`. Todas las
salidas nuevas llevan `VEREDICTO_BAJO_CONTRATO_PROPUESTO`, sin conclusión académica
aprobada, selección de campeón o autorización operativa.

## Un solo flujo y un solo comando

Después de preparar, registrar y aprobar **una identidad nueva** conforme al
[manual](manual_pipeline.md), el comando desde la raíz es:

```sh
uv run --locked --group tracking --directory pipeline kedro run --pipelines experiment_run --params experiment_id=ID_NUEVO_APROBADO
```

`ID_NUEVO_APROBADO` es un marcador: no es un experimento existente ni permiso
para ejecutar uno real. En esta implementación solo se ejecutaron pruebas con
fuentes artificiales. La preparación/aprobación humana de la receta precede al
comando; no hay transferencias manuales de canónicos, predicciones o métricas.

El grafo ejecuta, secuencialmente:

```text
registro/aprobación/reserva
 → adquisición y construcción canónica certificada
 → preparación de todos los brazos/cortes/semillas
 → preflight temporal y soportes de desarrollo
 → entrenamiento y congelación de políticas
 → ambas predicciones por procedimiento
 → lectura diferida de desenlaces
 → scientific_evaluation
 → tracking y registro exclusivo de evidencia
```

Kedro y la API Python comparten `runner.STAGES`, `advance` y la misma finalización;
no existe otro orquestador científico o evaluador externo. El contexto mantiene
la sesión propietaria en memoria, sin copiar conexiones SQLite. Se usa el runner
secuencial; no se acredita ejecución distribuida de esa sesión.

En datos reales se reutiliza la certificación N=3 fijada por hash en la receta:
se verifica el artefacto **consumido** antes de preparar/ajustar. En el fixture
V3 se reconstruye N=3 mediante el certificador existente en tres procesos nuevos.
No se sustituye la certificación histórica ni se certifican tres entrenamientos
por el hecho de certificar tres canónicos.

## Receta V3

Se conservan candidato, preparación, cinco roles, manifiesto, certificado,
semilla nominal y políticas existentes. `schema_version: 3` agrega un bloque
cerrado `scientific_evaluation`:

| Campo | Compromiso que debe declarar la receta |
|---|---|
| `contract.path`, `contract.sha256` | Archivo `docs/experiments/contrato.md` y hash de sus bytes; una edición exige nueva identidad/aprobación. |
| `readings` | `primary`, y opcionalmente `secondary_t2`. |
| `arms` | IDs únicos y predictores canónicos ordenados de cada brazo. La lista superior `predictors` es exactamente su unión. |
| `cuts` | IDs y cinco ventanas completas `roles_by_horizon`; objetivos de evaluación no solapados entre cortes. |
| `seeds` | Lista explícita, ordenada, sin repetidos; se ejecutan todas, sin escoger la mejor. |
| `channel_fraction_grid` | Grilla por horizonte fijada antes de evaluar, o `null` si la decisión está pendiente. |
| `channel_selection` | `max_f1_then_fewer_alerts_then_larger_fraction_on_threshold_selection`. |
| `budget_rate_by_horizon` | Fracción por horizonte comprometida en la receta, o `null`; no se infiere de la evaluación. |
| `budget_rule` | `fixed_rate_monthly_department_cap_floor_ties_by_municipality`. |
| `consistency_rule` | `strict_majority_min_three`, o `null` hasta decidirla. |
| `consistency_vote` | `both_rules_cumple`, o `null`; explicita qué cuenta como mejora para votar. |
| `uncertainty` | `paired_target_month_bootstrap`, 2.000 réplicas, semilla 42, nivel 0,95. |

La plantilla debe declarar `matrix_columns` y configuración nativa de XGBoost
coherentes con los predictores. Las recetas efectivas derivan únicamente cambios
mecánicos declarados: predictores/matriz, semilla/calibrador y ventanas de cada
brazo/corte. Se guardan esas configuraciones e identidades. No se agrega búsqueda,
refit ni una selección silenciosa de variables o hiperparámetros.

La selección por F1, la regla de cupo y el criterio de voto son **opciones
implementadas que la receta debe comprometer**, no decisiones científicas
aprobadas ni valores predeterminados inventados. El contrato exige predeclarar
esas políticas. No se asigna una fracción de capacidad sanitaria por defecto.
Si falta grilla o presupuesto, A/B/C conserva sus cálculos descriptivos en el
punto congelado, pero la utilidad se informa `NO_EVALUABLE` con
`PENDING_RECIPE_POLICY`. Si falta regla/voto, se detiene la consistencia, no las
métricas ni los intervalos independientes de esa decisión.

## Cohortes, comparadores y presupuesto

La lectura primaria exige estado conocido y sin exceso en **T** para ambos
horizontes. La secundaria T+2 incluye ambos estados conocidos en T. La etiqueta
siempre se construye con `domain.onset.build_labels`: no exceso en T+1 y exceso
en T+2. T+1 solo interviene retrospectivamente en ese desenlace, después de las
predicciones. Nunca decide elegibilidad, cupo o alertas en T.

El canal condicionado usa `casos(T) > f_h × P75_h5(T+h)`, con contexto del
canónico disponible en T. `casos(T)` es `dengue_notifications_count` (evento
210), el mismo conteo que construye P75 H5 y las zonas del canónico. La fracción se selecciona en `threshold_selection`,
con la grilla declarada y sin leer evaluación. Modelo y canal reciben la misma
compuerta de la lectura. Se conservan aparte C0 (`f=1`, regla histórica sin
ajuste) y C1 (`exceso(T)`). En la lectura primaria C1 degenera en cero; en la
secundaria puede detectar inicios T+2 y no se reemplaza por ceros.

El cupo es `floor(tasa × N_emisión)` por mes objetivo y departamento, aplicado
antes de consultar etiquetas. Candidato y canal usan el mismo cupo y claves;
se ordenan sus scores congelados con desempate por código municipal. Primero
se aplica su umbral/fracción y después el tope: no se rellenan alertas donde la
regla no alerta para simular igualdad de volumen. Se informa el volumen realizado;
el tope idéntico permite que un método se sature antes. C0/C1 conservan su punto
histórico para A/B/C y no se retocan para pasar C. Si faltan desenlaces, el cupo
original no se recalcula para gastar de nuevo sus alertas en las filas restantes.

## Clima y población común

`X` contiene solo los predictores declarados, con validación de tipos/orden y sin
imputación. El brazo epidemiológico **nativo** no pierde filas por clima ausente.
Con varios brazos se ejecuta también una población **común**, definida por la
completitud de la unión de sus variables en cada uno de los cinco roles. Cada
brazo ajusta un modelo independiente sobre esa población común, proyectando solo
sus propias variables. Así la comparación climática no confunde cambiar
predictores con entrenar/evaluar en otra población.

Las diferencias entre brazos usan claves y etiquetas idénticas, con bootstrap
emparejado por mes, desglosadas por año y territorio. Las coberturas nativas y
comunes llevan IDs diferentes y no se mezclan para favorecer un resultado.

## Salidas y límites de interpretación

Cada celda identifica brazo, población, lectura, corte, semilla, horizonte, año y
territorio. Se reportan vista nacional, Meta/Tolima y cada departamento presente;
son vistas solapadas y **no se suman entre sí**. `N`, `I`, TP, alertas, falsas de
inicio y de exceso y denominadores permanecen explícitos. Una predicción ausente
invalida la comparación; una etiqueta ausente se cuenta y no se convierte en cero.

A/B/C usa C0/C1 y FAR de **exceso**. `carga_FA_inicio_100mm` utiliza inicio y el
soporte común `N`, y nunca se denomina condición B. La utilidad usa el canal
condicionado y ambas cotas de diferencias emparejadas; AP/AUROC/Brier reutilizan
las funciones existentes. Las referencias deterministas conservan AP/AUROC de
sus scores y Brier no aplicable. Los controles aleatorio, alertar todo, canal inflado y
persistencia se reportan; un control que pase invalida la utilidad.

El bootstrap remuestrea meses completos con las mismas multiplicidades para
ambos métodos; no reajusta nada. Se informa calendario/digest, réplicas válidas e
indefinidas. Con menos de dos bloques o alguna réplica indefinida los límites
quedan ausentes; no se inventa precisión. Las celdas con menos de 30 inicios se
reportan sin conclusión científica ni voto. La consistencia se calcula por
semilla y territorio con la regla predeclarada; una celda inválida no se elimina
para mejorar el voto. Las cinco diferencias por semilla, su dispersión y cambios
de signo se reportan también para diferencias de uno o dos inicios.

**Agregación implementada como propuesta, pendiente de aprobación del equipo:**
la función pequeña `aggregate_seed_consistency` en `evaluation/scientific/reporting.py`
consume las consistencias por semilla que ya produce la etapa final
`scientific_evaluation`. Para cada brazo × población × lectura × horizonte ×
territorio conserva la mayoría estricta de cortes utilizables dentro de cada
semilla (mínimo tres) y exige las cinco identidades predeclaradas con `CUMPLE`
para emitir `CUMPLE_BAJO_CONTRATO_PROPUESTO`. No añade métricas, pipelines,
comandos ni ejecuciones. Las vistas anuales no votan como cortes adicionales.

Faltantes de corridas/cortes, políticas o soporte producen `NO_EVALUABLE`;
la semilla ausente se conserva explícitamente con ese estado. Una corrida
inválida produce `INVALIDO` y tiene precedencia; no se elimina por soporte
pequeño. Cinco resultados válidos sin unanimidad (incluido 4/5) producen
`INCONCLUSO_POR_INESTABILIDAD`, sin convertir la mezcla en fallo de efecto.
El resumen no infiere un efecto negativo ni siquiera con 0/5: conserva los
veredictos individuales para su revisión científica. Los cortes excluidos por
soporte se mantienen visibles y 2/3 utilizables sigue siendo mayoría suficiente.

Cada registro `seed_stability` conserva los cinco resultados en `seeds`, los
votos y cortes observados, y las distribuciones existentes. Incluye
`aggregation_rule: all_five_declared_seeds_cumple`,
`contract_status: PROPUESTA_PARA_APROBACION`, `team_approval_required: true` y
`scientific_conclusion: NOT_APPROVED`. T+1 y ambas lecturas de T+2, las
poblaciones, brazos y territorios se agregan por separado. No se escoge la mejor
semilla ni se cuentan semillas como cortes o cohortes independientes. La regla
comprueba sensibilidad algorítmica y requiere aprobación prospectiva del equipo
según el apartado 13 del contrato. Sustituye solo el bloqueo técnico anterior.

Siguen pendientes aprobación del equipo, cohorte confirmatoria independiente y
reproducción E2E N=3 de un eventual finalista. El N=3 canónico no satisface esa
reproducción de modelos. La evidencia retrospectiva ya consumida, incluido 2025,
no se convierte en confirmatoria; 2025 permanece fuera de todo desarrollo.

## Evidencia y aceptación sintética

Se conserva `docs/evidence/experiments/<id>/<execution_id>/` y sus cinco archivos
habituales, más `scientific-0000.json`, etc. Cada fragmento contiene solo agregados,
configuración efectiva, identidades, soportes, compromisos, intervalos y veredictos,
y figura en el inventario de hashes existente. `metrics.json`, MLflow y `compare`
conservan una proyección compacta por dimensiones; el detalle completo vive en
los fragmentos científicos. En V3 los campos heredados de `validation.json`
(soportes, huellas y lecturas) describen la primera variante; cada variante tiene
su registro completo identificado en los fragmentos. Esas proyecciones no se
suman como si fueran lecturas o resultados independientes. No se versionan modelos, matrices,
filas de predicción ni datos crudos. El recibo enlaza fragmentos/contrato y el
registro sigue RUNNING hasta conclusiones humanas; COMPLETED describe el cálculo.
En los recibos V3 nuevos, `scientific_evaluation.summary` proyecta los estados
`seed_stability` de los fragmentos guardados, con brazo, población, lectura,
horizonte y territorio separados. Si el fallo impide calcular la agregación,
la lista queda vacía y el terminal/etapa del recibo identifica el fallo; si ya se
calculó, conserva esos estados incluso en un terminal fallido. Los límites de
aprobación del equipo, confirmación independiente y N=3 finalista siguen pendientes.
Los fallos en cualquier nodo preservan terminal/evidencia y bloquean el registro.
Las evidencias de versiones anteriores conservan sus esquemas y bytes.

Prueba reproducible desde la raíz, sin fuente privada:

```sh
uv run --locked --directory pipeline pytest tests/test_scientific_e2e.py -q
```

Incluye el grafo completo, una invocación CLI Kedro real en repositorio temporal
con MLflow SQLite real, y un fallo inyectado de identidad de predicción. Los datos
son cinco fuentes artificiales con centinelas 2025 y clima faltante; se cotejan
certificado, modelos ajustados, selección de variables y poblaciones de ambos
brazos, inventario y terminales. Es aceptación de software, no evidencia científica.

La regla entre semillas se comprueba además con resultados artificiales, sin ajustar
modelos, en `tests/test_seed_aggregation.py`: 5/5, 4/5, semilla ausente, soporte
insuficiente y corrida inválida; se verifica también la separación de dimensiones,
políticas pendientes, denominadores, identidades y exclusiones por soporte.
