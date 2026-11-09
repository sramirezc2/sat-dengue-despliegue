# Pipeline SAT DENGUE: adquisición y preparación

[Reporte ejecutivo: entregables, evidencia y límites](../docs/reports/pipeline-e2e-executive-report.md).

Subproyecto Kedro independiente del despliegue. Incluye el smoke de cinco etapas,
dominio científico, construcción/certificación desde crudos, fábrica reproducible
y administración de experimentos registrados. No es un modelo aprobado ni
autoriza alertas.

La [guía operativa central](../docs/operations/pipeline-operations.md) reúne
preparación multiplataforma, recuperación, límites y migración de almacenamiento.
El [manual de la fábrica](../docs/experiments/manual_pipeline.md) documenta el
ciclo experimental y el [catálogo](../docs/agents/skills-catalog.md) selecciona
las cuatro skills reutilizables de operación, revisión, verificación y recuperación.

Requisitos: Python 3.12 y uv (validado con 0.11.19). Dependencias fijadas en
`pyproject.toml` y resueltas en `uv.lock`: Kedro 1.7.0, pytest 9.2.0 y Ruff 0.17.4.
La adquisición agrega `huggingface_hub` 2.4.0; la preparación usa NumPy 2.5.4
y pandas 3.0.6. No se requieren AWS, credenciales,
datos externos ni servicios desplegados para ejecutar las pruebas o el sintético.

En macOS, XGBoost 3.0.5 necesita el runtime nativo OpenMP de Homebrew:
`brew install libomp`. El lock de Python no instala esta biblioteca del sistema.
La matriz de CI la instala solo en el runner macOS antes de ejecutar los gates;
la suite completa conserva las pruebas del adaptador XGBoost real.

Desde la raíz del repositorio:

```sh
uv lock --check --project pipeline
uv sync --locked --project pipeline
uv run --directory pipeline kedro run --pipelines synthetic
```

El comando único de ejecución es la última línea. `--directory pipeline` cambia
el directorio para que Kedro encuentre su `pyproject.toml`; `--project pipeline`
por sí solo selecciona el entorno de uv y no cambia el directorio del proceso.
El entorno vive en `pipeline/.venv/` y no altera las dependencias de API o tablero.
Se usa la opción vigente `--pipelines` de Kedro 1.7.0. Persisten avisos internos
de deprecación de OmegaConf.

Validaciones desde la raíz:

```sh
uv run --directory pipeline ruff check .
uv run --directory pipeline pytest
```

El fixture genera valores 2, 4, 6, 8 y 10 para 2020–2024. Ajusta la constante 5
sobre las primeras cuatro observaciones y comprueba la última: una observación,
MAE 5 y MSE 25. Esas métricas sintéticas se muestran en consola. El catálogo usa
solo `MemoryDataset`; nada se publica ni persiste. La configuración de logging
solo escribe a consola y `.telemetry` desactiva la telemetría de Kedro.

La instalación necesita acceso al índice de paquetes; la ejecución del smoke test
no usa red ni lee archivos reales del repositorio. Las comprobaciones del fixture
son independientes de los controles temporales de preparación.

No hay campeón ni modelo operativo aprobado; el tracking remoto y DVC permanecen
fuera del alcance. La fábrica implementa únicamente `xgboost_onset/v1` para las
recetas cerradas de T16/T17. La publicación local explícita se implementó en
tarea 14. Los límites están en [la arquitectura](../docs/architecture/pipeline-e2e.md).

## Adquisición de entradas científicas

`acquisition/contracts.py` define `ReleaseManifest`, `ReleaseFile`, `DataSource`,
`ResolvedFile` y `ResolvedBundle`, con dataclasses inmutables y un Protocol.
`create_source` es el único punto que selecciona proveedor; `resolve_release`
coordina la caché sin conocerlo. El servicio se puede usar desde un nodo Kedro;
pytest comprueba esa integración con archivos temporales. No se registra un
pipeline `acquisition` que dependa de un release real todavía inexistente.

Preparación, entrenamiento y evaluación reciben **solo ResolvedBundle**:
identificador del release, digest del manifiesto, cobertura declarada y una tupla
de archivos con nombre lógico, ruta local absoluta, tamaño y SHA-256. No contiene
URLs, proveedor, clientes o credenciales. La disposición local se normaliza;
la normalización científica de los contenidos corresponde a tareas posteriores.

El manifiesto es un objeto JSON estricto con estos campos obligatorios:

| Campo | Contenido |
| --- | --- |
| `schema_version` | Entero `1`. |
| `release_id` | Identificador inmutable, simple y apto para directorios. |
| `provider` | `local`, `huggingface`, `zenodo` o `s3`. |
| `location` | Directorio local, repo_id de dataset, ID de registro Zenodo o bucket. |
| `revision` | Revisión explícita según la tabla de proveedores inferior. |
| `coverage_start`, `coverage_end` | Fechas ISO ordenadas; los fixtures cubren 2018–2024. |
| `files` | Lista no vacía de objetos con `logical_name`, `remote_path`, `relative_path`, `size_bytes` y `sha256`. |

