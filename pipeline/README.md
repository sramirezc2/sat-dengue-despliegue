# Pipeline SAT DENGUE: sintético y adquisición desacoplada

Subproyecto Kedro independiente del despliegue. Actualmente prueba cinco etapas
en memoria: generar observaciones artificiales, validarlas, ajustar una constante,
evaluarla y producir métricas. No es un modelo científico ni autoriza alertas.

Requisitos: Python 3.12 y uv (validado con 0.11.19). Dependencias fijadas en
`pyproject.toml` y resueltas en `uv.lock`: Kedro 1.7.0, pytest 9.2.0 y Ruff 0.17.4.
La adquisición agrega `huggingface_hub` 2.4.0. No se requieren AWS, credenciales,
datos externos ni servicios desplegados para ejecutar las pruebas o el sintético.

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
no sustituyen los controles temporales científicos de la tarea 7.

Quedan aplazados: migración de V2, preparación científica, modelos definitivos,
MLflow, DVC y publicación en `datos/resultados/`. Los límites completos están en
[la arquitectura](../docs/architecture/pipeline-e2e.md).

## Adquisición de entradas científicas

`acquisition/contracts.py` define `ReleaseManifest`, `ReleaseFile`, `DataSource`,
`ResolvedFile` y `ResolvedBundle`, con dataclasses inmutables y un Protocol.
`create_source` es el único punto que selecciona proveedor; `resolve_release`
coordina la caché sin conocerlo. El servicio se puede usar desde un nodo Kedro;
pytest comprueba esa integración con archivos temporales. No se registra un
pipeline `acquisition` que dependa de un release real todavía inexistente.

Preparación, entrenamiento y evaluación futuros recibirán **solo ResolvedBundle**:
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
| Hugging Face | `location` es el repo_id; `revision` debe ser un commit completo de 40 hexadecimales. El SDK oficial usa `repo_type="dataset"`, `token=False` y una caché SDK temporal, que se elimina tras copiar al temporal común. |
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
El digest del manifiesto cambia y crea una caché independiente. Los futuros nodos
científicos mantienen su interfaz `ResolvedBundle`.

Esta caché contiene **entradas científicas**; no escribe ni valida resultados
publicados en `datos/resultados/`. El SHA-256 de publicaciones continúa aplazado
a la tarea 13. No se importan módulos de `app/` ni se reutiliza su sincronizador.

Faltan para registrar el primer release público: repo_id y commit reales de HF,
registro versionado de Zenodo, inventario de archivos y rutas, tamaños y hashes
verificados, cobertura temporal y procedencia/licencia confirmadas. No se ha
descargado ni validado un release remoto real. La reproducción real corresponde
a la tarea 15; el manual de operación, a la 17. Todas las pruebas actuales usan
archivos temporales y bloquean conexiones reales, DNS y acceso a publicaciones.
