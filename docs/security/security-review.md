# Revisión de seguridad — tarea 20

Fecha: 2026-11-08. Resultado: **APPROVED_WITH_LIMITATIONS**.
Base documental y funcional: `498583b` (T19); correcciones auditadas:
`0f4fc20c36390d6a9c1705b89eedd9bbcc901cbf` y corrección de transporte
`bb03e65bf8612f4a478f13487467e264bce3c8de`. No quedan hallazgos CRITICAL/HIGH
abiertos dentro de las superficies verificadas. Esto no certifica la configuración
actual de proveedores, un despliegue remoto ni una aprobación humana de merge.

## Alcance y método

Inspección de código, configuración, workflows, Dockerfiles, contratos, historial
Git alcanzable y evidencia agregada; contraste mediante pruebas y hashes.
Se examinaron manifiestos públicos de dependencias mediante OSV el 2026-11-08:
693 combinaciones únicas de ecosistema/nombre/versión después de la corrección,
incluyendo `pipeline/uv.lock`, `app/dashboard/bun.lock`, pins de API y los 29
paquetes de una resolución limpia de sus requirements con Python 3.12.
Solo se enviaron identificadores públicos de paquetes a OSV; ninguna credencial,
ruta local, dato científico o configuración privada. La consulta es puntual,
no un servicio continuo ni una auditoría de código de cada dependencia.

No se solicitó ni utilizó una credencial real de Hugging Face; no se descargaron fuentes privadas ni se abrió
contenido de los objetos crudos históricos. Los nombres/tamaños y alcanzabilidad
Git se comprobaron por metadatos. No se consultaron ACL, sesiones, secretos o
credenciales de Hugging Face, Zenodo, AWS o GitHub. No hubo entrenamiento,
reproducción privada, ejecución remota ni edición de notebooks.

## Activos, clasificación y publicación

| Activo | Clasificación y tratamiento requerido | Comprobación y límite |
|---|---|---|
| Microdatos epidemiológicos | Privados y sensibles; acceso mínimo, nunca publicar completos ni versionar. | Bundle de cinco fuentes en [contrato crudo](../decisions/raw-canonical-build.md); adquisición de fábrica exige privacidad y revisión. ACL actual NOT_VERIFIED. Existe copia histórica exclusivamente local: SEC-05. |
| Clima y DIVIPOLA | Referencia territorial/ambiental; conservar procedencia, derechos y hashes; el bundle científico sigue privado. | Cinco identidades cerradas; Excel auxiliar y clima recortado excluidos. No se presupone permiso de republicación por estar disponibles en origen. |
| Tabla canónica y matrices | Derivados científicos de uso controlado; fuera de Git y de publicación automática. | `pipeline/data/` ignorado; cuarentena temporal y guardias revisados en [T18](../reviews/scientific-review.md). Agregación no garantiza anonimización. |
| Modelos y predicciones | Artefactos restringidos hasta aprobación; no subir modelos ni predicciones por fila a evidencia. | Runner guarda artefactos científicos en workspace ignorado y tracking/evidencia admiten esquemas agregados. No se inventarió contenido privado de workspaces. |
| Métricas agregadas y evidencia experimental | Versionables solo tras minimización: soportes, conteos, hashes, versiones y estados. | Allowlists, tamaño máximo, inventario, firma lógica y ejemplos EXP001/EXP002 artificiales; no equivalen a licencia para publicar cualquier agregado. |
| JSON publicados | Salida pública del tablero, por municipio y mes; minimizar y revisar riesgo de grupos pequeños antes de nuevos releases. | Los 22 archivos actuales se preservan; 24 documentos existentes/artificiales aceptados por ambos consumidores. No contienen microdatos de notificación. |
| Credenciales y configuración local | Secretos fuera de Git, recibos, artefactos y logs. | Variables de entorno, `.env` ignorado, sin valores en guía/evidencia; controles de logs corregidos en SEC-02. |