Los hashes de archivos son SHA-256 hexadecimales en minúsculas calculados sobre
sus bytes; los tamaños son enteros no negativos. Se rechazan campos desconocidos,
nombres o destinos duplicados, conflictos archivo/directorio, rutas absolutas,
`..`, rutas ambiguas y escapes por symlinks. La cobertura es una declaración,
no una inspección temporal de las filas: la política científica completa sigue
en la tarea 7. Ningún ejemplo ni fixture de adquisición usa 2025.

El digest del manifiesto usa SHA-256 sobre JSON UTF-8 con claves ordenadas,
`ensure_ascii=False` y separadores `(',', ':')`. Se conserva el orden de los
archivos declarado en el release. No se versiona un manifiesto público ficticio:
las pruebas construyen JSON temporales con hashes de bytes artificiales.

| Proveedor | Configuración y transferencia |
| --- | --- |
| Local | `location` es el directorio configurado y `remote_path` su ruta relativa. La revisión identifica el snapshot local; los hashes detectan alteraciones. |
| Hugging Face | `location` es el repo_id; `revision` debe ser un commit completo de 40 hexadecimales. El SDK oficial usa `repo_type="dataset"` y una caché temporal. Por defecto `token=False`; `use_env_token=True` habilita únicamente `HF_TOKEN` del entorno, sin login ni token cacheado. |
| Zenodo | `location` y `revision` contienen el mismo ID numérico de registro versionado, no el DOI conceptual. Se verifica `id` frente a `conceptrecid` en la API, con metadatos acotados a 1 MiB; el archivo se lee en bloques de 64 KiB. HTTPS, timeout de 30 segundos y sin seguir redirecciones. |
| S3 simulado | `location` es el bucket; `revision` es el prefijo de release que debe mantenerse inmutable. La clave es `<revision>/<remote_path>`. El cliente `S3Client` se inyecta; no se crea boto3 ni se buscan credenciales. |

Hugging Face y Zenodo públicos no requieren token. Los adaptadores admiten
funciones de descarga o HTTP sustituidas en pruebas. Las excepciones externas se
transforman en errores de adquisición sin propagar URLs firmadas o credenciales.
El proveedor S3 solo se ha probado con un cliente en memoria; no accede a AWS.

## Caché e integración mínima

La caché se recibe como argumento. Desde el directorio `pipeline/`, la ubicación
recomendada es `data/01_raw/releases/`; `pipeline/data/` está ignorado por Git.
La estructura final es `<cache>/<release_id>/<manifest_sha256>/<relative_path>`.
Un hit exige tamaño **y SHA-256**, incluso si el nombre y tamaño no cambiaron.
Una copia corrupta vuelve a materializarse. La transferencia usa un temporal en
el mismo directorio, valida integridad y hace `os.replace`. Al fallar, limpia
temporales y conserva los archivos previos; no borra otros releases. La atomicidad
es por archivo: no se entrega un bundle hasta que todos sus archivos son válidos.
Los valores del contrato son inmutables; esto no bloquea cambios externos en disco.

Ejemplo de consumo desde el subproyecto, cuando el equipo aporte `release.json`
con identificadores y hashes reales (el archivo no se incluye en este paso):

```python
from pathlib import Path
from sat_dengue_pipeline.acquisition import ReleaseManifest, create_source, resolve_release

manifest = ReleaseManifest.from_json(Path("release.json").read_text(encoding="utf-8"))
source = create_source(manifest)
bundle = resolve_release(manifest, Path("data/01_raw/releases"), source)
```

Para S3 se aporta además `s3_client` a la fábrica. Migrar de HF o Zenodo cambia
solo el proveedor, origen y revisión del manifiesto y la configuración del cliente;
se conservan los nombres lógicos, hashes y rutas relativas de las entradas.
El digest del manifiesto cambia y crea una caché independiente. Los nodos
científicos mantienen su interfaz `ResolvedBundle`.

Esta caché contiene **entradas científicas**; no escribe ni valida resultados
publicados en `datos/resultados/`. El publicador de tarea 14 produce su propio
manifiesto SHA-256; no se importan módulos de `app/` ni se reutiliza su sincronizador.

El release crudo privado de HF, su commit inmutable y los cinco tamaños/hashes
aprobados están fijados para la tarea 16. Su adquisición y reproducción real se
registran en `docs/decisions/task16-reproduction.md`; el depósito académico de
Zenodo sigue pendiente. Las suites unitarias usan archivos temporales y bloquean
conexiones reales, DNS y acceso a publicaciones. El manual operativo central fue
cerrado en T19 después de la revisión científica T18.

## Panel canónico y preparación temporal

