# Arquitectura del pipeline E2E y transición a V3

Estado: decisiones adoptadas para la implementación incremental. Fecha: 2026-11-08.
Actualizada hasta T21; el producto desplegado y la evidencia cerrada se conservan.

## Fuente oficial y situación actual

**V3 es este repositorio, `sramirezc2/sat-dengue-despliegue`, y será la única
fuente oficial del proyecto**, incluyendo el futuro trabajo científico.
`SAT-Dengue-V2` queda como antecedente y procedencia histórica; no será una
segunda fuente activa. La migración debe conservar la trazabilidad de sus artefactos.

La distribución observada es compatible con una integración aditiva:

| Ruta actual | Responsabilidad observada |
| --- | --- |
| `app/api/` | API de solo lectura; valida y sirve JSON persistidos, sin inferencia en línea. |
| `app/dashboard/` | Producto que consume el contrato HTTP de la API. |
| `datos/resultados/` | JSON publicados por departamento y mes, incluidos resultados de evaluación de 2025. |
| `datos/retro/` | Evidencia de retroanálisis que el generador incorpora a los resultados. |
| `scripts/construir_resultados.py` | Envoltura compatible; la lógica de publicación reside en `pipeline/.../deployment_publication/`. |
| `docker/`, `scripts/` | Despliegue con Compose, proxy y operación de la instancia. |
| `docs/`, `modelos/`, `notebooks/` | Documentación, referencias de artefactos y material histórico; se conservan. |

`pipeline/` ya contiene Kedro, adquisición neutral, dominio canónico, controles
temporales, arnés experimental, evaluación y tracking local opt-in. La API permite sincronizar resultados desde S3
a su directorio local mediante `SATD_BUCKET_S3`; esto transporta resultados
publicados, no adquiere datos científicos ni ejecuta entrenamiento.

## Estructura objetivo y límites

```text
app/                 producto desplegado existente
pipeline/            proyecto Kedro autocontenido
datos/datos-crudos/  entrada local privada, ignorada por Git
datos/resultados/    único contrato entre pipeline y API
docker/              despliegue existente
scripts/             operación y envolturas temporales
docs/                arquitectura, decisiones y evidencia
.agents/skills/       cuatro capacidades canónicas de operación y revisión
```

Esta estructura expresa responsabilidades principales; no elimina las demás
carpetas existentes. `docs/architecture/` contiene este documento central;
`docs/decisions/` queda reservado para decisiones futuras que lo justifiquen,
sin duplicar aquí las reglas en múltiples ADR.

La única dirección permitida de entrega y consumo es:

```text
pipeline/ → datos/resultados/ → app/api/ → app/dashboard/
```

Las flechas representan el flujo de artefactos y respuestas. En código, la API
nunca importará Kedro ni módulos de `pipeline/`; el pipeline tampoco importará
`app/` ni escribirá dentro de ella. El tablero consumirá la API, sin acceder al
pipeline o a sus archivos internos.

`pipeline/` tendrá configuración, catálogo y dependencias propias. Las
dependencias científicas y Kedro no se instalarán en la imagen de la API.
Cada responsabilidad tendrá un dueño: adquisición y normalización, dominio
científico, y publicación. Se aplicarán DRY, SOLID e inversión de dependencias
mediante interfaces pequeñas; se evitarán implementaciones duplicadas y capas
sin necesidad. El Python futuro usará tipado y docstrings estilo Google.

## Contrato de publicación: `datos/resultados/`

Es la única frontera entre el cálculo científico y el servicio. No se publican
bundles de entrenamiento, modelos ni dependencias ejecutables en esta frontera.
Se conserva la convención `resultado_<departamento>_<AAAA-MM>.json` y el esquema
vigente `DashboardResponse`, definido en
[`schemas.py`](../../app/api/sat_api/contrato/schemas.py). El consumidor actual es
[`RepositorioDirectorio`](../../app/api/sat_api/repositorio.py).

El nombre debe corresponder al departamento y al mes de referencia del contenido
(`department.department_code`, `department.requested_period` y
`metadata.reference_period`). Se conservan metadatos de identidad, fechas y
versión de datos, resultados municipales, contexto de evaluación y gobernanza;
no se inventa un esquema paralelo. La publicación futura deberá validar el
contrato antes de exponer archivos completos y evitar lecturas parciales.
La estrategia de actualización coherente del índice y la caché se verificará
al implementar la publicación, sin cambiarla en este paso.