Cualquier publicación futura necesita revisión humana de finalidad, permisos,
riesgo de reidentificación, resolución territorial/temporal y supresión o
agrupación de celdas pequeñas. La migración de proveedor no autoriza publicar el
release privado. Reutilizar [la guía operativa](../operations/pipeline-operations.md)
y [el manual](../experiments/manual_pipeline.md), sin copiar credenciales a comandos,
notebooks o archivos versionados.

## Fronteras de confianza y amenazas

1. Proveedor privado → adaptador → caché local: sustitución de fuentes,
   referencias mutables, fuga de token, descarga parcial y escape de rutas.
   `acquisition/contracts.py`, `raw_manifest.py`, `sources.py` y `resolver.py`
   fijan manifiesto, revisión, tamaño, SHA-256, paths relativos y temporales.
2. Registro/protocolo/configuración → ejecución Kedro: YAML malicioso,
   experimento no aprobado, symlinks, carreras y alteración de receta.
   La configuración del repositorio sigue siendo código de confianza; no es un
   servicio de ejecución arbitraria de YAML recibido por red.
3. Workspace → evidencia/MLflow: publicación accidental de filas, rutas o
   excepciones; truncado y evidencia incompleta. Allowlists y cierre por inventario
   protegen las rutas previstas, con límites de confianza local en SEC-08.
4. Publicador → `datos/resultados/` → API → tablero: archivos incompletos,
   JSON no conforme, dependencia vulnerable y exposición de detalles internos.
   El publicador usa staging/rollback/manifiesto; API y tablero validan contratos.
5. Git/dependencias/Actions → ejecución: supply chain, scripts de instalación,
   refs locales privadas y credenciales de checkout. El push debe nombrar
   explícitamente la única rama autorizada.

## Matriz de controles

PASS significa observado en código/pruebas; PARTIAL tiene límites explícitos;
NOT_VERIFIED exige comprobación humana o infraestructura fuera del alcance.