`canonical_input.canonical_from_bundle(bundle)` recibe el archivo lógico local
`panel` en CSV mensual, comprueba tamaño/SHA-256 y cobertura y devuelve tabla y
esquema. `domain/canonical.py` valida conteos separados, cobertura, días climáticos
y claves; agrega canal H5, rezagos calendario y umbrales históricos al origen.
`predictor_matrix` exige roles exclusivos y una allowlist ordenada. Los códigos
DANE son cadenas de cinco dígitos. Ausencia y cero observado son distintos.

`preparation.prepare_horizon` recibe la tabla, esquema, orígenes explícitos,
horizonte 1/2 y disponibilidad de predictores. Los orígenes se separan de la
historia: observaciones de noviembre/diciembre de 2024 pueden evaluar un origen
de octubre T+2. La compuerta usa claves y calendario antes de leer etiquetas y
rechaza observaciones/orígenes desde 2025 y objetivos desde enero de 2025.
Una configuración más restrictiva puede adelantar ese límite.

Inicio significa no exceso en el mes anterior al objetivo y exceso en el
objetivo; si alguno falta, y es ausente. La elegibilidad de ambos horizontes solo
consulta no exceso observado en T. Se distinguen elegibilidad operativa,
evaluabilidad y completitud de X. `PreparedSet` entrega claves, X e y separados;
no ajusta modelos. Los offsets de disponibilidad son conceptuales: las latencias
operativas reales siguen sin demostrarse.

Ejemplo con una tabla canónica ya obtenida de un bundle autorizado:

```python
from sat_dengue_pipeline.domain.temporal import select_origins
from sat_dengue_pipeline.preparation import PREDICTOR_AVAILABILITY, prepare_horizon

origins = select_origins(table, "2023-01", "2024-12", horizon=2)
controls, labels, prepared, audit = prepare_horizon(
    table, schema, origins, horizon=2, availability=PREDICTOR_AVAILABILITY
)
# prepared.keys, prepared.X y prepared.y están alineados y separados.
```

El grafo `pipelines/preparation.create_pipeline()` expone compuerta y preparación
de ambos horizontes con seis salidas: controles, etiquetas T+1/T+2, auditoría y
conjuntos utilizables separados. Los tests suministran un catálogo en memoria;
no se registra de forma aislada. El registro vigente expone `synthetic`,
`canonical_build`, `canonical_reproducibility`, `deployment_publication`,
`factory_validation`, `experiment_run` y el alias `__default__`.

Procedencia, hashes, adaptaciones y límites en
[la decisión de migración](../docs/decisions/v2-scientific-migration.md).
Las referencias pequeñas se generaron ejecutando funciones puras de V2 fijado
en datos artificiales hasta 2024; los tests normales no acceden a V2. Verificación
optativa de procedencia, fuera de la suite normal:

```sh
uv run --directory pipeline python tools/generate_v2_reference.py \
  --v2 /ruta/local/SAT-Dengue-V2 --verify
uv run --directory pipeline pytest tests/test_onset.py -k sentinel_2025
```

Esta paridad sintética es evidencia de ingeniería, sin reproducción real ni
validación científica. La adquisición privada, reproducción y validación reales
quedaron documentadas en T15–T16; no existe un release público de fuentes crudas.
No se usan datos de 2025; los centinelas contienen solo claves artificiales para
comprobar su rechazo antes del consumidor.

## Arnés rolling-origin

`experiments/rolling.py` recibe `ExperimentData` con claves, X, y nullable y
controles separados. `from_prepared` enlaza el conjunto utilizable de tarea 7;
la disponibilidad de etiquetas es el objetivo más una demora declarada.
`ExperimentSpec(horizon=1)` fija calentamiento 2018 y folds mensuales enero de
2019–noviembre de 2024 (T+2 acaba en octubre). Los objetivos llegan a diciembre
de 2024. La ventana de entrenamiento es expansiva y solo usa etiquetas maduras
estrictamente antes del origen consumidor. No se hace shuffle ni partición aleatoria.

```python
from sat_dengue_pipeline.experiments.rolling import (
    ExperimentSpec, build_folds, calendar_audit, from_prepared, run_rolling,
)

spec = ExperimentSpec(horizon=2, label_delay_months=0)
data = from_prepared(prepared, horizon=2)
folds = build_folds(spec)
audit = calendar_audit(spec)
# predictions, audit = run_rolling(data, spec, factory_de_instancia_nueva)
```

La fuente debe aportar historia utilizable para cada fold: una preparación que
empieza en 2023 requiere configurar un primer origen posterior, no inventar
entrenamiento de 2018. El ejecutor no lee y de validación, no calcula métricas
finales y rechaza claves reservadas antes de crear modelos. Cada fold usa una
instancia nueva. Las pruebas emplean solo un doble determinista.
IDs y digest provienen del protocolo/calendario; las filas se ordenan por claves.

```sh
uv run --directory pipeline pytest tests/test_rolling.py
```