`SATD_DIRECTORIO_RESULTADOS` permite ubicar esta frontera en otro entorno;
Compose la monta en `/datos/resultados`. Un transporte remoto puede replicar
estos mismos artefactos sin crear una interfaz alternativa al pipeline.
`datos/retro/ventana_expansiva.json` sigue siendo una entrada del generador;
su contenido llega al consumidor incorporado en los JSON publicados, no por
una segunda dependencia de la API.

Los resultados históricos y sus estados `G5 = NOT_APPROVED` y
`champion_status = NOT_SELECTED` se preservan. Incorporar el pipeline no autoriza
un modelo ni modifica la política científica vigente.

La tarea 14 incorpora `deployment_publication`, fuera del pipeline predeterminado.
Consume entradas locales ya calculadas, construye documentos con fecha inyectada,
valida un snapshot JSON Schema derivado y las invariantes del producto, y prepara
staging fuera del destino. Solo tras validar el conjunto promueve mediante
reemplazos atómicos por archivo, backups y rollback ante excepciones. El
manifiesto SHA-256 vive en `.publication/manifest.json`; los nombres consumidos
por la API permanecen iguales. Las pruebas externas usan los contratos Pydantic
y Zod reales; el código productivo no importa consumidores.

Los nuevos periodos requieren recargar el índice del repositorio o reiniciar la
API; los reemplazos están sujetos al TTL HTTP existente. No se cambia ese
comportamiento ni se promete aislamiento multiarchivo frente a lectores activos.
Procedimiento, límites y equivalencia en
[la decisión de publicación](../decisions/deployment-publication.md).

## Adquisición desacoplada y almacenamiento

Hugging Face distribuirá exclusivamente las cinco fuentes crudas mediante un
release privado fijado por revisión y hashes. Zenodo podrá conservar releases
académicos aprobados. La interfaz `DataSource`
encapsulará adquisición con adaptadores intercambiables para archivos locales,
Hugging Face, Zenodo y, posteriormente, AWS S3 o almacenamiento compatible.

DEC-021 precisa que el repositorio remoto puede conservar
`Listados_DIVIPOLA.xlsx` como auxiliar: la adquisición selectiva lo ignora y el
bundle científico de Kedro contiene únicamente las cinco fuentes aprobadas.
El Excel no interviene en construcción canónica ni aprendizaje. El release
autorizado y la evidencia de privacidad se registran en
[la documentación de tarea 16](../decisions/task16-reproduction.md).

Cada adaptador entrega un `ResolvedBundle` de archivos crudos locales verificados.
Desde esa frontera, normalización, entrenamiento y evaluación no conocen el
proveedor, sus clientes, URLs ni credenciales. La selección del adaptador será
configuración de adquisición, no una condición dentro del dominio científico.
El contrato `release_kind: raw_sources` exige el inventario cerrado de cinco
archivos, bytes y SHA-256 de la sección 4.1 de `plan.md`. Se rechazan derivados,
features, matrices, `google_earth_engine-selected-columns.csv`, el Excel como
insumo y revisiones mutables (`main`, `latest`). DIVIPOLA es el JSON aprobado en
`Divipola-municipios.md` acompañado de su procedencia. El clima exige 18 columnas.
`datos/datos-crudos/` es entrada local, nunca publicación; el inbox remoto y el
trabajo local permanecen bajo `pipeline/data/`, ignorado por Git.

La extensión hacia AWS sustituirá el adaptador y su configuración, manteniendo
el bundle y el contrato publicado. El S3 de adquisición será una responsabilidad
distinta de la sincronización de resultados ya existente en la API.
AWS Academy seguirá siendo un entorno de laboratorio, **nunca almacenamiento
definitivo**. No se presupone un bucket permanente ni se agregan credenciales.
DVC queda fuera de esta implementación. La nube no entrega tablas canónicas.

## Construcción y certificación canónica

Los nodos delgados de Kedro y funciones de dominio siguen este orden:
`raw_contract_validation` → `raw_temporal_projection` →
`raw_temporal_quarantine` → `geography_normalization` →
`epidemiology_normalization` → `climate_daily_normalization` →
`climate_monthly_aggregation` → `canonical_sources` → `canonical_panel` →
`canonical_validation` → `canonical_serialization`.

