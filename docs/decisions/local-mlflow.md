# Tracking local de agregados

La tarea 12 observa resultados ya calculados. Ningún módulo científico importa
MLflow; el adaptador recibe `EvaluationReport` inmutable y un recibo de linaje
separado. No ejecuta folds, modelos, calibración, selección, métricas o campeón.
Tracking apagado y encendido conservan exactamente los bytes/digests científicos.

## Dependencia y backend

Se seleccionó `mlflow-skinny==3.17.2`, versión del SDK correspondiente al MLflow
histórico fijado. El paquete completo no es necesario: no se usan UI, servidores,
registro de modelos o flavors. Skinny por sí solo no incluye soporte SQL; se
agregan sus tres dependencias oficiales de backend: `sqlalchemy==2.0.57`,
`alembic==1.20.1`, `sqlparse==0.6.1`. SQLAlchemy se fija en la serie 2.0 compatible
con el store probado, evitando el loader obsoleto de la serie 2.1 en este SDK.
Las transitivas quedan fijadas en uv.lock, incluidas dependencias del SDK como
Databricks, OpenTelemetry y FastAPI; no se activan servicios, exportadores o clientes
remotos. Ninguna dependencia de tracking se incorpora a la API desplegada.

Fuentes oficiales: [distribución skinny](https://pypi.org/project/mlflow-skinny/3.17.2/)
y [arquitectura de tracking](https://mlflow.org/docs/latest/self-hosting/architecture/tracking-server/).
La instalación y operación del backend se prueban realmente, también desde
checkout limpio. `tracking` es un grupo opcional incluido en dev para ejecutar
la suite completa; `uv sync --locked --no-dev` conserva el runtime científico
y el E2E sintético sin SDK MLflow.

`LocalTracker(workspace, TrackingConfig(...))` recibe configuración explícita,
con opt-in desactivado por defecto. El store debe estar bajo `.tracking/<nombre>`
dentro del workspace, ignorado por Git, sin symlinks o escapes. No usa HOME,
credenciales, servidores, S3 ni red. No utiliza API fluida, autologging, singleton
de aplicación, hooks automáticos o selección global de tracking URI.

El SDK normaliza URI locales estándar a rutas absolutas. Para evitar persistir
rutas privadas se usan explícitamente `SqlAlchemyStore` y `LocalArtifactRepository`
del SDK, con URI lógica `satdlocal:/artifacts` en metadatos. La ubicación física
se resuelve solo dentro del adaptador configurado. No se registra un plugin ni
se modifica el registry global de repositorios. La conexión SQLite utiliza una
ruta operacional interna que no se registra como parámetro, tag o artefacto.
Incluso el experimento Default queda sin rutas privadas. Los tests inspeccionan
el dump SQLite y todos los artefactos y recuperan el store después de moverlo.

Estos puntos de extensión del SDK están fijados y cubiertos por pruebas de
compatibilidad; una actualización necesita repetirlas. Los artefactos se consultan
con `LocalTracker.artifacts(run_id)`, no mediante resolución genérica de la URI
lógica en UI/API fluida. No se implementa compatibilidad de UI o backend remoto.
Los opt-outs del SDK `MLFLOW_DISABLE_TELEMETRY=true` y
`MLFLOW_DISABLE_AGENT_HINT=1` se fijan explícitamente antes de importarlo y permanecen
activos para el proceso; no determinan parámetros científicos o almacenamiento.

## Corridas, linaje y artefactos

Cada invocación registra una corrida padre real en el experimento declarado.
Un reporte ya corresponde a un candidato/horizonte y sus referencias; no se
añaden hijas sin aportar una comparación adicional. Cada repetición crea otro
run_id; no hay deduplicación implícita. El recibo separado contiene experimento,
run_id real, parent_run_id nulo, estado, tracking_enabled y artifact_digest.
No se insertan IDs de MLflow en X, y o registros de métricas científicas.

`collect_lineage` captura Git SHA y dirty reales, release/manifiesto/hashes de
entrada, cobertura, semilla, horizonte, candidato/configuración, digest de protocolo,
freeze, definiciones y claves, bootstrap, Python, sistema/máquina, SHA-256 del lock,
versiones científicas/SDK y UTC. El proveedor procede exclusivamente del recibo de
orquestación; `ResolvedBundle` no cambia. Sus rutas locales nunca se proyectan.
Un dirty registrado es una limitación de reproducibilidad, no se oculta ni implica
que Git SHA por sí solo identifique todo el código no confirmado.

Las allowlists de parámetros/tags, estructuras y valores son estrictas. Se
rechazan campos desconocidos, tokens, credenciales, URI, rutas, usuarios explícitos
y códigos individuales. Los nombres lógicos de entradas deben ser alias simples
de letras/guiones bajos, sin números o identificadores territoriales. No se
capturan argv, variables de entorno, usuario de sistema o filas científicas.
MLflow user_id queda vacío. El proveedor es solo metadato, nunca una dependencia
del cálculo científico.

Solo se almacenan metrics.json, comparisons.json, strata.json, curves.json,
uncertainty.json, configuration.json, lineage.json e inventory.json. Son agregados;
no se registran réplicas detalladas, X, y, predicciones individuales o modelos.
Cada archivo se limita a 512 KB y se verifica con SHA-256. artifact_digest identifica
el conjunto científico agregado/configuración; inventory.json añade también la
huella del linaje particular de la corrida (UTC y run_id), sin autorreferencia.
Por ello los agregados/digest científico se mantienen entre repeticiones aunque
run_id y linaje temporal sean diferentes.

El ciclo es RUNNING → FINISHED. Cualquier excepción se propaga y cierra FAILED;
interrupciones cierran KILLED. Los archivos se preparan en temporal, se publican
por rename y se eliminan si falla el cierre, incluso después del rename. No se
modifican resultados científicos ni quedan artefactos completos de una corrida
fallida. Tracking habilitado nunca oculta fallos. Deshabilitado no importa el SDK
ni crea store y devuelve DISABLED.

## Procedencia histórica y exclusiones

Fuente: `j-mauro-r/SAT-Dengue-V2@916a69f3bb73f2ffbb0ec038b8bef887ee91adf1`,
blobs consultados solo con git show; sin imports o escrituras V2:

| Archivo | SHA-256 | Regla y adaptación/exclusión |
|---|---|---|
| `src/sat_dengue/tracking/local.py` | `d7a796f56efd883a309b89a0e1b88c939a192883c2f0ecce65c1775cdd72d21d` | Allowlists, local opt-in y estados terminales. V3 usa store/repositorio explícitos, una corrida, sin hooks o registry global. |
| `src/sat_dengue/tracking/lineage.py` | `a119b6f89c85ba082506747d9cd7a6e2c6f9918d9ce6bb3c5c2bdbeaded0d86f` | Proyección de hashes/versiones/agregados; V3 recibe recibos ya calculados, sin abrir bundles históricos/publicaciones. |
| `src/sat_dengue/tracking/artifacts.py` | `42eee4e827fe55fda894dd9636098688ee469e6c1180d1bb137cce6ee268b63e` | URI lógicas para privacidad y artefactos cerrados. V3 no instala el plugin global histórico; usa instancia del repositorio SDK y recuperación explícita. |
| `tests/integration/test_mlflow_tracking.py` | `47403abd672afc64d394bc5c9da67842a98ecd95807d129fc732c670899272ec` | Corridas reales, privacidad, igualdad científica, fail/kill y SDK desactivado; adaptado a agregados V3/SQLite temporal bajo guard de red. |
| `docs/product/experiments/experiment-registry.yml` | `8f34f1dda012e2c20ea2d5919c7aa38d1b7f892165086cf5dc04265ec1be6f28` | Contexto de registro científico explícito; no se copian EXP históricos, hipótesis, aprobaciones o resultados a V3. |

`NOT_REPRODUCED`: jerarquías/hook Kedro y deduplicación históricas, registro
EXP00/01/02/03/031, payloads/replay privados, modelos nativos, aprobaciones y
evaluación científica de 2025. No se afirma paridad de corridas con V2.
Tracking solo aporta trazabilidad de ingeniería. Release real, revisión científica,
seguridad completa, CI remota/ruleset y único PR permanecen pendientes. Una futura
migración remota deberá sustituir el adaptador y su política de privacidad sin
modificar ciencia; no basta cambiar la URI local, que rechaza destinos remotos.