El protocolo histórico de ocho ventanas está `NOT_REPRODUCED`: este arnés mínimo
mensual no afirma paridad ni validación científica real. Procedencia, diferencias
y regla estricta de disponibilidad en
[la decisión temporal](../docs/decisions/temporal-experiments.md).

## Adaptadores de modelos

`models/adapters.py` expone `ModelAdapter`: `spec`, `fitted`, `fit(X, y)` y
`predict_positive(X)`. `AdapterSpec` contiene familia, versión, configuración
JSON canónica y semilla. Un `ModelRegistry` vacío recibe constructores explícitos;
no carga modelos/frameworks implícitos. Cada constructor debe crear una instancia
nueva sin ajustar, con la misma identidad declarada.

```python
from sat_dengue_pipeline.models.adapters import AdapterSpec, ModelRegistry, run_candidate

registry = ModelRegistry()
# registry.register("familia_equipo", "1", constructor_del_adaptador)
candidate = AdapterSpec("familia_equipo", "1", config_json='{}', seed=42)
# predictions, audit = run_candidate(data, spec, candidate, registry)
```

El ejecutor usa el calendario rolling-origin común; protege copias, detecta
mutaciones y comprueba esquema, orden, tipos y probabilidades. La inferencia no
recibe y. La salida separada conserva municipio, origen, objetivo, horizonte,
fold, candidato y probabilidad positiva original. Los modelos no conocen Kedro,
proveedores, calibración, umbrales ni publicación. Configuración y procedencia son
serializables; no se versionan estimadores ajustados.

```sh
uv run --directory pipeline pytest tests/test_adapters.py
```

Los dobles deterministas siguen cubriendo los contratos genéricos. La única
implementación real admitida por la fábrica es `xgboost_onset/v1`; LightGBM, GAM
y otras familias permanecen fuera del alcance, sin paridad atribuida a V2.

## Calibración, umbral y referencias

`experiments/roles.py` define cinco ventanas disjuntas por objetivo:
`train → calibration_fit → calibration_selection → threshold_selection → evaluation`.
Cada transición exige disponibilidad de etiquetas más embargo estrictamente
anterior al primer origen consumidor. Los meses de embargo no se usan para
ajustar. Soporte, claves y 2025 se comprueban antes de cualquier lector de y o fit.

El candidato se ajusta una sola vez. La sigmoide sobre probabilidad original se
ajusta solo en calibration_fit, con scikit-learn 1.7.2. SciPy 1.18.1 aplica los
parámetros congelados mediante expit; ambas versiones están fijadas como en V2.
calibration_selection elige sigmoide solo si mejora Brier más de 1e-12; empates
conservan original. Ambas clases y soporte completo son obligatorios en los roles
de ajuste/selección. No se buscan hiperparámetros ni se refit al evaluar.

threshold_selection opera sobre esa representación congelada. La grilla ordenada
y una cota FAR absoluta son argumentos explícitos, sin defaults científicos.
Se maximiza sensibilidad de inicio bajo la cota, con desempates por menos falsas
alertas, menor FAR y mayor umbral. Sin alertas, FAR permanece ausente. Sin umbral
factible, se rechaza; no existe sustitución manual silenciosa.

```python
from sat_dengue_pipeline.experiments.decisions import ThresholdPolicy
from sat_dengue_pipeline.experiments.procedure import fit_procedure, predict_frozen
from sat_dengue_pipeline.experiments.roles import split_roles

# plan debe declarar las cinco ventanas y el soporte, con disponibilidad válida.
batches = split_roles(data, plan)
# Ejemplo artificial, no política científica aprobada:
policy = ThresholdPolicy(tuple(i / 10 for i in range(11)), max_false_alarm_ratio=1.0)
fitted = fit_procedure(batches, plan, candidate, registry, policy)
receipt = fitted.decisions.to_json()
output = predict_frozen(fitted, batches["evaluation"], expected_digest=fitted.decisions.digest)
```

La salida separa claves, probabilidades originales/seleccionadas y decisiones.
Las referencias comparten todas las claves: prevalencia solo de y_train y
persistencia de no exceso observado, adaptada a “sin nuevo inicio” en la cohorte
elegible. Persistencia es determinista; prevalencia no recibe silenciosamente el
umbral del candidato. y de evaluación no se lee durante ajuste ni inferencia.
La evaluación emparejada implementada después cuenta ausencias y aplica soporte
común a candidato y referencias; esta sección describe solo la etapa de decisión.

```sh
uv run --directory pipeline pytest tests/test_procedure.py
```

JSON/digest congela parámetros y decisiones sin pickle o modelos versionados.
La cota absoluta, grilla fija, soporte mínimo de ingeniería y persistencia de
inicio son adaptaciones explícitas. Bins/gap, utilidad relativa y protocolo exacto
V2 quedan `NOT_REPRODUCED`, detallados en
[la decisión temporal](../docs/decisions/temporal-experiments.md).
El ejemplo artificial no demuestra suficiencia científica ni autoriza alertas.

## Evaluación emparejada e incertidumbre