| Superficie | Estado | Evidencia concreta y límite |
|---|---|---|
| Release inmutable/neutral | PASS | `acquisition/sources.py`: HF exige commit de 40 hex y verifica `private`/`sha`; Zenodo exige ID de versión, HTTPS y rechaza redirects; S3 científico es adaptador simulado. `test_acquisition.py`, `test_raw_canonical.py`. |
| Descarga/caché | PASS | `resolve_release`: tamaño+SHA-256 por bloques, temporal y `os.replace`, conservación de copia previa. `test_acquisition.py` y pruebas de adquisición de fábrica. Caché en filesystem de confianza, sin promesa de aislamiento frente a otro proceso con igual UID. |
| Privacidad de adquisición | PASS | `acquisition/factory.py:acquire` desactiva logging durante SDK, limita fallo a tipo/estado y desactiva progreso/telemetría HF. No login persistente ni token en manifiesto. No activar trazas manuales del SDK en una sesión con credenciales. |
| Rutas/registro | PASS | `experiment_management/registry.py:confined`, `identifier`, `UniqueLoader`: rechazo de escape, symlinks por componente y claves duplicadas; SafeLoader y esquema cerrado. `test_experiment_management.py`. No sandbox para plugins/código Python hostil. |
| Aprobación y hashes | PASS | `Registry`, runner y `verify_execution`: estados, protocolo/config congelados, conclusiones y firmas verificadas antes de comparar; evidencia previa inmutable. `test_experiment_management.py`. |
| Escritura, locks e integridad | PARTIAL | `registry_lock` reserva con mkdir; `exclusive_json` usa xb/fsync; inventario final marca cierre. Paquete parcial no verifica. SIGKILL, disco lleno y escritor local malicioso siguen en SEC-08; no firma criptográfica de autor. |
| MLflow/evidencia | PASS | `tracking/privacy.py`, `tracking/canonical.py`, `tracking/local.py` validan allowlists y store local, rechazan URI remota/symlinks/artefactos desconocidos. `test_tracking.py`, recibos EXP artificiales preservados. No inspección de stores privados ajenos a esta ejecución. |
| Transporte API S3 | PASS | `almacenamiento.py`: descarga temporal, tamaño+contrato antes de reemplazo; fallo conserva copia local. Excepciones SDK y cadenas del validador ocultas; creación/listado/descarga cubiertos por regresiones. Autenticidad del productor: SEC-09. |
| Logs de API | PASS | `main.py:crear_app` mantiene boto3/botocore/urllib3/s3transfer en WARNING incluso con aplicación DEBUG; siete casos nuevos de transporte/logging y fallback. No prueba de configuración externa de logging. |
| Contrato/API/tablero | PASS | 35 pruebas API, 55 tablero, 24 Pydantic y 24 Zod; validación de JSON, errores controlados, API GET/CORS explícito. SEC-01 conserva aceptación histórica de UUID/fechas/enteros al actualizar Zod. |
| Fronteras científicas | PASS | 541 pruebas pipeline: bloqueo de import inverso, red, DNS y aperturas de datos reales en tests; revisión T18. API requirements sin Kedro ni dependencias científicas; pipeline no escribe en app. |
| Dependencias | PARTIAL | uv lock/sync y Bun frozen aprobados; OSV sin HIGH/CRITICAL pendiente en versiones consultadas; cinco avisos moderados en SEC-04. API fija directas, no transitivas ni hashes de wheels. |
| Workflows | PARTIAL | Cuatro workflows: pull_request/workflow_dispatch, contents:read, checkout persist-credentials:false, sin pull_request_target ni interpolación de título/cuerpo en shell; sin secretos de proveedor. Acciones por tag, no SHA: SEC-06. |
| Contenedores/red | PARTIAL | Dockerfiles API/tablero usan usuario sin privilegios, API sin ciencia. Nginx expone HTTP; TLS/firewall/IAM actuales NOT_VERIFIED (SEC-07). Imágenes base por tag (SEC-06). No Docker build ni despliegue remoto en esta revisión. |
| Historial/repositorio | PARTIAL | 781 blobs históricos alcanzables al iniciar la inspección, búsqueda de patrones de token HF/GitHub/AWS, claves privadas y asignaciones literales: sin candidatos. Ruta absoluta detectada solo en fixture de rechazo `test_tracking.py`. Copia cruda local excluida de lectura: SEC-05. Escáner por patrones no garantiza ausencia universal de secretos. |
| Preservación/portabilidad | PASS | 49 hashes de baseline, 16 recibos anteriores, 22 JSON y N=3 intactos; snapshot extendido de 68 archivos incluye EXP001/EXP002. Checkout autocrlf artificial demuestra LF en archivos de identidad y CRLF en control; CI nativa del nuevo HEAD debe confirmarlo. |
| Proveedores y gobierno remoto | NOT_VERIFIED | No acceso a privacidad actual, IAM, ownership, cifrado, audit logs, secretos ni reglas remotas. Revisión humana, ruleset y checks obligatorios siguen siendo condiciones anteriores al merge. |

Las rutas de módulos/pruebas anteriores son relativas a
[`pipeline/src/sat_dengue_pipeline/`](../../pipeline/src/sat_dengue_pipeline/)
y [`pipeline/tests/`](../../pipeline/tests/), salvo las rutas API/tablero explícitas.

## Hallazgos por severidad

### Corregidos

