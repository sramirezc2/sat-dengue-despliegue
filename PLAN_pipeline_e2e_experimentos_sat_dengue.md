# Plan de diseño v7: Pipeline E2E de experimentación para SAT DENGUE

**Plan interno:** `PLAN_pipeline_e2e_experimentos_sat_dengue`

**Versión de diseño:** 7.2 — correcciones operativas previas al merge

**Fase actual:** diseño aprobado en ejecución sobre `feature/pipeline-e2e`; `plan.md`
es la única fuente de verdad sobre número, estado, dependencia y avance de las tareas

**Nivel de rigor:** deep
**Razón:** combina migración entre repositorios, datos científicos versionados,
experimentación temporal, prevención de fuga, ejecución multiplataforma, artefactos
pesados, gobernanza de champion y protección obligatoria mediante PR.

## 1. Objetivo

Convertir
[`sramirezc2/sat-dengue-despliegue`](https://github.com/sramirezc2/sat-dengue-despliegue)
en la única fuente de verdad del producto y de su experimentación, de modo que una
persona del equipo pueda:

1. clonar el repositorio;
2. resolver desde un manifiesto una versión inmutable de las fuentes crudas o dejar
   un bundle crudo válido en la carpeta de entrada;
3. ejecutar un único comando lógico;
4. obtener de corrido validación, construcción de la tabla canónica, preparación,
   entrenamiento, calibración, evaluación, comparación con líneas base,
   trazabilidad y artefactos publicables;
5. reproducir el experimento sin pedir archivos a otro integrante ni ejecutar
   notebooks o scripts personales intermedios.

La solución debe funcionar en macOS, Windows y Google Colab. Todo cambio al
repositorio definitivo debe entrar por pull request y superar validaciones
automáticas. La adquisición será un componente reemplazable: inicialmente usará
Hugging Face como distribución operativa y Zenodo como archivo académico, pero
ninguna etapa científica conocerá esos proveedores. Una migración futura a AWS,
R2 u otra fuente deberá limitarse a configuración, credenciales y un adaptador que
cumpla el mismo contrato. La implementación científica vivirá íntegramente bajo
`pipeline/`; `app/` conservará la API y el tablero existentes, y
`datos/resultados/` será el único contrato de publicación entre ambos dominios.

## 2. Evidencia examinada y diagnóstico

La propuesta se basa en una revisión de:

- V3/despliegue en `main@1302152310a68812bc4d7e89166ef3e9978619b5`;
- V2/científico en `main@916a69f3bb73f2ffbb0ec038b8bef887ee91adf1`;
- el código Kedro, catálogos, pruebas y contratos científicos de V2;
- la bitácora experimental, la política de decisión y el publicador del tablero
  de V3.

Hallazgos que condicionan el diseño:

1. **Al iniciar el plan, V3 no contenía el pipeline científico.** La ejecución de
   esta hoja de ruta ya creó `pipeline/`; `plan.md` y los commits de la rama son la
   evidencia vigente de qué capacidades están implementadas.
2. **V2 ya usa Kedro**, pero su comando E2E oficial es un `replay`: verifica
   artefactos guardados y prohíbe ajustes reales. No satisface el objetivo de
   preparar, entrenar y evaluar nuevos enfoques.
3. **El avance sobre inicios está documentado, pero no es reproducible desde
   V3.** La propia bitácora indica que los scripts de las tandas son material
   personal no publicado y que el banco 2018–2024 es un arnés experimental, no
   el pipeline oficial. El `.gitignore` de V3 excluye `experimentos/`.
4. **Los 1,6 GB de datos y varios artefactos necesarios no tienen una cadena de
   descarga común.** V2 conserva snapshots privados/locales y manifiestos, pero
   reconoce que no existe recuperación universal de todas las fuentes.
5. **2025 ya fue consumido.** V2 y V3 registran que el bloque se utilizó en la
   evaluación congelada G5. Puede y debe excluirse de nuevos ajustes, pero no se
   puede presentar científicamente como un holdout virgen.
6. **`main` no está protegido actualmente** y no existen workflows versionados
   en V3, aunque la regla del equipo exige PR.
7. **Hay código valioso para reutilizar**, especialmente contratos temporales,
   etiquetas de inicio, prevención de fuga, familias de modelos, evaluación y
   pruebas. Debe migrarse selectivamente con trazabilidad, no incorporar V2 como
   dependencia de ejecución.
8. **El release agregado no requiere licencia ni autorización adicional.** Esta
   decisión humana queda registrada como `not_required`; aun así, el manifiesto
   conserva fuentes, atribución, procedencia, hashes y clasificación. Los archivos
   epidemiológicos completos no se versionarán en Git ni se harán públicos; su
   distribución inicial será privada y restringida al equipo.
9. **El release publicado anteriormente en Hugging Face contiene derivados.** Por
   decisión del equipo, deja de ser una entrada válida del E2E. La nube contendrá
   únicamente fuentes crudas aprobadas; Kedro será responsable de construir la
   tabla canónica utilizada por entrenamiento.
10. **La migración completada en la tarea 6 no cubre todavía la ingestión cruda.**
    V3 ya valida y enriquece un panel mensual estructurado mediante
    `domain/canonical.py`, pero faltan los productores modulares que normalizan,
    agregan y unen las fuentes crudas reales. La paridad sintética previa se
    conserva como evidencia, no como certificación del nuevo E2E real.
11. **El inventario crudo de ejecución ya fue identificado y verificado
    localmente.** Los snapshots epidemiológicos y DIVIPOLA coinciden byte a byte
    con las identidades fijadas por V2. El archivo climático completo de 18
    columnas también coincide con V2; reemplaza de forma definitiva al recorte
    `google_earth_engine-selected-columns.csv`, que no puede producir las nueve
    variables climáticas exigidas por el contrato canónico de V3.
12. **La carpeta local autorizada es `datos/datos-crudos/`.** Está ignorada por
    Git y funciona únicamente como entrada del adaptador local. Nunca debe
    confundirse con `datos/resultados/`, que continúa reservado para la frontera
    de publicación consumida por API y tablero.

## 3. Decisiones de arquitectura propuestas

### D1. Monorepo V3 con subproyectos y dependencias dirigidas

V3 será la única fuente de verdad, pero no mezclará responsabilidades. Alojará:

- `pipeline/`: proyecto Kedro autocontenido para adquisición, preparación,
  entrenamiento, evaluación y publicación;
- `app/api/`: API de solo lectura existente;
- `app/dashboard/`: tablero existente.

La dependencia será estrictamente unidireccional:

```text
pipeline/ -> datos/resultados/ -> app/api/ -> app/dashboard/
```

La API no importará Kedro ni código del pipeline; el pipeline no escribirá dentro
de `app/`; el tablero solo hablará con la API. Las dependencias Python pesadas del
pipeline quedarán en `pipeline/pyproject.toml` y `pipeline/uv.lock`, separadas de
`app/api/requirements.txt`. El Docker Compose existente seguirá desplegando solo
API, tablero y proxy; la corrida canónica científica tendrá su propia definición
en `pipeline/docker/`.

V2 queda como referencia histórica congelada. V3 no hará imports, submodules ni
instalaciones desde V2. Cada componente reutilizado se migrará mediante PR con un
manifiesto que registre ruta y commit de origen, cambios realizados y pruebas de
equivalencia.

### D2. Kedro orquesta; las funciones de dominio calculan

Kedro será el grafo E2E y el catálogo de datasets. Los nodos deben ser delgados;
la lógica científica vivirá en funciones Python puras, testeables sin levantar una
sesión Kedro. Los notebooks serán solo vistas exploratorias o lanzadores y nunca
la fuente de una transformación.

Pipelines modulares propuestos:

1. `data_acquisition`
2. `raw_data_validation`
3. `raw_temporal_quarantine`
4. `canonical_sources`
5. `canonical_panel`
6. `canonical_reproducibility`
7. `feature_engineering`
8. `temporal_splits`
9. `candidate_training`
10. `calibration_and_thresholds`
11. `candidate_evaluation`
12. `model_comparison`
13. `experiment_reporting`
14. `deployment_publication`

Estos nombres describen etapas lógicas del diseño, no el registro CLI vigente.
Hasta T21, `pipeline_registry.py` registra `synthetic`, `canonical_build`,
`canonical_reproducibility`, `deployment_publication`, `factory_validation`,
`experiment_run` y el alias `__default__`; las funciones de dominio componen esas
entradas sin exponer cada etapa como pipeline independiente.

`data_acquisition` será la única frontera que conoce proveedores externos. Usará
un puerto `DataSource` y adaptadores intercambiables que materializan un bundle
local verificado:

```text
LocalDataSource
HuggingFaceDataSource   # fuente operativa inicial
ZenodoDataSource        # archivo y fallback inicial
S3DataSource            # contrato listo para una migración futura a AWS/R2
```

Todos los adaptadores reciben un descriptor de release y devuelven el mismo
`ResolvedBundle` (`local_path`, `release_id`, archivos, tamaños y SHA-256). Desde
`raw_data_validation` en adelante solo se aceptan rutas y contratos locales; quedan
prohibidos imports de SDK de Hugging Face, Zenodo o AWS. Agregar o cambiar una
fuente no puede alterar features, particiones, modelos, métricas ni publicación.

El contrato científico exigirá `release_kind: raw_sources`. Un bundle que incluya
una tabla canónica, features o matrices listas para entrenamiento será rechazado
como entrada del E2E, aunque sus hashes sean válidos. La tabla canónica será un
artefacto derivado local, direccionado por contenido y siempre reconstruible desde
el manifiesto crudo, el código, la configuración y el lock.

Composiciones propuestas en el diseño inicial:

- `experiment`: adquisición cruda → validación → cuarentena → construcción
  canónica → preparación → entrenamiento → evaluación → reporte, solo con datos
  de desarrollo;
- `experiment_synthetic`: el mismo grafo con un bundle pequeño generado;
- `canonical_build`: construye una tabla canónica sin entrenar modelos;
- `canonical_reproducibility`: ejecuta `canonical_build` N veces en espacios
  aislados y certifica igualdad antes de liberar una salida;
- `publish`: transforma una corrida aprobada al contrato de la API/tablero;
- `final_validation`: grafo separado y bloqueado, sin acceso desde `experiment`.

### D3. Una sola CLI estable y multiplataforma

Comando lógico propuesto originalmente (no implementado como ejecutable `satd`):

```text
uv run --frozen --project pipeline satd experiment run \
  --spec pipeline/conf/experiments/EXP-YYYY-NNN-slug.yml
```

Las interfaces vigentes son Kedro para ejecutar y el módulo de administración
para gobernar el registro:

```text
uv run --directory pipeline kedro run --pipeline experiment_run --params experiment_id=EXP003
uv run --directory pipeline python -m sat_dengue_pipeline.experiment_management validate
```

La CLI Python hará en orden:

1. resolver el ambiente bloqueado;
2. cargar el manifiesto de release aprobado y seleccionar el adaptador por
   configuración;
3. localizar el bundle en caché o ejecutar `data_acquisition` para materializarlo;
4. verificar tamaños, SHA-256, contratos crudos, procedencia y cobertura temporal;
5. ejecutar la cuarentena de las fuentes crudas mediante sus claves temporales;
6. normalizar, agregar y unir las fuentes para construir la tabla canónica;
7. validar esquema, claves, tipos, ausencias, cobertura y digest semántico de la
   tabla canónica;
8. aplicar el guard temporal existente de V3 antes de cualquier consumidor que
   pueda aprender, consultar etiquetas o ajustar transformaciones;
9. generar el `run_id` a partir de Git SHA + configuración + versión de datos;
10. ejecutar el resto de `kedro run --pipeline=experiment`;
11. validar el paquete de resultados y escribir el resumen final.

`pipeline/uv.lock`, `pipeline/.python-version` y `pipeline/pyproject.toml` serán
autoridades versionadas.
`uv` ofrece lock universal y Python administrado en macOS, Windows y Linux. En
Colab se usará la misma CLI; el notebook de Colab será una envoltura mínima, sin
lógica científica.

No se usará `Makefile` como interfaz obligatoria porque no es nativo en Windows.
Docker será el entorno de la corrida canónica, no un requisito para explorar ni
para Colab.

### D4. El manifiesto identifica datos; Kedro orquesta; MLflow registra corridas

Las responsabilidades no se mezclarán:

| Capa | Responsabilidad |
|---|---|
| Git/GitHub | código, contratos, configuración, decisiones y revisión por PR |
| Manifiesto de release crudo | identidad lógica, fuentes, procedencia, periodos, granularidad, tamaños y SHA-256 |
| Hugging Face | distribución cotidiana exclusiva de fuentes crudas mediante revisión inmutable y acceso individual |
| Zenodo | preservación y DOI de releases académicos estables; fallback de descarga |
| Adaptadores `DataSource` | autenticación, descarga, caché y materialización local |
| Kedro | construcción canónica, dependencias y ejecución del grafo de datos/ML |
| Registro Git | identidad, estado, protocolo, configuración, conclusiones y evidencia agregada de cada experimento |
| MLflow local | índice operativo de corridas padre/hijas, parámetros, métricas, tags y linaje; no es la única fuente de verdad |
| JSON/Parquet de publicación | contrato estable que consume la API/tablero |

La primera implementación no incorporará DVC: Kedro será el único grafo y los
datasets derivados se conservarán localmente o se regenerarán. Solo podrán
registrarse fuera del equipo hashes, esquemas, métricas y reportes pequeños que no
permitan sustituir la construcción. MLflow no será fuente de verdad de datos ni
decidirá automáticamente el champion.

### D5. Hugging Face operativo, Zenodo archivístico y portabilidad de proveedor

La fuente operativa inicial será un nuevo release de Hugging Face que contenga
exclusivamente las fuentes crudas necesarias para construir el panel canónico. Su
identificador, inventario, commit inmutable y hashes deben fijarse antes de la
reproducción real; `main`, `latest` y URLs mutables no son identificadores válidos
para una corrida. Cada integrante accederá con su propia cuenta y token de lectura
configurado fuera de Git, sin depender de que otra persona encienda una máquina,
entregue archivos o autorice cada ejecución.

El primer release crudo tendrá exactamente estos cinco insumos de ejecución:

| Nombre lógico | Archivo físico | Bytes | SHA-256 | Uso |
|---|---|---:|---|---|
| `divipola_catalog` | `Divipola-municipios.md` | 209.867 | `72eabcea0ff26370d23b9688e8d8f2246946cc815c040ccf1a6966b37a1de9f3` | catálogo nacional de 1.122 municipios |
| `divipola_provenance` | `divipola-provenance.json` | 925 | `92091306f0130910f27de999776b5cf4ed36b7dd7c89bd724d58caeb74f8c158` | identidad y procedencia territorial |
| `dengue_notifications` | `dengue.csv` | 875.694.283 | `58d277cfef7a60c28d488eefe4e7a1a7bf0f7b0df3dd88245971cd7b3d32c84b` | notificaciones del evento 210 |
| `severe_dengue_notifications` | `dengue_grave.csv` | 24.537.734 | `3d60e96ccbedc35a19a8f5f54be8d786aa599813259c914f131522bf17dd1d70` | notificaciones del evento 220 |
| `daily_climate` | `google_earth_engine.csv` | 1.714.544.311 | `dfe20fa02b6d6068c04744b5c86f44112048400a7fde637368c0d4effc88cb3f` | clima diario nacional con 18 columnas |

`Listados_DIVIPOLA.xlsx` no es una entrada de ejecución. Puede conservarse fuera
del bundle como evidencia humana, pero no será descargado, leído ni usado como
segunda autoridad territorial. El recorte
`google_earth_engine-selected-columns.csv` queda explícitamente prohibido porque
solo contiene lluvia y no satisface el contrato de nueve variables climáticas.

La regla “solo datos crudos en la nube” aplica a la capa de datos científicos de
entrada. No elimina los JSON pequeños que el producto ya publica bajo el contrato
`datos/resultados/`, pero prohíbe usar almacenamiento remoto para sustituir la
construcción canónica de Kedro.

En este plan, “crudo” significa entrada anterior a la armonización y construcción
canónica. Los dos CSV epidemiológicos conservan granularidad individual y campos
sensibles; por tanto, el release que contenga los archivos completos debe ser
privado, con acceso individual de solo lectura y sin URLs públicas. La confirmación
de que licencia y autorización son `not_required` no elimina esta clasificación de
privacidad. Hacer público un release epidemiológico requeriría otro manifiesto,
minimización irreversible de columnas y una revisión de seguridad explícita; no
está autorizado por este plan.

El dataset `sat-dengue/sat-dengue-v3-through-2025-v1` y su commit
`f07f1cc5bd02c8d1f4a260f0d92ee85ca16ad484` quedan **retirados como entradas del
E2E** porque contienen la tabla canónica y otros derivados. No se usarán como
fuente primaria, fallback ni mecanismo de caché. Podrán conservarse fuera del
camino de ejecución como evidencia histórica, pero ninguna corrida nueva podrá
leer `canonical_model_table_national_v4.csv`, `temporal_roles.csv` u otro artefacto
de ese release.

El nuevo release crudo puede cubrir hasta diciembre de 2025. No se crearán copias
físicas separadas para desarrollo y 2025: Kedro aplicará la cuarentena por claves
temporales antes de agregar o unir fuentes y construirá únicamente la vista
canónica autorizada para desarrollo. Los releases crudos estables podrán
depositarse además en Zenodo y recibir un DOI de versión. Cuando exista esa copia,
debe contener los mismos archivos crudos y SHA-256.

```text
GitHub: pipeline/manifests/data_releases/<release_id>.yml
├── operational_source: Hugging Face + commit
├── archive_source: Zenodo + DOI/version, cuando aplique
├── release_kind: raw_sources
├── files: fuente cruda + granularidad + claves + tamaño + SHA-256
├── clasificación, procedencia y decisiones `license/authorization: not_required`
└── cobertura temporal y contrato de construcción canónica
```

Política inicial:

- la operación inicial admite el dataset privado con acceso individual de los
  cuatro integrantes y sin intermediación humana;
- los archivos epidemiológicos completos no tendrán descarga anónima; solo un
  futuro release minimizado y aprobado podrá considerar visibilidad pública;
- solo los publicadores autorizados podrán crear una nueva revisión o release;
- ningún secreto de publicación se guardará en Git;
- Zenodo se usará para hitos académicos, no para cada cambio provisional;
- la nube no almacenará tablas canónicas, features, particiones, matrices de
  entrenamiento, modelos ni predicciones como entradas del E2E;
- un futuro holdout intacto no heredará automáticamente la política pública;
- 2025 se conserva dentro del release como `consumed_retrospective_evidence`,
  nunca como holdout virgen ni como dato apto para aprendizaje.

La fuente de verdad lógica es el manifiesto revisado por PR, no el nombre de un
proveedor. Migrar a AWS requerirá implementar o habilitar `S3DataSource`, publicar
los mismos archivos crudos bajo rutas inmutables, actualizar el manifiesto mediante PR y
superar el conjunto común de pruebas contractuales. No requerirá cambiar el
catálogo científico ni los pipelines posteriores.

AWS Academy puede utilizarse para pruebas o cómputo temporal, nunca como única
copia. Si el equipo migra a AWS, la opción durable será una cuenta AWS ordinaria
del proyecto o de la universidad con S3, identidades individuales y credenciales
temporales. Cloudflare R2 puede implementar el mismo adaptador S3-compatible.

Google Drive no se recomienda como fuente primaria: su integración requiere OAuth
interactivo por integrante y está sujeta a cuotas. No será parte del camino
operativo inicial.

### D6. Contrato único del bundle de entrada

La entrada local manual y la caché resuelta por adquisición son responsabilidades
distintas:

```text
datos/datos-crudos/                         # staging local ignorado por Git
├── Divipola-municipios.md
├── divipola-provenance.json
├── dengue.csv
├── dengue_grave.csv
└── google_earth_engine.csv

pipeline/data/01_raw/inbox/<data_release>/
├── manifest.yml
├── epidemiology/
├── climate/
├── geography/
└── reference/
```

`LocalDataSource` podrá resolver los cinco archivos desde
`datos/datos-crudos/`; Hugging Face, Zenodo o S3 materializarán exactamente el
mismo `ResolvedBundle` bajo `pipeline/data/01_raw/inbox/`. Desde ese punto las
etapas científicas no conocerán la ruta de origen ni el proveedor.

El release tendrá un manifiesto pequeño versionado en Git y una copia dentro del
bundle. Debe declarar como mínimo:

- `schema_version`, `data_release` y `release_kind: raw_sources`;
- fuente operativa con proveedor, repositorio y revisión inmutable;
- fuente archivística con DOI/version de Zenodo, cuando exista;
- propietario, clasificación, procedencia y fecha de extracción;
- `license_requirement: not_required` y
  `authorization_requirement: not_required`, conforme a la decisión del equipo;
- periodo mínimo/máximo y geografía;
- archivos, tamaños y SHA-256;
- claves de negocio y temporales, granularidad y unidad de cada fuente cruda;
- contrato de normalización y productor canónico responsable de cada campo;
- regla de ausencia frente a cero observado;
- sensibilidad del dato y política de redistribución;
- cobertura temporal real de cada fuente y política para derivar roles por fila;
  el release completo no recibe un único rol metodológico;
- roles permitidos: `development` hasta objetivo `2024-12` y
  `consumed_retrospective_evidence` para 2025;
- orden de fuentes de fallback y política de caché.

El manifiesto no declarará como entradas `canonical_model_table_*`, features,
matrices X/y, particiones temporales, modelos o predicciones. Si alguno aparece en
un bundle crudo, la validación falla antes de construir el panel. La lista de cinco
archivos es cerrada: un archivo científico adicional, ausente, renombrado o con un
hash diferente detiene la corrida. Los CSV originales se conservan como bytes de
entrada; Parquet puede usarse únicamente para artefactos derivados locales.

El proveedor resuelto, la revisión/DOI y los hashes crudos realmente leídos quedan
registrados en cada corrida. La caché puede reutilizar los bytes crudos ya
verificados, pero nunca una salida canónica cuya identidad de constructor no
coincida.

### D7. Cuarentena temporal explícita y reutilización del guard de V3

El pipeline `experiment` aceptará como máximo objetivos hasta `2024-12`, aunque un
bundle crudo pueda llegar hasta `2025-12`. La adquisición puede descargar y
verificar los bytes completos, pero 2025 no puede entrar a agregaciones canónicas
de desarrollo, preparación, imputación aprendida, escalado, selección de variables,
HPO, ajuste, calibración, selección de umbral ni selección de champion.

Las protecciones serán redundantes y se ejecutarán en este orden:

1. `data_acquisition` materializa y verifica el bundle crudo completo sin
   interpretarlo como una matriz de aprendizaje.
2. Un adaptador temporal por tipo de fuente proyecta únicamente sus claves y las
   lleva a un contrato común municipio-periodo, sin calcular features ni etiquetas.
   Para epidemiología usa `INI_SIN` como fecha y
   `COD_DPTO_R + COD_MUN_R` como residencia; para clima usa `date` y
   `mpio_cdpmp`. DIVIPOLA es una referencia territorial sin rol temporal.
3. La cuarentena, usando `TemporalPolicy.reserved_start` como única frontera,
   separa las filas desde `2025-01`, registra conteo y digest y no las entrega a
   los productores canónicos de desarrollo.
4. Los módulos epidemiológico, climático, geográfico y de referencia normalizan
   sus fuentes aisladas; un nodo de integración construye el panel municipio-mes y
   `domain/canonical.py` añade los predictores derivados.
5. La salida canónica se ordena, valida y limita a objetivos como máximo
   `2024-12`; los roles se calculan dentro de Kedro y nunca se descargan.
6. Antes de construir etiquetas o llamar a cualquier consumidor aprendido, Kedro
   reutiliza `TemporalPolicy` y `guard_development` de
   `pipeline/src/sat_dengue_pipeline/domain/temporal.py`. No se creará un guard
   paralelo ni una segunda definición de la frontera.
7. `guard_development` falla de forma cerrada si una observación, origen u objetivo
   alcanza `2025-01`, si el calendario declarado fue alterado o si un horizonte
   cruza el límite. Por ejemplo, origen `2024-12` para T+1 y origen `2024-11` para
   T+2 deben rechazarse porque su objetivo es `2025-01`.
8. Pruebas centinela demuestran que el rechazo ocurre antes de leer etiquetas o
   invocar entrenamiento, calibración, HPO, umbrales o evaluación.
9. MLflow registra release crudo, commit, hashes, digest canónico, rangos por rol,
   conteos y digest de cuarentena; no registra valores ni etiquetas científicas de
   2025 como insumos del experimento.

El patrón aprovecha las lecciones de SAT-Dengue V2, pero la autoridad de ejecución
es el guard ya migrado y probado en V3. Cualquier cambio futuro a la política debe
modificar esa única implementación y sus pruebas. Como 2025 ya fue consumido, solo
puede utilizarse en un flujo descriptivo separado y explícito; una validación final
realmente independiente requiere un periodo posterior aún no utilizado.

### D8. Construcción canónica modular, determinista y certificable N veces

La tabla de entrenamiento no será descargada ni construida por un script monolítico.
`canonical_build` compondrá módulos con contratos explícitos:

1. `raw_contract_validation`: valida la lista cerrada, bytes, SHA-256, encabezados
   y estructura de los cinco insumos;
2. `raw_temporal_projection`: proyecta solo claves territoriales y temporales;
3. `raw_temporal_quarantine`: separa desde `2025-01` antes de cualquier productor;
4. `geography_normalization`: construye una única dimensión DIVIPOLA;
5. `epidemiology_normalization`: clasifica y agrega por residencia e `INI_SIN`;
6. `climate_daily_normalization`: valida códigos, fechas, numéricos y unicidad
   municipio-día;
7. `climate_monthly_aggregation`: calcula las nueve variables mensuales y su
   cobertura diaria;
8. `canonical_sources`: crea la cuadrícula municipio-mes y une conteos, clima y
   geografía con cardinalidad declarada;
9. `canonical_panel`: reutiliza las funciones de dominio de V3 para canal,
   rezagos, H5, roles y esquema;
10. `canonical_validation`: valida columnas, tipos, claves, orden, nulos, rangos,
    conservación de conteos y frontera temporal;
11. `canonical_serialization`: genera una salida local estable y un manifiesto
    derivado direccionado por contenido;
12. `canonical_reproducibility`: reconstruye N veces y certifica igualdad antes
    de liberar una única salida al experimento.

#### D8.1. Normalización territorial

- `Divipola-municipios.md` debe ser JSON válido pese a su extensión y contener
  `estado`, `conteo` y `resultado`;
- `conteo` y `resultado` deben representar exactamente 1.122 códigos
  `CODIGO_DPTO_MPIO` únicos, de cinco dígitos;
- `CODIGO_DPTO_MPIO` debe ser igual a
  `CODIGO_DEPARTAMENTO.zfill(2) + CODIGO_MUNICIPIO.zfill(3)`;
- `divipola-provenance.json` debe referenciar el SHA-256 aprobado del catálogo;
- no se inventarán equivalencias históricas ni se remapearán códigos no presentes;
  se excluirán con razón explícita y conteo de reconciliación;
- `Listados_DIVIPOLA.xlsx` no participa en el grafo ni puede contradecir el JSON.

#### D8.2. Normalización epidemiológica

- ambos CSV deben conservar el mismo encabezado ordenado de 69 columnas;
- el productor leerá por bloques y seleccionará únicamente `COD_EVE`,
  `COD_DPTO_R`, `COD_MUN_R` e `INI_SIN` para construir conteos; otros campos no
  entran a la tabla canónica;
- `dengue.csv` admite evento `210` y `dengue_grave.csv` evento `220`; cualquier
  evento diferente queda en reconciliación y no se reetiqueta;
- la identidad municipal se forma con residencia, normalizando departamento a
  dos dígitos y municipio a tres;
- `INI_SIN` se interpreta estrictamente como `dd/mm/YYYY` y define
  `year_month`; no se sustituye por `FEC_NOT` ni otra fecha;
- no se deduplica por `CONSECUTIVE`: los resultados son conteos de notificaciones,
  no personas, episodios ni casos confirmados;
- las dos corrientes se agregan por `municipality_code + year_month` y se
  conservan separadas; el total se calcula después de integrarlas;
- cada corrida reporta filas fuente, admitidas, fuera de ventana, fecha inválida,
  territorio inválido y evento incompatible, sin exportar microdatos.

#### D8.3. Normalización y agregación climática

- `google_earth_engine.csv` debe tener exactamente las 18 columnas aprobadas;
- la clave diaria es `mpio_cdpmp + date`, debe ser única y coherente con
  `dpto_ccdgo`; duplicados conflictivos detienen la corrida;
- las nueve variables diarias deben ser numéricas finitas cuando están presentes;
- se suman lluvia, escorrentía, evaporación y radiación solar;
- se promedian temperatura, punto de rocío, humedad del suelo y viento U/V;
- cada agregado conserva su contador `<variable>_valid_days` y solo recibe valor
  cuando los días válidos coinciden con los días calendario del mes;
- clima incompleto permanece nulo: nunca se rellena con cero ni con promedios de
  otros municipios o periodos;
- el recorte de diez columnas y cualquier archivo que no permita producir las
  nueve variables climáticas se rechaza en `raw_contract_validation`.

#### D8.4. Integración municipio-mes y derivación canónica

- el universo es la dimensión DIVIPOLA de 1.122 municipios;
- la salida de desarrollo cubre `2011-06` a `2024-12`: 163 meses y 182.886 claves
  municipio-mes esperadas;
- la cuadrícula territorial-temporal se define antes de observar densidad de
  casos; dentro de cobertura, ausencia de filas epidemiológicas significa cero;
- fuera de cobertura, ausencia permanece nula y nunca se convierte en cero;
- los joins de geografía, conteos y clima son `one-to-one` sobre
  `municipality_code + year_month`; duplicados o pérdida no explicada detienen la
  construcción;
- `total_notifications_count` debe ser exactamente la suma de las dos corrientes;
- `pipeline/src/sat_dengue_pipeline/domain/canonical.py` continúa como única
  autoridad para canal endémico, rezagos 1/2/3/12, percentiles H5 y roles;
- la tabla se ordena por municipio y mes antes de calcular el digest;
- `guard_development` se ejecuta nuevamente sobre la salida y sobre los orígenes
  por horizonte antes de etiquetas o consumidores aprendidos. Para T+1 el último
  origen admisible es `2024-11`; para T+2 es `2024-10`.

Cada módulo será una función pura respecto de sus entradas declaradas, sin red,
relojes, rutas personales, estado global ni acceso a modelos. Los joins declararán
cardinalidad esperada y fallarán ante duplicados o pérdida inesperada de filas. El
orden de columnas y filas, tipos, tratamiento de nulos, locale, zona horaria y
precisión numérica estarán fijados antes de calcular el digest.

La capacidad de “crear la misma tabla N veces” será un gate de reproducibilidad,
no N copias usadas para entrenar:

- `canonical_reproducibility` recibe un entero
  `canonical_rebuild_repetitions`; para certificar un release debe ser al menos 2
  y el valor inicial recomendado es 3;
- cada repetición ejecuta `canonical_build` en un proceso y directorio temporal
  independientes, sin reutilizar artefactos canónicos ni caches derivados; puede
  reutilizar únicamente el bundle crudo ya verificado por hash;
- todas las salidas deben coincidir exactamente en esquema, orden, tipos, claves,
  valores y máscara de nulos, y producir el mismo digest semántico estable;
- en la corrida canónica Linux también debe coincidir el SHA-256 del archivo
  serializado; una diferencia detiene el pipeline antes del entrenamiento;
- el diagnóstico identifica la primera clave/columna divergente, pero nunca elige
  una salida “mayoritaria” ni aplica tolerancias para ocultar la diferencia;
- tras aprobar, se conserva una sola tabla canónica junto con un reporte que
  registra N, hashes, tiempos, código, configuración, lock y manifiesto crudo; las
  copias temporales se descartan.

La ejecución cotidiana puede construir una vez o reutilizar una tabla canónica
cuya identidad completa coincida. La certificación inicial de cada release crudo,
cambio de productor o actualización de dependencias debe ejecutar el gate N veces.
La clave de linaje será, como mínimo:

```text
raw_manifest_digest + builder_git_sha + builder_config_digest + lock_digest
    -> canonical_semantic_digest
```

### D9. Experimentos declarativos y preinscritos

La validación `T16-FACTORY-XGB-S53-v1` permanece cerrada como evidencia de
ingeniería. Otros experimentos usarán un pipeline separado, previsto como
`experiment_run`, y no relajarán el validador ni sobrescribirán los recibos de
la tarea 16.

Cada enfoque del equipo tendrá una configuración ejecutable versionada:

```text
pipeline/conf/experiments/EXP001.yml
```

El índice científico único vivirá en:

```text
docs/experiments/registry.yml
```

Cada entrada tendrá esquema cerrado: `experiment_id`, slug, hipótesis, tipo,
estado, rutas y SHA-256 del protocolo/configuración, pipeline, conclusiones,
resultado científico y estado de champion. Las transiciones permitidas serán
`PROPOSED -> APPROVED -> RUNNING -> COMPLETED|BLOCKED`. Identificadores
duplicados, rutas absolutas, escapes, symlinks, campos desconocidos, hashes
alterados y ejecuciones no aprobadas fallarán de forma cerrada.

La configuración declarará, dentro de contratos permitidos, horizontes, predictores
canónicos, adaptador/versionado, semilla, hiperparámetros, preparación, cinco roles,
soportes, calibración, umbrales, métricas y líneas base. No aceptará imports
dinámicos. El registro de adaptadores será allowlist; inicialmente puede exponer
solo `xgboost_onset/v1` y rechazará familias aún no implementadas.

Cada ejecución tendrá `execution_id` único y `execution_signature` estable
calculada con experimento, protocolo, configuración, manifiesto de datos, Git,
lock y versiones científicas. La evidencia agregada se creará de forma exclusiva
y append-only bajo:

```text
docs/evidence/experiments/<experiment_id>/<execution_id>/
```

Como mínimo contendrá recibo, configuración, linaje, métricas, validación e
inventario SHA-256. Git no almacenará crudos, tabla canónica, X/y, predicciones
por fila, microdatos, secretos ni modelos pesados. Los modelos se identificarán
por hash; su almacenamiento físico remoto queda fuera de esta tarea.

MLflow registrará una corrida padre por ejecución y solo las hijas que representen
comparaciones reales, por ejemplo candidato/horizonte. El registro, protocolos,
conclusiones y evidencia Git deben permitir reconstruir la historia aunque se
pierda un store MLflow local. No se incorporará servidor o backend remoto.

Todo experimento completado tendrá `SPECIFICATION.md` y `CONCLUSIONS.md`,
incluidos resultados negativos o inconclusos. Una herramienta CLI determinista
leerá únicamente registro y evidencia para listar, filtrar y comparar experimentos.
La bitácora resumirá el aprendizaje y enlazará la evidencia sin duplicar todas las
métricas.

La especificación debe entrar por PR antes de ejecutar una corrida real. Dos
fixtures sintéticos probarán coexistencia, aislamiento, comparación, rechazo de
recetas alteradas y exclusión de 2025; no contarán como evidencia científica.

La implementación y los límites concretos de T17 se documentan en
[`docs/experiments/README.md`](docs/experiments/README.md), con evidencia de
aceptación en [`docs/evidence/task17/validation.json`](docs/evidence/task17/validation.json).
Los estados y el siguiente paso autorizado se consultan exclusivamente en `plan.md`.

### D10. Protocolo común de evaluación de inicios

Todos los enfoques producirán una interfaz común de probabilidades por:

```text
municipality_code, origin_month, target_month, horizon, probability
```

El arnés central, no cada modelo, construirá etiquetas, líneas base y métricas.
Reglas mínimas:

- inicio = exceso en el mes objetivo y no exceso en el mes calendario anterior;
- meses ausentes no se puentean ni se convierten en cero;
- elegibilidad se calcula solo con información disponible en el origen;
- a T+2 está prohibido condicionar con el estado del mes anterior al objetivo,
  porque todavía no ocurrió;
- las features del canal, incluido el bloque G, pasan pruebas de invariancia al
  truncar el futuro;
- calibración, selección de umbral y evaluación usan particiones distintas o
  predicciones out-of-fold; nunca se elige umbral sobre las filas evaluadas;
- las líneas base se evalúan sobre exactamente las mismas filas y con la misma
  información disponible.

Banco de desarrollo propuesto: rolling origin anual 2018–2024. Cada año exterior
se evalúa una sola vez con entrenamiento/desarrollo anteriores. La política exacta
de calibración y umbral debe congelarse en un ADR científico antes de reproducir
la tanda G, porque el código original de las tandas no está en V3.

Métricas obligatorias:

- sensibilidad de inicios y conteos absolutos;
- falsas alarmas por inicio detectado;
- tasa de falsas alarmas;
- número total de alertas;
- AUROC y average precision sobre inicios;
- Brier y calibración;
- desglose por año, departamento, municipio cuando el soporte lo permita;
- intervalos emparejados que respeten bloques temporales/municipales;
- curvas a igual volumen de alertas, no solo un punto de operación.

Líneas base obligatorias:

- persistencia;
- canal endémico estándar;
- canal con umbral ajustado;
- canal condicionado, con la restricción informacional correcta por horizonte.

### D11. El avance G se replica, no se asume

`margen_objetivo` y el bloque G de la bitácora son candidatos prioritarios. La
primera tarea científica debe intentar recuperar, mediante PR, los scripts,
configuraciones, matrices y manifests originales del autor. Si no se obtienen:

- se implementan de manera independiente desde la especificación escrita;
- se crean pruebas primitivas de índices, umbrales e invariancia temporal;
- se compara contra los resultados publicados con tolerancias predeclaradas;
- cualquier diferencia queda como `NOT_REPRODUCED`, no se ajusta hasta coincidir;
- el resultado nuevo se etiqueta como reproducción independiente, no como la
  misma corrida.

La migración debe preservar el hallazgo metodológico más importante de la bitácora:
una línea base incorrecta puede exagerar más al modelo que un error de métrica.

### D12. Selección y promoción separadas

El pipeline puede recomendar un candidato, pero no promoverlo solo.

1. `experiment` produce una tabla comparable y un `candidate_recommendation.json`.
2. Un PR científico revisa protocolo, resultados y limitaciones.
3. La aprobación humana fija `champion.yml` con su run, datos, código y política.
4. Solo entonces se habilita `final_validation`.
5. La validación final no reentrena, no cambia umbral y no elige otra variante.
6. `publish` transforma únicamente una corrida aprobada al contrato existente de
   `datos/resultados/`.

El champion de T+1 y el de T+2 pueden ser distintos o puede no existir champion
para un horizonte.

### D13. Reproducibilidad portable y corrida canónica

El mismo pipeline debe ejecutar en todos los ambientes, pero no se exigirá que un
modelo serializado sea byte a byte idéntico entre macOS ARM, Windows y Linux. Se
definen dos niveles:

- **portable run:** mismo código, datos, configuración y semillas; métricas y
  predicciones dentro de tolerancias predeclaradas;
- **canonical run:** Linux CPU, imagen Docker fijada, un hilo cuando aplique,
  versiones bloqueadas; única corrida habilitada para publicar artefactos oficiales.

Cada corrida incluirá:

- Git SHA y diff limpio/sucio;
- hash del spec, del manifiesto crudo, de cada fuente, de la configuración del
  constructor, de la tabla canónica y del lock;
- adaptador, proveedor, revisión inmutable o DOI y fallback realmente utilizado;
- sistema operativo, arquitectura y versiones;
- semillas y política de paralelismo;
- número de reconstrucciones canónicas, digest de cada repetición y resultado del
  gate de igualdad;
- tiempos, filas por etapa y periodos leídos;
- manifiesto de archivos de salida con SHA-256.

Se reemplazarán supuestos POSIX heredados de V2, como `fcntl`, por mecanismos de
bloqueo/atomicidad portables.

### D14. Publicación como frontera; despliegue existente protegido

El análisis de V3 en `main@1302152310a68812bc4d7e89166ef3e9978619b5`
confirma que `app/api` y `app/dashboard` forman una aplicación de solo lectura y
que `datos/resultados/` ya es su contrato estable. La implementación E2E no
reorganizará `app/`, `docker/` ni los scripts operativos en sus primeros bloques.

El pipeline `deployment_publication` será el único componente científico que
puede producir archivos bajo `datos/resultados/`. La migración de
`scripts/construir_resultados.py` será gradual:

1. caracterizar su salida actual con fixtures y pruebas de igualdad;
2. trasladar la lógica a funciones puras dentro de
   `pipeline/src/sat_dengue_pipeline/pipelines/deployment_publication/`;
3. mantener el script como envoltura temporal de compatibilidad;
4. retirarlo fuera de esta primera implementación y solo cuando API y tablero
   acepten una salida byte-equivalente o semánticamente equivalente según el
   contrato aprobado.

`app/api/sat_api/almacenamiento.py` seguirá atendiendo la recuperación de JSON
publicados para el despliegue. No se reutilizará como adaptador de datos de
entrenamiento: `pipeline/src/sat_dengue_pipeline/acquisition/sources.py` mantiene
el adaptador S3 bajo un contrato, pruebas y ciclo de vida independientes.

Antes de conectar el E2E se congelará una línea base del despliegue. Debe
verificarse y, si corresponde, corregirse en un commit aislado dentro del único PR
la promesa de que un clon limpio arranca con resultados: el Dockerfile actual no copia
`datos/resultados/` y Compose monta un volumen nombrado inicialmente vacío. La
sincronización de JSON desde S3 también se endurecerá separadamente con descarga
atómica e integridad por hash; estas correcciones no se mezclarán con el esqueleto
de Kedro.

## 4. Flujo E2E propuesto

```text
Git PR + spec del experimento
            |
            v
manifiesto crudo -> DataSource -> caché local -> fuentes crudas hasta 2025
                       |                              |
           HF inicial / Zenodo / local               v
                                            validación de contratos
                                                      |
                                                      v
                                       cuarentena por claves temporales
                                                      |
                          +---------------------------+-------------------------+
                          |                           |                         |
                          v                           v                         v
                 epidemiología                   clima                 geografía/referencia
                          |                           |                         |
                          +---------------------------+-------------------------+
                                                      |
                                                      v
                                   integración municipio-mes <= 2024
                                                      |
                                                      v
                                 canonical_build -> tabla canónica derivada
                                                      |
                                  +-------------------+------------------+
                                  |                                      |
                                  v                                      v
                   validación normal de corrida       certificación N reconstrucciones
                                  |                                      |
                                  +-------------------+------------------+
                                                      |
                                                      v
                                    guard_development existente de V3
                                                      |
                                                      v
                                      features base + bloque candidato
                                                |
                                                v
                                     rolling origin / folds temporales
                                                |
                                                v
                                   entrenar -> calibrar -> fijar umbral
                                                |
                                                v
                                evaluar modelo + líneas base emparejadas
                                                |
                                          +--------------------+-------------------+
                                          |                                        |
                                          v                                        v
                                   MLflow + artifacts                    reporte/decisión versionada
                                                                                   |
                                                                     aprobación humana por PR
                                                                                   |
                                                       +---------------------------+----------------+
                                                       |                                            |
                                                       v                                            v
                                              final_validation bloqueado                 publish al API/tablero
```

## 5. Estructura objetivo del repositorio

El árbol siguiente conserva el objetivo de diseño original y no debe leerse como
inventario del checkout. La estructura implementada y sus comandos vigentes se
documentan en `pipeline/README.md`, `docs/operations/pipeline-operations.md` y
`docs/experiments/manual_pipeline.md`; por ejemplo, no existe una CLI `satd` ni
se registran por separado todos los pipelines lógicos enumerados arriba.

```text
.
├── app/                               # producto desplegado; conservar estructura
│   ├── api/
│   └── dashboard/
├── pipeline/                          # proyecto Kedro autocontenido
│   ├── pyproject.toml
│   ├── uv.lock
│   ├── .python-version
│   ├── README.md
│   ├── conf/
│   │   ├── base/
│   │   │   ├── catalog.yml
│   │   │   ├── data_sources.yml       # adaptador y release crudo, sin secretos
│   │   │   └── parameters.yml
│   │   ├── experiments/
│   │   │   └── EXP001.yml
│   │   └── final_validation/          # sin datos ni secretos en Git
│   ├── manifests/
│   │   └── data_releases/             # identidad lógica y fuentes por release
│   ├── src/sat_dengue_pipeline/
│   │   ├── cli.py
│   │   ├── pipeline_registry.py
│   │   ├── acquisition/                # puerto, resolver y adaptadores existentes
│   │   │   ├── contracts.py
│   │   │   ├── resolver.py
│   │   │   └── sources.py
│   │   ├── data_contracts/
│   │   ├── canonical/                  # normalizadores crudos y ensamblador
│   │   │   ├── epidemiology.py
│   │   │   ├── climate.py
│   │   │   ├── geography.py
│   │   │   ├── integration.py
│   │   │   └── reproducibility.py
│   │   ├── pipelines/
│   │   │   ├── data_acquisition/
│   │   │   ├── raw_data_validation/
│   │   │   ├── raw_temporal_quarantine/
│   │   │   ├── canonical_sources/
│   │   │   ├── canonical_panel/
│   │   │   ├── canonical_reproducibility/
│   │   │   ├── feature_engineering/
│   │   │   ├── training/
│   │   │   ├── evaluation/
│   │   │   └── deployment_publication/
│   │   ├── models/
│   │   └── tracking/
│   ├── tests/
│   │   ├── unit/
│   │   ├── contracts/
│   │   ├── integration/
│   │   └── e2e/
│   ├── notebooks/                     # exploración, sin lógica obligatoria
│   ├── data/                          # crudos y derivados ignorados salvo fixtures
│   │   ├── 01_raw/                    # bundle materializado; solo fuentes crudas
│   │   ├── 02_intermediate/           # salidas modulares por fuente
│   │   └── 03_primary/                # tabla canónica certificada
│   ├── artifacts/                     # artefactos locales ignorados; MLflow
│   └── docker/                        # corrida científica canónica
├── datos/
│   ├── datos-crudos/                  # staging local ignorado; entrada LocalDataSource
│   ├── resultados/                    # único contrato pipeline -> API
│   └── retro/
├── docker/                            # despliegue actual; no incluye pipeline
├── scripts/                           # operación y envolturas temporales
├── modelos/                           # legado/punteros; sin artefactos pesados nuevos
├── notebooks/                         # legado; redirige a pipeline/notebooks
├── docs/
│   ├── architecture/
│   ├── data/
│   ├── experiments/
│   │   ├── registry.yml               # índice científico único
│   │   └── EXP001/
│   │       ├── SPECIFICATION.md
│   │       └── CONCLUSIONS.md
│   ├── evidence/
│   │   └── experiments/               # recibos agregados append-only
│   └── decisions/
└── .github/
    ├── CODEOWNERS
    ├── pull_request_template.md
    └── workflows/
        ├── pipeline-ci.yml
        ├── api-ci.yml
        ├── dashboard-ci.yml
        └── publication-contract.yml
```

La carpeta personal `experimentos/` deja de ser la fuente de trabajo. El código
reutilizable va a `pipeline/src/`, los specs a `pipeline/conf/experiments/`, los
derivados grandes a almacenamiento local ignorado o se regeneran, y los informes pequeños a
`docs/experiments/` mediante PR. Los nuevos notebooks vivirán en
`pipeline/notebooks/`; los directorios raíz `notebooks/` y `modelos/` actuales no
recibirán trabajo científico nuevo y solo se retirarán o redirigirán en un PR de
limpieza posterior.

## 6. Gobernanza GitHub y CI

Antes del merge del único PR, un administrador debe activar un ruleset
para `main`:

- requerir pull request;
- mínimo una aprobación que no sea del autor;
- descartar aprobación cuando cambie el diff;
- requerir checks verdes y conversación resuelta;
- bloquear force push y borrado;
- sin bypass rutinario, incluidos administradores si el plan lo permite.

Checks obligatorios en PR:

1. Ruff y formato;
2. mypy;
3. unitarias y contratos;
4. E2E sintético de Kedro;
5. prueba de cuarentena 2025;
6. pruebas anti-fuga/prefix invariance;
7. API Python;
8. lint/test/build del dashboard;
9. validación de `pipeline/uv.lock` y del registro de experimentos;
10. escaneo de secretos y dependencias;
11. pruebas contractuales comunes para `LocalDataSource`, Hugging Face y Zenodo;
12. rechazo de manifiestos con `main`, `latest`, archivos sin hash o fuentes no
    registradas;
13. rechazo de releases que incluyan tablas canónicas o matrices listas para
    entrenamiento en lugar de `raw_sources`;
14. reconstrucción canónica sintética N veces, con caches derivados aislados y
    digest idéntico;
15. pruebas de contratos, cardinalidad de joins, orden, tipos, nulos e idempotencia
    de cada productor crudo;
16. verificación de que no se agregaron datos/modelos grandes a Git.

Matriz portable de CI: Ubuntu, macOS y Windows para el E2E sintético; la suite
completa puede quedar en Ubuntu y los otros sistemas ejecutar el smoke crítico.
Los datos reales no entran en GitHub Actions; el gate N de CI utilizará un bundle
crudo sintético pequeño. Los checks se dividirán por
responsabilidad: `pipeline-ci`, `api-ci`, `dashboard-ci` y
`publication-contract`. Cada workflow usará filtros de rutas sin impedir que un
cambio en `datos/resultados/` ejecute conjuntamente el contrato de publicación,
las pruebas de la API y las del tablero.

El primer gate de integración será una línea base del despliegue actual: construir
las imágenes, arrancar Compose desde un clon limpio, verificar `/api/salud` y una
consulta válida del tablero. El E2E no podrá incorporarse si rompe esa línea base.

## 7. Tareas de implementación propuestas

El estado ejecutable y los commits de estas tareas se controlan en `plan.md`. Este
documento conserva la arquitectura y los criterios que deben guiar lo pendiente.

Impacto de la decisión v7: las tareas 1–16 conservan su estado y evidencia. Se
inserta una nueva tarea 17 para generalizar la fábrica y administrar experimentos;
las antiguas tareas 17–21 pasan a 18–22. `plan.md` registra DEC-024 y es la única
autoridad sobre estados y avance. Este documento conserva las directrices y el
detalle arquitectónico, sin mantener un estado operativo paralelo.

Secuencia de integración obligatoria dentro del único PR:

```text
gobernanza -> línea base de despliegue -> esqueleto pipeline -> adquisición cruda
-> construcción canónica -> preparación científica -> entrenamiento/evaluación
-> administración/comparación de experimentos -> publicación -> limpieza
```

La corrección del despliegue actual, la creación de Kedro y la migración científica
se separarán mediante commits y gates verificables dentro de la misma rama. El
único PR debe dejar API y tablero operativos; los cambios de contrato requieren
pruebas de los tres consumidores: publicador, API y tablero.

1. **Congelar decisiones y fronteras.** Crear ADRs de monorepo, puerto
   `DataSource`, estructura `pipeline/`, frontera `datos/resultados/`, Hugging
   Face operativo, Zenodo archivístico, migración futura a S3/AWS, release crudo
   hasta 2025, construcción canónica en Kedro, protocolo temporal y estado
   consumido de 2025.
2. **Activar gobernanza y CI por componentes.** Configurar ruleset de `main`,
   CODEOWNERS, plantilla de PR y workflows separados para pipeline, API, tablero
   y contrato de publicación.
3. **Congelar y proteger la línea base del despliegue.** Caracterizar el arranque
   desde clon limpio, Docker Compose, disponibilidad de resultados, salud y
   consulta del tablero. Corregir en un commit independiente el sembrado del volumen
   y endurecer la sincronización S3 con atomicidad/hash si las pruebas confirman
   las brechas, sin introducir todavía Kedro.
4. **Crear el subproyecto `pipeline/` con Python/Kedro/uv.** Empaquetado, lock,
   CLI, estructura autocontenida, reglas `.gitignore` para cachés/artefactos y E2E
   sintético vacío, sin modificar `app/` ni las imágenes del despliegue.
5. **Implementar contrato de releases y adquisición desacoplada.** Puerto
   `DataSource`, `ResolvedBundle`, manifiestos, caché, descarga atómica,
   adaptadores local/Hugging Face/Zenodo/S3, fallback, fixture sintético y pruebas
   contractuales reutilizables. `S3DataSource` se validará contra un servicio S3
   simulado, sin aprovisionar AWS real. Esta tarea completada creó el transporte
   neutral; la restricción `raw_sources` y los productores reales se añaden en la
   tarea 13. La tabla canónica no se distribuirá mediante DVC ni otro remoto.
6. **Migrar la lógica canónica de dominio desde V2.** Portar validación y
   predictores derivados, documentar procedencia y verificar igualdad sobre una
   muestra artificial aprobada. Esta tarea completada no equivale a ingestión real
   desde archivos crudos.
7. **Implementar etiquetas y controles temporales.** Inicio, elegibilidad,
   ausencias, horizontes y centinela 2025 con pruebas primitivas. Esta tarea deja
   como autoridad de V3 a `TemporalPolicy` y `guard_development`; las tareas
   posteriores deben reutilizarlos, no duplicarlos.
8. **Recuperar o reimplementar el arnés de tandas.** Priorizar G y el rolling
   origin 2018–2024; registrar cualquier falta de equivalencia.
9. **Implementar adaptadores de modelos.** Interfaz común para enfoques de los
   cuatro integrantes, sin duplicar evaluación.
10. **Implementar calibración, umbral y líneas base.** Separación temporal y
   restricciones simétricas por horizonte.
11. **Implementar métricas e incertidumbre.** Tablas emparejadas, curvas de
    volumen, estratos y soporte.
12. **Agregar trazabilidad de corridas.** MLflow, manifiesto y hash, adaptador,
    revisión de Hugging Face o DOI de Zenodo, fallback utilizado, run IDs,
    rangos temporales por rol, hashes crudos, identidad del constructor, digest
    canónico y digest/conteo de la cuarentena. La tarea reserva estos campos; la
    tarea 13 los conecta al constructor real, sin registrar valores o etiquetas de
    2025 como insumos del experimento.
13. **Construir y certificar la tabla canónica desde fuentes crudas.** Extender el
    manifiesto con `release_kind: raw_sources`; rechazar el release derivado actual;
    fijar la lista cerrada de los cinco archivos, sus tamaños, hashes y esquemas;
    implementar `raw_contract_validation`, proyección/cuarentena temporal,
    dimensión DIVIPOLA, normalizadores epidemiológicos por residencia/`INI_SIN`,
    agregación climática de nueve variables e integración de las 182.886 claves
    municipio-mes. Reutilizar `domain/canonical.py`, añadir contratos de joins y
    registrar el pipeline `canonical_build`. Añadir
    `canonical_reproducibility` para ejecutar la construcción N veces de forma
    aislada, comparar igualdad exacta y liberar una sola salida local únicamente si
    todos los digests coinciden. Prohibir el archivo climático recortado y el Excel
    DIVIPOLA como insumos de ejecución. Integrar la cuarentena antes de los
    productores y reutilizar `guard_development` después de la tabla canónica.
14. **Migrar la publicación sin romper el despliegue.** Caracterizar
    `scripts/construir_resultados.py`, portar su lógica a
    `pipeline/.../deployment_publication`, mantenerlo temporalmente como envoltura
    y exigir equivalencia del contrato API/dashboard antes de retirarlo.
15. **Cerrar portabilidad.** macOS Intel/ARM, Windows, Linux/Colab, rutas, locks,
    wheels, construcción canónica, digests, tolerancias de modelos y comportamiento
    idéntico de adquisición.
16. **Conectar el nuevo release crudo y ejecutar reproducción sintética y real.**
    Primero fixture; luego el nuevo release de fuentes crudas fijado por commit y
    hashes. Ejecutar el gate canónico con N=3 en la corrida de certificación, usar
    la única salida aprobada para el experimento y demostrar con el guard de V3 que
    2025 no llega a ningún componente aprendido. El release derivado anterior está
    prohibido. Esta es la primera descarga científica real; la tarea 5 solo dejó el
    adaptador y su contrato de transporte preparados.
17. **Generalizar la fábrica y administrar experimentos reproducibles.** Conservar
    `factory_validation`, T16 y sus hashes sin cambios; crear registro científico
    y esquemas cerrados, configuraciones/protocolos congelados, pipeline separado
    `experiment_run`, identidad por ejecución, evidencia agregada append-only,
    tracking MLflow padre/hijas, conclusiones obligatorias y comparación
    determinista. Validar con dos fixtures diferentes sin ejecutar ciencia real,
    HPO, selección de champion, nuevas familias ni backend remoto. Una receta no
    aprobada, alterada o que habilite 2025 debe fallar antes del ajuste.
18. **Revisión científica independiente.** Auditar fuentes, construcción canónica,
    determinismo N veces, etiquetas, línea base, información disponible, folds,
    métricas, gobernanza experimental y correspondencia con la bitácora.
19. **Documentar operación, límites y migraciones.** Guía de un comando,
    troubleshooting, Colab, publicación de fuentes crudas en HF/Zenodo,
    reconstrucción canónica, registro y comparación de un nuevo enfoque,
    recuperación de una corrida, significado de `app/`, `pipeline/` y
    `datos/`, y procedimiento HF → AWS sin cambiar componentes científicos.
20. **Revisión de seguridad.** Decisión de publicación, clasificación de fuentes
    crudas, registro/evidencia experimental, tokens, propietarios, secretos,
    dependencias, futuros buckets, logs y superficies de red.
21. **Descubrimiento de skills y agentes.** Registrar exactamente cuatro skills
    canónicas bajo `.agents/skills/`: operación experimental, revisión científica,
    verificación y recuperación. Documentarlas en `docs/agents/skills-catalog.md`
    y en el manual, sin añadir agentes, plugins, hooks ni autoridades paralelas.
22. **Corregir caché y recibos de adquisición.** Depende de T21: distinguir caché
    ausente, no directorio, faltantes, adicionales, corrupción y symlinks; conservar
    integridad existente. Recibos exclusivos bajo `pipeline/data/`, nunca sobre T16.
23. **Agregar operación portable y comando canónico E2E.** Depende de T22:
    helper delgado en `pipeline/tools/`, mismo intérprete, adquisición y luego
    `canonical_build` aprobado; salida provisional. Documentar secretos por shell
    y recursos históricos, sin garantías de RAM no demostradas.
24. **Validar las correcciones operativas acumuladas.** Depende de T23: gate local
    completo, pruebas sin fuentes privadas, checkout limpio y preservación por hash.
25. **Elaborar reporte ejecutivo final.** Depende de T24; antigua T22. Resumir
    entregables, validaciones, limitaciones y decisiones pendientes.
26. **Publicar cambios y validar el PR #1.** Depende de T25; fase 2 pendiente y
    autorización posterior. Publicar únicamente en el PR existente y comprobar CI
    remota del nuevo HEAD, sin atribuirle resultados históricos.
27. **Ejecutar auditoría final de merge.** Depende de T26; fase 2 pendiente.
    Verificar ruleset, revisión independiente, conversaciones y checks obligatorios;
    el merge requiere autorización específica.

DEC-027 amplía el plan por revisión humana: conserva T1–T21 y toda la historia;
la antigua T22 pasa a T25. La fase 1 autoriza exclusivamente T22–T24 operativas,
sin ciencia, fuentes privadas, entrenamiento ni cambios a T16/EXP001/EXP002.
Ampliación temporal, canal condicionado y EXP003 quedan fuera; trabajo científico
posterior necesita otro alcance después del merge. El progreso inicial es 21/27;
los estados y el control de avance viven exclusivamente en `plan.md`.

## 8. Criterios de aceptación del producto E2E

La implementación estará lista cuando las 27 tareas y sus dependencias estén
completas según `plan.md`. La entrega local de fase 1 termina en T24, con T25–T27
pendientes y sin publicar. Se exige además:

- errores de caché controlados sin rutas privadas y sin relajar integridad;
- recibos operacionales exclusivos e ignorados que no sobrescriban historia;
- adquisición y construcción provisional mediante un helper portable sin ciencia;
- gate local acumulado y checkout limpio, preservando evidencia y publicación;

- un clon limpio conserva el despliegue actual: Compose levanta API, tablero y
  proxy, `/api/salud` reporta resultados y una consulta válida responde 200;
- un clon limpio ejecuta el E2E sintético con un comando en Ubuntu, macOS y
  Windows;
- el mismo comando corre en Colab sin copiar lógica a un notebook;
- los cuatro integrantes obtienen el nuevo release privado de fuentes crudas desde
  Hugging Face con cuentas y tokens individuales, sin pedir archivos, autorización
  en cada corrida ni ayuda de otro integrante;
- los CSV epidemiológicos completos permanecen privados; cualquier publicación
  futura requiere minimización, nuevo manifiesto y revisión de seguridad;
- el manifiesto acepta exclusivamente los cinco archivos, tamaños y SHA-256
  aprobados y rechaza `google_earth_engine-selected-columns.csv` y
  `Listados_DIVIPOLA.xlsx` como entradas científicas;
- el mismo release crudo puede recuperarse desde Zenodo cuando exista el depósito
  académico, y ambas copias producen los mismos SHA-256 por archivo fuente;
- un bundle crudo local válido puede sustituir la descarga sin editar código;
- cambiar Hugging Face por local, Zenodo o un adaptador S3 simulado exige solo
  configuración/manifiesto y no modifica componentes posteriores a adquisición;
- el contrato rechaza `sat-dengue-v3-through-2025-v1` y cualquier otro release que
  entregue una tabla canónica o matrices listas para entrenamiento;
- ningún módulo posterior a `data_acquisition` importa SDKs o contiene URLs,
  credenciales o condiciones específicas de un proveedor;
- ningún módulo de `app/` importa `pipeline/`, y las dependencias pesadas de ML no
  aparecen en la imagen ni en `app/api/requirements.txt`;
- el único efecto del pipeline sobre el producto desplegado ocurre mediante
  `deployment_publication` y archivos validados bajo `datos/resultados/`;
- modificar `datos/resultados/` activa automáticamente las pruebas del contrato,
  la API y el tablero;
- una descarga interrumpida o corrupta no se publica en caché y falla antes de
  cualquier transformación;
- la transformación cruda reproduce una cuadrícula de 1.122 municipios por 163
  meses, 182.886 claves únicas entre `2011-06` y `2024-12`;
- los dos productores epidemiológicos usan residencia e `INI_SIN`, conservan
  eventos 210/220 separados, no aplican fallback de fecha y no deduplican por
  `CONSECUTIVE`;
- el productor climático genera cuatro sumas y cinco medias mensuales, conserva
  días válidos y deja nulo cualquier mes incompleto;
- los conteos se conservan de fuente a salida y todo rechazo queda reconciliado
  por razón sin publicar filas individuales;
- dos ejecuciones ordinarias del mismo release pueden reutilizar el bundle crudo y
  una tabla canónica cuya identidad completa coincida;
- el modo de certificación reconstruye la tabla canónica N veces sin reutilizar
  derivados y obtiene exactamente el mismo esquema, orden, tipos, claves, valores,
  nulos y digest en todas las repeticiones;
- la corrida canónica con N=3 produce además el mismo SHA-256 serializado; cualquier
  divergencia detiene el flujo antes del entrenamiento;
- solo una salida canónica certificada continúa al experimento y su linaje permite
  reconstruirla desde manifiesto crudo, código, configuración y lock;
- no existe ruta manual entre adquisición cruda, construcción canónica,
  preparación, entrenamiento y evaluación;
- el bundle adquirido puede contener 2025, pero ninguna fila con observación,
  origen u objetivo desde `2025-01` puede entrar a la construcción canónica de
  desarrollo ni a una vista aprendible, incluso por configuración errónea;
- `guard_development` se ejecuta antes de etiquetas y consumidores aprendidos, y
  las pruebas rechazan también los cruces de horizonte desde 2024 hacia 2025;
- cada corrida puede reconstruirse desde Git SHA, release crudo, configuración del
  constructor, digest canónico, lock y spec;
- dos experimentos aprobados pueden coexistir y compararse sin sobrescribir
  configuración, evidencia, conclusiones o corridas anteriores;
- una receta no registrada, no aprobada, con hash alterado, ruta insegura o intento
  de habilitar 2025 falla antes de cualquier ajuste;
- cada ejecución conserva identidad, estado terminal, métricas agregadas, linaje e
  inventario SHA-256 en evidencia Git append-only, aunque el MLflow local se pierda;
- todo experimento `COMPLETED` tiene especificación y conclusiones que registran
  hipótesis, resultado, limitaciones, aprendizaje y siguiente decisión;
- una herramienta determinista lista y compara experimentos desde el registro y
  la evidencia agregada, sin depender de microdatos ni predicciones individuales;
- `factory_validation`, los 16 recibos anteriores y la identidad N=3 de T16
  permanecen intactos;
- un nuevo enfoque de modelo se agrega como adaptador + spec, reutilizando el
  mismo arnés;
- las líneas base y el modelo usan las mismas filas e información disponible;
- el E2E con objetivos de desarrollo hasta 2024 produce un reporte reproducible y
  una conclusión honesta de equivalencia o no equivalencia con la bitácora;
- el publicador genera JSON que pasa las pruebas actuales de API y dashboard;
- ningún cambio llega a `main` sin PR, aprobación y checks verdes;
- no se suben datos sensibles, modelos grandes ni secretos a Git.

## 9. Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Recibos operacionales sobrescriben evidencia cerrada | T22: directorio exclusivo por ejecución bajo pipeline/data/, sin escritura histórica |
| El helper se confunde con certificación o experimento | T23: solo adquisición y canonical_build provisional, sin N=3 ni entrenamiento |
| Se atribuye CI anterior a commits locales nuevos | T24 es local; publicación y CI del HEAD nuevo pertenecen a T26 |
| Los scripts originales de las tandas no se entregan | Recuperación prioritaria; si falla, reproducción independiente y estado `NOT_REPRODUCED` |
| El esqueleto Kedro rompe el despliegue existente | `pipeline/` autocontenido, línea base Docker previa y CI separado por componentes |
| Se mezclan dependencias de ML con la API | Entornos y locks independientes; la imagen API no copia ni instala `pipeline/` |
| Conviven dos publicadores con resultados distintos | Pruebas de caracterización; script temporal delega en funciones puras; retiro solo tras equivalencia |
| El volumen Docker arranca vacío aunque Git contiene resultados | Smoke desde clon limpio y corrección aislada del mecanismo de sembrado antes de integrar el E2E |
| Se confunden `pipeline/data/` y `datos/resultados/` | Documentación explícita: el primero es caché/trabajo ignorado; el segundo es contrato publicado y revisado |
| Se pierde trazabilidad de fuentes aunque no se requiera licencia o autorización | Manifiesto conserva procedencia, atribución y la decisión explícita `not_required` |
| 2025 se trata como virgen por costumbre | Rol `consumed_retrospective_evidence`, cuarentena, guard técnico de V3 y periodo posterior para validación final |
| El release crudo permite una fuga accidental desde 2025 | Cuarentena antes de productores, vista por objetivo, `guard_development` y centinelas T+1/T+2 que fallan de forma cerrada |
| Se reutiliza por accidente la tabla canónica publicada anteriormente | `release_kind: raw_sources`, lista de artefactos prohibidos y prueba que rechaza el release derivado anterior |
| Se usa el archivo climático recortado | Lista cerrada, hash y encabezado de 18 columnas; rechazo antes de proyectar fechas o calcular clima |
| Se pierde la historia al borrar un store MLflow local | Registro, protocolos, conclusiones y evidencia agregada append-only versionados en Git; MLflow es índice secundario |
| Una nueva receta sobrescribe o reinterpreta T16 | Pipeline `experiment_run` separado, escritura exclusiva por ejecución y regresiones sobre hashes/recibos T16 |
| Registro y configuración divergen | Hashes obligatorios, esquema cerrado, estados controlados y rechazo fail-closed antes de adquirir o ajustar |
| DIVIPOLA tiene dos autoridades | Solo el JSON y su procedencia participan en ejecución; el Excel queda fuera del bundle |
| La construcción canónica cambia entre ejecuciones | Gate N en procesos y directorios aislados, igualdad exacta, digest semántico y fallo antes de entrenar |
| Un join crudo duplica o elimina municipios-periodos silenciosamente | Cardinalidad declarada, unicidad por etapa, conteos antes/después y contratos fail-closed |
| Se confunde “crudo” con autorización para publicar microdatos | Release completo privado, acceso individual, sin descarga anónima; una versión pública exige minimización y revisión nueva |
| Hugging Face cambia límites o no está disponible | Revisión fija, archivos portables, Zenodo para releases estables y fallback verificado |
| Hugging Face y Zenodo divergen | SHA-256 por fuente cruda; una corrida falla si la copia no coincide con el manifiesto |
| La lógica del proveedor invade el pipeline | Puerto `DataSource`, `ResolvedBundle` y prueba arquitectónica de imports/fronteras |
| Se usa `main` o `latest` | Validador rechaza referencias mutables antes de descargar |
| La migración futura a AWS exige reescribir el E2E | Adaptador S3 bajo el mismo contrato y pruebas contractuales reutilizables |
| Aparece una segunda orquestación de datos | Kedro es el único grafo; no se incorpora DVC en esta implementación |
| Resultados distintos entre sistemas | lock universal, normalización estable, digest canónico, semillas, un hilo canónico, tolerancias de modelos y manifiesto de entorno |
| Colab se desconecta | descarga y caché atómicas, checkpoints por etapa y reanudación explícita |
| Cada integrante crea su propio arnés | contrato de adaptador y evaluación central obligatoria |
| La línea base favorece o castiga artificialmente | filas emparejadas, información simétrica, curvas de volumen y revisión independiente |
| Branch protection se asume pero no existe | El ruleset debe verificarse obligatoriamente antes del merge; su ausencia no bloquea implementación local en la rama ni validación mediante el único PR |

## 10. Decisiones humanas y operativas

1. **Licencia y autorización:** el equipo confirmó que no se requieren; registrar
   `not_required` sin eliminar procedencia, atribución ni la obligación de mantener
   privados los microdatos individuales completos.
2. **Gobernanza de plataformas:** completar la administración de Hugging Face, la
   comunidad de Zenodo, al menos dos administradores y recuperación de acceso.
3. **Nuevo release crudo:** el inventario local de cinco archivos, granularidad,
   claves, tamaños y hashes queda aprobado por esta versión. Falta publicar una
   revisión privada inmutable y decidir cuáles versiones se archivan con DOI en
   Zenodo. El release derivado anterior y el clima recortado no son elegibles.
4. **Política del contrato desplegable:** decidir qué resultados pequeños se
   versionan en `datos/resultados/`, cómo se siembra el volumen Docker y quién
   aprueba su publicación.
5. **Estado de 2025:** queda fijado como `consumed_retrospective_evidence`; reservar
   un periodo posterior no utilizado para validación realmente independiente.
6. **Protocolo rolling-origin:** congelar las particiones internas de ajuste,
   calibración y selección de umbral.
7. **Autoridad de champion:** quién aprueba `champion.yml` y cuántas revisiones
   científicas se requieren.
8. **Disponibilidad de los scripts/artefactos originales:** el autor debe aportarlos
   mediante PR o declarar que la reproducción será independiente.

## 11. Fuera de alcance de la primera implementación

- inferencia operativa en línea;
- promoción automática de modelos;
- uso de 2025 en preparación aprendida, entrenamiento, HPO, calibración, umbrales,
  selección, construcción canónica de desarrollo o evaluación presentada como
  independiente; su descarga, verificación y cuarentena técnica sí forman parte
  del E2E;
- reconstrucción universal desde sistemas fuente externos no disponibles;
- infraestructura distribuida de entrenamiento;
- aprovisionar una cuenta AWS o migrar datos reales a S3 en la primera versión;
- incorporar DVC o publicar datasets derivados en la nube;
- reorganizar o renombrar `app/`, `docker/` y los scripts operativos existentes en
  los primeros bloques de implementación;
- hacer que el Docker Compose del producto ejecute entrenamiento;
- convertir notebooks en pasos obligatorios;
- modificar el dashboard salvo lo necesario para mantener su contrato de datos.

## 12. Referencias técnicas de la decisión

- [Kedro Data Catalog](https://docs.kedro.org/en/latest/catalog-data/data_catalog/)
- [Hugging Face: descarga de datasets](https://huggingface.co/docs/hub/datasets-downloading)
- [Hugging Face: límites de almacenamiento](https://huggingface.co/docs/hub/storage-limits)
- [Zenodo: ayuda y versionamiento](https://help.zenodo.org/)
- [uv: proyectos y lock multiplataforma](https://docs.astral.sh/uv/guides/projects/)
- [MLflow Tracking](https://mlflow.org/docs/latest/tracking/)
- [GitHub rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets)