`evaluation/paired.py` recibe `EvaluationTables`: claves, etiquetas, probabilidades,
decisiones, contexto y estratos en tablas separadas, todas enlazadas uno a uno
por municipio/origen/objetivo/horizonte/fold/candidato. Se exige el digest de
decisiones congeladas. `evaluate_procedure` es el puente que consulta evaluation.y
solo después de verificar freeze e inferencia de tarea 10.

```python
from sat_dengue_pipeline.evaluation.paired import EvaluationConfig, evaluate_procedure

# strata es una tabla de las seis claves más department_code declarado.
report = evaluate_procedure(
    fitted, batches["evaluation"], strata,
    expected_digest=fitted.decisions.digest,
    config=EvaluationConfig(bootstrap_replicates=200, seed=42, min_clusters=5),
)
# report.canonical_json y report.digest son agregados inmutables, sin filas.
```

Se calculan AP no interpolada, AUROC con empates, Brier, sensibilidad de inicio,
FAR, volumen y fracción de alertas. Hay un único soporte de etiquetas conocidas
y contexto válido; ausencias se cuentan, no se imputan. Una predicción ausente
invalida las métricas aplicables de todos los métodos sin reducir el denominador
de inicios. Persistencia no tiene Brier y prevalencia no tiene política de alertas.

Las diferencias emparejadas, vistas global/horizonte/departamento y curvas sobre
grilla predeclarada son descriptivas; las curvas nunca cambian el umbral.
El bootstrap sortea municipios completos con las mismas réplicas para métodos
y referencias. Con pocos municipios no emite límites; conserva réplicas no
evaluables y no las reemplaza. No se declara superioridad ni campeón.

```sh
uv run --directory pipeline pytest tests/test_evaluation.py
```

Definiciones, denominadores, procedencia y límites en
[la decisión de evaluación](../docs/decisions/paired-evaluation.md).
El bootstrap histórico de cuatro ventanas queda `NOT_REPRODUCED`; la muestra
artificial adicional solo prueba ingeniería, sin intervalos científicamente calibrados.

## Tracking local optativo

El grupo `tracking` instala mlflow-skinny 3.17.2 y el soporte SQLite mínimo fijado:
SQLAlchemy 2.0.57, Alembic 1.20.1 y sqlparse 0.6.1. Dev incluye ese grupo para
ejecutar la suite; el runtime sin dev no necesita MLflow:

```sh
uv sync --locked --project pipeline
uv run --directory pipeline pytest tests/test_tracking.py
# Runtime científico/sintético sin SDK de tracking:
uv sync --locked --no-dev --project pipeline
uv run --no-dev --directory pipeline kedro run --pipelines synthetic
# Tracking explícito sin herramientas dev:
uv sync --locked --no-dev --group tracking --project pipeline
```

`LocalTracker` recibe el workspace y `TrackingConfig`; por defecto está apagado,
sin imports SDK o creación de store. Para resultados/recibos ya existentes:

```python
from pathlib import Path
from sat_dengue_pipeline.tracking.local import LocalTracker, TrackingConfig
from sat_dengue_pipeline.tracking.privacy import collect_lineage

repo_root = Path.cwd().parent  # ejemplo ejecutado desde pipeline/
lineage = collect_lineage(
    repo_root, bundle, provider=manifest.provider, spec=candidate,
    protocol_digest=audit["digest"], report=report,
)
tracker = LocalTracker(Path.cwd(), TrackingConfig(enabled=True, store=".tracking/local"))
receipt = tracker.record(report, lineage)
run = tracker.get_run(receipt.run_id)
artifacts = tracker.artifacts(receipt.run_id)
tracker.close()
```

Cuando esos agregados y el linaje se hayan guardado bajo `pipeline/data/`
(ignorado; no se incluyen archivos de entrada ficticios en Git), el comando es:

```sh
uv run --directory pipeline python -m sat_dengue_pipeline.tracking \
  --report data/evaluation/report.json --lineage data/evaluation/lineage.json \
  --enable --store .tracking/local
```

Omitir `--enable` desactiva tracking y no crea almacenamiento. El store configurable
queda bajo `.tracking/<nombre>`, ignorado por Git, con SQLite y artefactos locales.
No inicia servidor ni usa red, S3 o credenciales. Guarda URI lógicas, sin rutas
absolutas/usuarios; su recuperación se realiza con el adaptador explícito y funciona
tras mover el workspace. No se configura la resolución genérica de esas URI en UI
o API fluida. Los opt-outs de telemetría/hints del SDK se activan antes de importarlo.

Una corrida padre por invocación contiene candidato/horizonte/referencias y devuelve
un run_id real; no se añaden jerarquías. Se registran Git/dirty, release/manifiesto/
hashes/proveedor de orquestación, cobertura, configuración/semillas, digests de
protocolo/freeze/definiciones/claves, bootstrap, lock y versiones/entorno/UTC.
Solo se aceptan agregados de métricas, diferencias, estratos, curvas, incertidumbre,
configuración y linaje con inventario SHA-256. Nunca X, y, filas, códigos municipales,
modelos, secretos o rutas. El SDK solo observa: los bytes científicos son idénticos
encendido/apagado. Fallos se propagan y cierran FAILED/KILLED, sin artefactos completos.