La proyección lee solo territorio/fecha; la cuarentena separa registros desde
`2025-01` antes de normalizar o agregar valores. Solo se registran conteos y
digests. Epidemiología mantiene eventos 210/220 separados, usa residencia e
`INI_SIN`, sin fallback a `FEC_NOT` ni deduplicación por `CONSECUTIVE`. Los
descartes se reconcilian por causa. Clima produce cuatro sumas y cinco medias;
los meses incompletos quedan nulos, nunca se rellenan con cero.

La dimensión aprobada tiene 1.122 municipios; la cuadrícula de desarrollo abarca
163 meses (`2011-06`–`2024-12`), 182.886 claves únicas. Los joins declaran
cardinalidad y conservan conteos y ausencias. Se reutiliza `domain/canonical.py`
para canal, lags y predictores; `TemporalPolicy` y `guard_development` son las
únicas autoridades temporales. T+1 admite orígenes hasta noviembre de 2024;
T+2 hasta octubre. La serialización determinista incluye esquema, tipos, orden,
claves, valores y nulos, digest semántico y SHA-256; usa temporal y rename atómico.

Kedro expone `canonical_build` y `canonical_reproducibility`. Este último
reconstruye N=3 en procesos y directorios aislados desde los crudos, sin compartir
derivados. Cualquier diferencia bloquea al consumidor de entrenamiento; únicamente
se libera una salida certificada. Las pruebas usan un perfil sintético explícito
de menor tamaño, sin atribuirle los hashes ni la certificación del release real.
La conexión y reproducción del release privado corresponden a la tarea 16.

El observador local existente recibe solo agregados: manifiesto/hashes crudos,
Git SHA, configuración y lock, cuarentena, cobertura, conteos/rechazos, digest
canónico y las tres huellas con el resultado N=3. El linaje mínimo vincula
`raw_manifest_digest + builder_git_sha + builder_config_digest + lock_digest`
con `canonical_semantic_digest`; no contiene filas ni rutas privadas.

## Validación de fábrica de tarea 16

La especificación V3 [T16-FACTORY-XGB-S53-v1](../decisions/task16-experiment-specification.md)
autoriza `factory_validation`: adquisición privada fijada de cinco fuentes,
construcción canónica nueva, cinco roles por objetivo, dos XGBoost CPU/hist
independientes, calibración, umbrales y evaluación diferida. Kedro consume
`pipeline/conf/base/parameters_experiment.yml`; las pruebas exigen conformidad
exacta con el documento normativo. No hay búsqueda, refit, G, presupuesto del
canal, campeón ni habilitación operativa.

Cada uno de tres procesos secuenciales usa inbox, derivados y tracking nuevos.
La certificación previa canónica permanece aprobada; esta nueva certificación
compara toda la fábrica, incluido JSON completo de modelos. Los ocho soportes
productores y las claves de evaluación pasan antes del primer ajuste. Las etiquetas
de evaluación se construyen después de congelar y predecir ambos horizontes.
Un gate fallido o divergencia detiene el procedimiento sin otra receta ni cuarta
corrida. Solo se emiten agregados/huellas, preservando la evidencia existente.

## Tratamiento de 2025

El bundle crudo puede incluir 2025; su cuarentena ocurre antes de cualquier
normalización, agregación, join, imputación o ajuste. Los datos de 2025 son
**evaluación previamente utilizada y evidencia consumida**.
No entrarán al desarrollo: entrenamiento, selección de variables o candidatos,
ajuste de hiperparámetros, calibración o elección de umbrales y criterios.
Tampoco se presentarán como holdout intacto ni como nueva confirmación.
Los resultados históricos pueden seguir publicados con su procedencia y
limitaciones. La futura preparación del bundle deberá separar y verificar las
particiones por fecha objetivo, incluyendo horizontes que crucen de 2024 a 2025,
para impedir filtraciones. Una evaluación confirmatoria requerirá una cohorte
independiente que no haya intervenido en las decisiones de desarrollo.
Esto concuerda con la advertencia de evidencia consumida de la
[propuesta de política v2](../politica-de-decision-v2.md), que sigue siendo propuesta.

## Secuencia incremental y alcance protegido

Toda la implementación se acumulará en `feature/pipeline-e2e` y terminará en
**un único Pull Request**. La siguiente secuencia registra la orientación inicial
de la transición; no representa el estado vigente de tareas:

1. Formalizar estos límites y registrar un commit local de documentación.
2. Crear el proyecto Kedro independiente y definir el bundle y `DataSource`.
3. Incorporar adquisición local/Hugging Face y acceso a versiones de Zenodo,
   con normalización, procedencia y separación temporal verificables.
4. Integrar entrenamiento y evaluación sobre el bundle, sin acceso al proveedor.
5. Migrar gradualmente la lógica de `scripts/construir_resultados.py` hacia la
   publicación del pipeline, comprobando equivalencia contractual antes de
   sustituirla; conservar temporalmente una envoltura si hace falta.
6. Verificar el flujo E2E y la compatibilidad con el despliegue; añadir el
   transporte S3 de adquisición cuando exista una necesidad concreta, sin DVC.

Hasta T21 se implementaron y validaron adquisición, canónico, preparación,
evaluación, publicación, fábrica reproducible, administración experimental,
revisiones, operación y cuatro skills. DEC-027 amplía la secuencia a 27 tareas:
T22–T24 son correcciones operativas y validación local; la anterior T22 pasa a T25.
T26–T27 reservan publicación/CI y auditoría final para autorización posterior.
Los estados y el alcance autorizado se consultan exclusivamente en `plan.md`.

En las primeras etapas se preservaron rutas, configuración y comportamiento de
API, tablero, Docker y operación. No se mueven ni renombran `app/`, `docker/`,
`datos/` o `scripts/`; el generador actual no se elimina ni se cambia en este paso.
La prohibición de editar celdas Markdown de notebooks sin autorización formal
continúa vigente. La CI, código y dependencias incorporados por tareas posteriores
se rigen por sus decisiones y evidencia; este texto histórico no los invalida.

## Diferencias de transición y riesgos

- El generador y la evidencia conservan referencias a V2 como procedencia
  histórica. V3 es la fuente activa única; esas referencias no crean una segunda
  autoridad ni deben reescribirse dentro de evidencia cerrada.
- El S3 existente no contradice que Hugging Face sea la fuente operativa inicial:
  sirve resultados terminados. Confundir ambos usos acoplaría el servicio al dominio.
- Cambios de proveedor o revisiones mutables pueden romper la reproducibilidad:
  se exige procedencia versionada e integridad del bundle.
- Reutilizar 2025 o filtrar etiquetas de horizontes cruzados invalidaría la
  evaluación; las particiones deberán comprobarse antes de desarrollar modelos.
- Divergencias del esquema o publicación parcial pueden romper el tablero:
  se conservará el contrato y se verificará la equivalencia antes de migrar.
- Copiar lógica del generador a la vez que se mantiene otra implementación
  produciría deriva; la migración será gradual con una única implementación final.
- El almacenamiento de Academy es transitorio; su continuidad no puede ser
  condición para recuperar datos o reproducir resultados académicos.

No hay incompatibilidad estructural que exija cambiar el producto en este paso.

## Administración multi-experimento (T17)

`experiment_management/` resuelve el registro versionado de
`docs/experiments/registry.yml` y configuraciones independientes de
`pipeline/conf/experiments/`. El pipeline `experiment_run` valida aprobación,
rutas, hashes y allowlist antes de adquirir; comparte las etapas científicas de
`factory.engine` sin invocar ni flexibilizar el validador cerrado de T16.
La extensión del adaptador admite un subconjunto declarado de predictores y el
motor admite uno o ambos horizontes, conservando el comportamiento de T16.

Una reserva exclusiva por ejecución precede al estado RUNNING. Evidencia agregada
append-only e inventario verificable viven en `docs/evidence/experiments/`; el
registro no permite COMPLETED sin conclusiones estructuradas enlazadas a evidencia
íntegra. MLflow extiende el store SQLite local existente con padre/hijos solo por
comparaciones efectivas. El CLI de comparación lee registro y agregados, nunca
microdatos o MLflow. T16 queda fuera del índice científico y se conserva cerrada.
Procedimiento, contratos y límites en [experimentos](../experiments/README.md).

## Capacidades reutilizables (T21)

Las únicas skills del repositorio viven en `.agents/skills/` y se descubren desde
el [catálogo](../agents/skills-catalog.md): operación del ciclo experimental,
revisión científica, selección/ejecución de gates y recuperación conservadora.
Todas delegan en las autoridades versionadas existentes y fallan cerradas ante
aprobaciones, secretos, publicación, push o merge. No se añadieron agentes,
plugins, hooks ni una segunda implementación de comandos o reglas científicas.