| ID | Severidad | Hallazgo, corrección y validación |
|---|---|---|
| SEC-01 | HIGH, resuelto | Zod 3.25.76 y copias 4.6.5 afectadas por agotamiento de memoria al validar colecciones sobredimensionadas. Se fija Zod 4.6.6 y override transitivo; no se agrega otra dependencia. Uso de colecciones V4 corregidas, con reglas explícitas que conservan aceptación JSON anterior de UUID, timestamp y enteros. 21 casos de compatibilidad y un caso con getters prueban rechazo previo a leer elementos de los dos horizontes. Comparación acotada: V3 procesa tres elementos pese a length(2), V4 cero. Cinco regresiones de compatibilidad fallaban con actualización sin adaptación. No cambia ningún dato ni regla científica. [Aviso](https://github.com/advisories/GHSA-mrhx-c7xc-m3w5), [corrección del mantenedor](https://github.com/colinhacks/zod/commit/a0ebf970f2d752e5f58527cd2942ff48be4f46bd). |
| SEC-02 | MEDIUM, resuelto | Excepciones arbitrarias del SDK S3 podían alcanzar logs/tracebacks y el cliente se construía fuera del bloque protegido. Ahora se oculta mensaje/cadena externa, se conserva diagnóstico interno de tamaño/contrato y se acota logging HTTP. Regresiones con marcador artificial fallaban en creación/listado/descarga; ahora pasan y mantienen fallback/atomicidad. No se observó una credencial expuesta. |
| SEC-03 | MEDIUM, resuelto localmente | autocrlf alteraba documentos de protocolo y rompía las identidades en Windows (fallo remoto previo de T17). `.gitattributes` fuerza LF en protocolos, evidencia, especificación T16 y JSON; no se renormaliza ni modifica evidencia histórica, no se relaja ningún hash. Regresión de checkout roja → verde. La primera CI (42451673280) eliminó los fallos por hashes y expuso referencias internas con separador Windows y una conclusión de prueba con encoding implícito. `bb03e65` usa as_posix al generar referencias/claves de identidad (mantiene guards de entrada) y UTF-8 explícito en fixtures. Cuatro regresiones controladas de rutas rojas → verdes y conclusión bajo CP1252 verde; confirmación nativa completa pendiente del segundo push. |

### Riesgo residual admitido con seguimiento

| ID | Severidad | Riesgo, mitigación actual, responsable y condición |
|---|---|---|
| SEC-04 | MEDIUM | Cinco avisos moderados en tres dependencias: detalle abajo. Responsable: mantenedor del tablero. Evaluar parches compatibles en un cambio dedicado; obligatorio antes de habilitar servidor de mocks accesible, patrones RegExp/typed arrays controlados por usuario o globs externos. No se declaran falsos positivos ni versiones libres de vulnerabilidades. |
| SEC-05 | MEDIUM | Una rama local antigua de respaldo conserva seis blobs crudos/auxiliares; tres superan 5 MB (máximo 875.694.283 bytes). Son metadatos de historia preexistente; cero objetos crudos alcanzables desde HEAD, origin/main y origin/feature/pipeline-e2e. El HEAD inspeccionado no contiene archivos >5 MB (máximo 300.050 bytes). Mantener esa copia bajo controles de datos privados y nunca usar push --all/--mirror. Responsable: propietario del equipo/repositorio; decidir retención o saneamiento local con autorización específica. No se borra ni reescribe ninguna referencia. No hay evidencia de publicación de esos objetos por las ramas verificadas; no se auditó cada ref remoto ajeno. |
| SEC-06 | MEDIUM | Acciones e imágenes base fijadas por tags mutables y API con resolución transitiva sin lock/hashes. Mitigación: permisos read-only, checkout sin credencial persistente, pins directos y lock científico/Bun; la resolución API actual también fue consultada en OSV. Responsable: mantenedor de CI/despliegue; fijar SHA/digests y resolver lock API antes de ejecución privilegiada o nuevo proceso de releases. No cambia permisos ni reglas en esta tarea. |
| SEC-07 | MEDIUM | Controles de proveedor y perímetro no verificados. Responsable: dueño de datos e infraestructura. Antes de migrar/desplegar: comprobar acceso privado real, ownership de bucket, bloqueo público, IAM mínimo/roles efímeros, MFA administrativa, cifrado en tránsito/reposo y claves, versionado/retención, logs de acceso/auditoría y TLS/firewall. Ninguna credencial o microdato debe atravesar HTTP. HF es origen privado normativo, Zenodo copia académica futura y S3 científico simulado; que la API ya pueda sincronizar resultados S3 no implementa esa migración científica. |
| SEC-08 | LOW | Hashes/locks locales no resisten un escritor hostil con igual permiso; posible carrera entre comprobación de symlink y apertura, lock abandonado o paquete parcial por terminación abrupta. Mantener checkout/workspace bajo un único operador confiable, inspeccionar inventario antes de consumir y conservar fallos. Responsable: operador; ante SIGKILL/disco lleno/corrida incompleta, investigar antes de liberar lock o repetir; si se requiere multiusuario no confiable, diseñar aislamiento/firma fuera de este alcance. |
| SEC-09 | LOW | La API valida tamaño y esquema de S3; no verifica el manifiesto SHA firmado del productor. Un productor con permiso de escritura puede sustituir un resultado válido. Mitigación: consumidor read-only y control humano de publicación; responsable: publicador/infraestructura. Antes de dar acceso de escritura a terceros o promover un nuevo release, exigir procedencia autenticada, permisos separados y política de integridad. No se cambia contrato público. |

Detalle de SEC-04 (severidad conservadora de la base de avisos):

| Paquete fijado | Avisos y condición de explotación | Mitigación observada |
|---|---|---|
| @vitest/mocker 4.1.11 | [registro de mocks](https://github.com/advisories/GHSA-qxg6-89mg-rqv8), [traversal Windows](https://github.com/advisories/GHSA-xp26-3454-mjgp); corregidos en 4.1.12. | Tests usan `vitest run`/jsdom, sin browser mode ni servidor de mocks publicado. No exponer watch/dev a redes no confiables. |
| seroval 1.6.8 | [RegExp dentro de script](https://github.com/advisories/GHSA-9wx9-5pv9-3349), [constructor de typed array](https://github.com/advisories/GHSA-f86p-h4j2-7qgj); corregidos en 1.6.10/1.6.11. | El tablero consume JSON validado; no construye RegExp desde entrada externa ni copia propiedades externas sobre typed arrays para SSR. Reexaminar cualquier nuevo uso de serialización. |
| minimatch 10.2.6 | [amplificación de globParts](https://github.com/advisories/GHSA-g3hv-75wg-m249); corregido en 11.0.1 (major). | Globs de herramientas/build de repositorio confiable; no endpoint que reciba patrones glob. Actualizar tras verificar compatibilidad, sin override major indiscriminado. |

## Validación, límites y cierre

- Gate acumulado: lock/sync/Ruff PASS; pipeline **541** pruebas (seis avisos
  OmegaConf existentes); API **35** (aviso deprecación TestClient); tablero
  **55**, Bun frozen, lint y build node_server PASS.
- `experiment_management validate` VALID; preservación **49/49**, incluyendo
  22 JSON y 16 recibos previos, y snapshot extendido **68/68**. Identidad N=3:
  `899ba8b2c48b69dbf2e9094a6efedfa838cbfe4c800bed25fa1823503d06d52f`.
- Pydantic y Zod aceptan **24 documentos cada uno** (22 publicados y dos
  artificiales). Fixtures sin ciencia nueva; no reemplazan validación operativa.
- Cuatro regresiones adicionales de referencias/identidad POSIX y conclusión artificial
  con locale CP1252 controlado PASS; no se atribuye ese control a Windows nativo.
- Cuatro workflows y Dockerfiles inspeccionados; pruebas pipeline bloquean red
  y DNS. Hubo red únicamente para metadatos públicos de paquetes/avisos y GitHub;
  no se afirma que builds/instalaciones normales sean offline o sin scripts.
- Escaneo de candidatos sensible limitado por patrones y contexto; no cubre
  secretos ofuscados, logs externos, configuración local ignorada ni todos los
  refs de terceros. No se imprimieron valores candidatos.
- SHA/estado del código y conteos permiten revisar el resultado sin almacenar
  logs completos, rutas personales, microdatos, modelos o predicciones por fila.

El [recibo determinista](../evidence/task20/security-review.json) registra el
cierre local. Los checks del nuevo HEAD se verificarán tras el push normal al
PR #1; su resultado remoto debe consultarse por SHA, sin atribuirle los checks
de 00c5404. No hacer merge: revisión humana, ruleset y checks requeridos siguen
pendientes como condiciones de merge. T21 permanece PENDIENTE.