No se registra tracking automático ni un pipeline operativo nuevo. El proveedor no
se añade a ResolvedBundle ni a los módulos científicos. Límites, decisiones de SDK,
procedencia y `NOT_REPRODUCED` en
[la decisión de tracking](../docs/decisions/local-mlflow.md). No es validación científica.

## Construcción desde crudos y certificación N=3 (tarea 13)

La entrada científica nueva exige `release_kind: raw_sources` y los cinco archivos,
bytes y SHA-256 aprobados en `plan.md`. Rechaza derivados, matrices, el Excel como
insumo, el clima de columnas seleccionadas y revisiones mutables. Los productores
reciben solo `ResolvedBundle`, sin proveedor, URL o credencial. La ruta anterior
de panel mensual se conserva para contratos históricos; no alimenta estos flujos.

Desde la raíz:

```sh
uv run --directory pipeline kedro run --pipelines canonical_build
uv run --directory pipeline kedro run --pipelines canonical_reproducibility
uv run --directory pipeline pytest tests/test_raw_canonical.py tests/test_raw_reproducibility.py
```

Ambos CLI generan exclusivamente cinco crudos artificiales bajo el workspace
ignorado `pipeline/data/canonical-fixture/`. `conf/base/parameters.yml` declara
`canonical.mode: synthetic`, workspace y tracking. El modo explícito `approved`
consume exclusivamente la caché verificada del manifiesto crudo aprobado; no
descarga desde los nodos científicos.
El fixture tiene dos municipios ficticios, 84 meses y 168 claves; una prueba
separada verifica 1.122 × 163 = 182.886 claves sobre dimensión artificial.

`canonical_build` produce un archivo provisional direccionado por digest.
`canonical_reproducibility` reconstruye desde los crudos en tres procesos e inboxes
nuevos, sin consumir el provisional. Compara esquema, tipos, orden, claves, valores,
nulos y bytes exactos, y libera un solo `certified/<digest>/canonical.json` tras
aprobar N=3. Divergencias o fallos bloquean `certify_then_consume`; ningún modelo
se entrena en estos pipelines. No utilices un provisional como entrada entrenable.

La cuarentena excluye fechas desde enero de 2025 antes de normalizar valores.
Fechas inválidas o ausentes se rechazan, sin fallback a FEC_NOT. Los guards V3
conservan diciembre de 2024 como observación y limitan los orígenes a noviembre
para T+1 y octubre para T+2. Epidemiología usa residencia/eventos separados, sin
deduplicar consecutivos. Clima incompleto permanece nulo y nunca se llena con cero.

Tracking se mantiene opt-in y no cambia la tabla. Para observar una certificación
con el SDK opcional instalado:

```sh
uv run --directory pipeline kedro run --pipelines canonical_reproducibility --params canonical.tracking=true
```

El run guarda únicamente agregados, hashes y linaje, incluido el resultado N=3.
Sin opt-in no abre store ni importa MLflow. Ante un error ejecuta primero
`canonical_build` para localizar el contrato/etapa que falla; no omitas controles
ni reutilices una salida anterior como certificación de la corrida fallida.
La conexión privada, cobertura/formatos y N=3 reales se registran en
[la evidencia de tarea 16](../docs/decisions/task16-reproduction.md).

El manifiesto `conf/releases/approved-raw.json` fija los cinco crudos privados.
Desde la raíz, tras `uv sync --locked --project pipeline` y autenticación explícita:

```sh
uv run --locked --directory pipeline python tools/build_approved_canonical.py
```

El helper usa el intérprete actual, adquiere y solo tras éxito ejecuta
`canonical_build` aprobado en `data/canonical-approved/<execution_id>`, sin
tracking ni credencial HF en el proceso Kedro. El resultado sigue **provisional**;
no certifica N=3, entrena, registra experimentos ni publica resultados.

Los comandos internos de diagnóstico son:

```sh
uv run --locked --directory pipeline python tools/acquire_private_raw.py
uv run --locked --directory pipeline kedro run --pipelines canonical_build --params canonical.mode=approved,canonical.workspace=data/canonical-approved-manual,canonical.tracking=false
```

El adquiridor reutiliza `DataSource`/`ResolvedBundle`, exige privacidad y revisión
fija, y verifica inventario y bytes. Guarda un recibo exclusivo por intento en
`data/acquisition/<execution_id>/receipt.json`, incluso ante fallo de adquisición;
no escribe en evidencia histórica. Sin permisos o espacio para el recibo, falla
con `ReceiptError`; no puede garantizar persistencia ante un filesystem fallido.
No hay opción de destino arbitrario. El preflight Kedro distingue ausencia,
faltantes, adicionales y enlaces; la integridad sigue en el validador existente,
sin reparación automática desde nodos científicos.

[Operación](../docs/operations/pipeline-operations.md#canónico-aprobado) centraliza
secretos por shell, requisitos nativos, recuperación y recursos históricos. La
certificación real cerrada de T16 se consulta como evidencia; no es un paso del
helper ni un diagnóstico rutinario. No reutilice un provisional como certificado.
La preparación posterior mide soporte T+1/T+2 y rechaza cruces de 2025; no elige
candidatos, calendarios de roles o políticas FAR científicas.

## Publicación del despliegue (tarea 14)

El módulo `sat_dengue_pipeline.pipelines.deployment_publication` contiene las
funciones puras migradas del publicador de V3 `32b6d06`. No entrena, modifica
predicciones o selecciona champion. Conserva G5 `NOT_APPROVED` / `NOT_SELECTED`.
Los contratos se verifican con snapshot JSON Schema e invariantes autónomos;
pruebas externas contrastan Pydantic y Zod sin imports de `app/` en producción.

Smoke independiente, desde la raíz:

```sh
uv run --directory pipeline kedro run --pipelines deployment_publication
```

La configuración base usa solo fixtures artificiales y escribe bajo
`pipeline/data/deployment-publication/`: entradas locales, dos resultados para
76 municipios ficticios y manifiesto. No escribe en `datos/resultados/` ni se
ejecuta al solicitar el pipeline predeterminado. Kedro devuelve
`publication_manifest` y `publication_receipt`; solo un recibo `COMMITTED`
confirma que terminó la promoción.

Para entradas ya calculadas, el wrapper conserva sus banderas y defaults.
Ejecutarlo desde la raíz preserva rutas relativas, incluida la omisión del
retroanálisis si no existe:

```sh
uv sync --locked --project pipeline
uv run --project pipeline python scripts/construir_resultados.py \
  --panel RUTA/panel.csv --predicciones RUTA/predictions.csv \
  --comparacion RUTA/comparison.csv --procedimiento ID_CORRIDA \
  --version-datos VERSION_DATOS --salida DIRECTORIO_RESULTADOS
```

Aquí `--project` es intencional: conserva el cwd de la envoltura histórica.
Kedro, pytest y Ruff siguen usando `--directory pipeline` (DEC-007).
`--generado 2024-07-01T12:00:00+00:00` permite repetir bytes; si se omite, solo el
CLI consulta el reloj UTC. `--candidato auto` conserva cobertura/coste en T+1;
`--candidato NOMBRE --justificacion TEXTO` registra el override en el manifiesto
y conserva el aviso histórico. Un empate exacto se resuelve por identificador,
corrección separada y caracterizada en DEC-018. Ninguna selección es aprobación.

Kedro también admite `publication.mode: local`, con configuración explícita de
`inputs` (claves `panel`, `predicciones`, `comparacion`, `retroanalisis` opcional),
`destination`, `generated_at`, `procedure`, `data_version` y, opcionalmente,
`candidate`, `model_version`, `justification`. No conecta releases ni entrenamiento.

La publicación prepara un staging hermano del destino, valida el conjunto y
sus nombres/hashes, conserva backups y reemplaza archivos completos. El
manifiesto queda en `.publication/manifest.json`, fuera del índice de la API.
Ante excepciones se restaura lo anterior y se eliminan temporales controlados.
Un lock excluye otros publicadores cooperantes. No se garantiza una lectura
aislada de varios archivos ni recuperación automática si falla el filesystem
durante rollback; en ese caso el error conserva la ruta de backups para recuperar.

Para nuevos periodos, reiniciar la API o recargar su repositorio incorpora las
claves al índice. Los reemplazos de periodos existentes respetan el TTL HTTP
configurado; coordinar la publicación con recarga e invalidación/expiración de
caché. La migración no cambia API, tablero, Docker o sincronización S3.

Validación externa de producto (requiere dependencias de API y tablero instaladas):

```sh
uv run --directory pipeline python tools/validate_publication_consumers.py \
  --directory data/deployment-publication/results --directory ../datos/resultados
```

El snapshot/recibo registra el contrato API inicial. Si cambia intencionalmente,
reexportar `DashboardResponse.model_json_schema()`, actualizar su hash fuente y
revalidar invariantes y consumidores. Detalles de equivalencia y límites en
[la decisión de publicación](../docs/decisions/deployment-publication.md).

## Portabilidad (tarea 15 completa)

Los ocho comandos oficiales anteriores siguen siendo la interfaz en todos los
sistemas. Para ejecutarlos secuencialmente y recoger evidencia, desde un árbol
limpio en la raíz:

```text
uv run --directory pipeline python tools/check_portability.py
```

El coordinador añade reportes JUnit y la suite específica; registra OS/CPU,
versiones, commit/árbol/lock, gates, duración, conteos y hashes. Comprueba árbol
limpio antes/después. `pipeline/data/portability/receipt.json` es el único
artefacto para compartir; logs, XML, datos, venv y tracking permanecen ignorados.
El colector recertifica N=3 usando las APIs existentes para recoger sus tres
huellas; no basta con escribir una configuración o imitar variables del SO.

En GitHub se conserva `Pipeline quality` y se añaden los checks inequívocos
`Pipeline portability (Ubuntu)`, `(Windows)` y `(macOS)`. Cada runner instala
Python 3.12 y uv 0.11.19 con caché deshabilitada, sin credenciales de proveedores.
La existencia del workflow no significa que haya sido ejecutado.

Para Colab, después de disponer de un clon de la revisión que contiene el runner,
una celda **solo de código** delega al script reutilizable (sustituir el SHA por
los 40 caracteres del commit revisado):

```python
import runpy
from pathlib import Path
run_colab = runpy.run_path("sat-dengue/pipeline/tools/colab_runner.py")["run_colab"]
receipt = run_colab(Path("sat-dengue"), expected_commit="SHA_COMPLETO_REVISADO")
```

El script se ejecuta desde el kernel anfitrión real de Colab; instala uv fijado y,
si el host no es 3.12, instala Python 3.12 administrado por uv. El entorno científico
es el venv aislado del lock, sin alterar los paquetes científicos del notebook.
Admite un bundle Git incremental revisado mediante `bundle=Path(...)` para validar
commits locales sin push, exige avance fast-forward y verifica el SHA final.
Solo exportar el recibo; no montar Drive ni introducir tokens para los fixtures.

La auditoría, limitaciones y evidencia concreta están en
[portability.md](../docs/decisions/portability.md). Tras el push autorizado hasta
61159d9, la matriz nativa Ubuntu/Windows/macOS terminó correctamente en el run
42424636145; los siete checks del PR están verdes. Recibos de esos runners,
Mac local y Colab real conservados en `docs/evidence/task15/`, con igualdad exacta
del lock y artefactos deterministas. Tarea 15 completa; el estado vigente de tarea 16 está en `plan.md`.
Cualquier publicación adicional requiere autorización acorde al alcance del chat;
no se autorizó merge ni force push.


## Fábrica autorizada de tarea 16

La receta [T16-FACTORY-XGB-S53-v1](../docs/decisions/task16-experiment-specification.md)
se consume desde `conf/base/parameters_experiment.yml`, sin decisiones científicas
ocultas. Incluye XGBoost 3.0.5 CPU/hist/un hilo/semilla 53, 33 predictores
canónicos (36 columnas internas por one-hot fijo), dos modelos independientes y
cinco roles definidos por objetivo. No selecciona campeón ni publica resultados.

```sh
uv run --directory pipeline kedro run --pipelines factory_validation
```

Antes de este comando deben estar verdes lock/sync, Ruff, suite completa,
regresiones API/tablero, contratos y verificaciones de integridad. El recibo local
ignorado `data/factory-validation/preflight-validation.json` identifica código,
lock y configuración de esos gates. La adquisición verifica privacidad y revisión
inmutable usando solo HF_TOKEN del entorno. Los hijos no reciben la credencial,
bloquean red/proveedores y reconstruyen desde las cinco fuentes en directorios
nuevos; no comparten derivados, matrices, modelos, decisiones, resultados o tracking.

Los soportes de los ocho roles productores se comprueban antes del primer ajuste;
evaluación comprueba claves/meses/municipios sin construir y. Ambas predicciones
se congelan antes de construir sus etiquetas, comprobar clases y calcular métricas.
N=3 compara identidades exactas de datos, matrices, modelos JSON completos,
probabilidades, decisiones, métricas, configuración y linaje. No hay cuarto intento.
Un fallo produce evidencia BLOCKED y se detiene sin cambiar parámetros. Los siete
recibos agregados en `docs/evidence/task16/factory-experiment/` se crean de forma
exclusiva; su existencia impide sobrescribirlos o repetir el comando sobre ellos.
No se versionan filas, modelos ni rutas privadas. 2025 conserva el estado
`consumed_retrospective_evidence`. T16 permanece cerrada; T17 reutiliza el motor
sin modificar esa receta ni conceder autorización operativa.

## Administración experimental y capacidades reutilizables

El pipeline separado `experiment_run` ejecuta únicamente recetas registradas y
aprobadas; `experiment_management` valida, registra, transiciona, lista y compara
sin usar MLflow como fuente de verdad. EXP001 y EXP002 son fixtures técnicos
cerrados. Los procedimientos y estados están en el
[manual de la fábrica](../docs/experiments/manual_pipeline.md).

T21 añadió exactamente cuatro skills canónicas bajo `.agents/skills/`:
`sat-dengue-experiment`, `sat-dengue-scientific-review`,
`sat-dengue-verification` y `sat-dengue-recovery`. Su catálogo es la entrada de
descubrimiento; ninguna skill concede aprobación científica, secretos, push,
publicación o merge.
