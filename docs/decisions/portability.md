# Portabilidad — tarea 15 (EN CURSO)

Solo fixtures artificiales. No habilita tarea 16 ni certifica reproducción
científica real. El PR único es [#1](https://github.com/sramirezc2/sat-dengue-despliegue/pull/1).
No hay autorización de push en este chat; los commits de tarea 15 son locales.

## Evidencia y criterio

Una prueba de encoding/CRLF o un doble de symlink prueba una condición concreta;
no valida Windows. Un recibo identifica exactamente el commit/árbol ejecutados.
Los cambios documentales posteriores no se atribuyen a esa ejecución.

| Entorno | Evidencia real disponible | Estado de tarea 15 |
| --- | --- | --- |
| Mac local | Darwin arm64; Python 3.12.13; uv 0.11.19; línea base 440 y revisión local 463 pruebas verdes | Recibo final pendiente |
| Ubuntu Actions | [run 42421879813](https://github.com/sramirezc2/sat-dengue-despliegue/actions/runs/42421879813), job 128551854736; ubuntu-26.04 x64, Python 3.12.16, uv 0.11.19, 440 pruebas/4 warnings/105 s; cuatro CLI ejecutados | Solo línea base 1bad249, matriz nueva pendiente |
| Windows Actions | Ninguna ejecución de la matriz nueva | BLOQUEO: falta autorización de push y run real |
| macOS Actions | Ninguna ejecución de la matriz nueva | BLOQUEO: falta autorización de push y run real |
| Colab | Notebook de código creado y runtime GCE conectado: Linux x86_64, host Python 3.13.18 | Gates desde lock pendientes; conectar un runtime no equivale a aprobarlos |

DEC-006/019 conservan ruleset, revisión independiente y checks verdes antes del
merge. La lista de reviews del PR estaba vacía al inicio; mergeable=true es solo
una condición técnica. Los cuatro checks originales estaban aprobados sobre
`1bad249e396d2313ad160c6ab21b434cff57c452`; sus URLs están en
[ci-governance.md](ci-governance.md). No se alteran las bitácoras de tareas 1–14.

## Auditoría del código versionado

Revisión de `pipeline/src`, pruebas, herramientas y wrapper; no de entornos ni
cachés. Cada fila distingue evidencia concreta de riesgos todavía no ejecutados.

| Hallazgo | Impacto, tratamiento y evidencia |
| --- | --- |
| Lecturas de texto sin encoding en tracking CLI y pruebas de fuentes/fixtures | UTF-8 interpretado como cp1252 altera `Río`; regresión roja antes del cambio. Encoding UTF-8 explícito en estas lecturas/escrituras; no se cambia el JSON ni el dominio. |
| Escritor histórico de caracterización usa nueva línea nativa | La regresión inyecta CRLF y antes cambiaba ambos hashes congelados. Solo el helper de referencia normaliza transporte al leer UTF-8 con nuevas líneas universales y codificar LF. Producción sigue comparándose en bytes crudos; goldens intactos. No se afirma identidad cruda del escritor histórico CRLF. |
| `core.autocrlf=true` cambia bytes del lock y fuente del schema | Prueba con Git real, repositorio minúsculo y clon nuevo: roja antes de `.gitattributes`. LF explícito solo para `pipeline/**`, wrapper y fuente de contrato API. No se modifica código API ni JSON publicados. |
| Creación de symlinks requiere capacidad/privilegios Windows | Cada guard existente corre en modo nativo y con denegación EPERM controlada. El fallback reconoce solo marcadores de `tmp_path` y resuelve sus prefijos; no modifica código productivo. Errores inesperados se propagan. El recibo mide capacidad nativa por separado. Ningún skip silencioso. |
| Rutas absolutas, `/tmp`, HOME, `~`, separadores | Producción recibe workspaces explícitos y usa pathlib; rutas absolutas entre workers son referencias transitorias, nunca linaje. `/tmp/private` aparece como entrada negativa de prueba. Sin HOME ni `/tmp` obligatorio. `/` en URI lógicas/contratos y nombres relativos no es concatenación de rutas del SO. |
| Permisos, fcntl, señales y Bash | Sin chmod/fcntl/señales POSIX en el pipeline/wrapper. Subprocesos usan listas, sin shell=True. Bash histórico del job Ubuntu se conserva solo allí; matriz ejecuta una línea Python con shell nativa. Git es prerrequisito explícito, ya instalado en runners/Colab. |
| Nombres reservados y case | Inventario aprobado de cinco nombres, UUID/hex y publicaciones usan nombres válidos sin colisiones de case. No se amplía ni restringe el contrato de adquisición por anticipar nombres arbitrarios Windows. Ese espacio de entradas no queda certificado. |
| Longitud de rutas | Workspaces relativos cortos, TemporaryDirectory y SHA de 64 caracteres. No se promete soporte universal de raíces profundas; ejecución Windows pendiente, incluido límite del filesystem y instalación del venv. |
| Archivos abiertos y os.replace | Adquisición/canónico cierran streams antes de reemplazar; publicación prepara/cierra archivos antes de promoción. Pruebas existentes cubren corrupción, fallos antes/después de rename y rollback. Ningún cambio especulativo. Windows puede negar reemplazo de un archivo abierto por terceros: el error debe propagarse, sin garantía de recuperación del SO. |
| Atomicidad y locks | Reemplazo por archivo en el mismo filesystem; publicación usa lock exclusivo y rollback de excepciones. No garantiza aislamiento multiarchivo ni recuperación frente a apagado/fallo del filesystem (DEC-018). |
| Orden del filesystem | Conjuntos de nombres/clave y serialización ordenada; glob del colector se convierte en mapping y JSON sort_keys. No se utiliza orden de directorio para ciencia o selección. |
| Timestamps | Reloj operacional UTC explícito; fixture de publicación mantiene fecha congelada. UTC y duración no forman parte del hash científico. |
| Procesos | N=3 usa `sys.executable -m ...` con listas y main guard, sin fork ni herencia implícita de objetos. Workers nuevos y directorios nuevos; guard existente bloquea red, proveedores, publicación, crudos reales y V2. |
| TemporaryDirectory | Contextos cierran procesos/streams antes de cleanup; no se usan nombres de un archivo temporal todavía abierto para reabrirlo en Windows. N=3 copia el certificado fuera del temporal antes de salir. |
| SQLite/MLflow | Backend explícito local opt-in, engine.dispose al cerrar y prueba existente de mover store cerrado/releer. No se cambia la URI ni el SDK por hipótesis; Windows real debe confirmar locks/cleanup. |
| Wheels y dependencias | Lock existente conserva 94 resoluciones/hashes. Kedro, MLflow-skinny, jsonschema son universales; NumPy/pandas/SciPy/sklearn/SQLAlchemy/Ruff incluyen wheels de las familias Linux, Windows amd64 y macOS en el lock. Presencia estática no certifica instalación: solo los runs reales pueden hacerlo. |
| Encoding de herramientas | El colector escribe JSON en bytes UTF-8; logs binarios conservan salida original, sin depender del encoding de consola. Las herramientas externas Pydantic/Zod ya leen UTF-8 y transmiten JSON escapado. |
| Red y datos | Tests bloquean sockets/DNS, imports inversos y acceso a árboles protegidos; tests de transporte usan clientes falsos. Cuatro CLI tienen configuración sintética explícita; colector adicional reutiliza `enforce_boundaries(synthetic=True)`. Solo instalación de herramientas/paquetes y clon Git usan red. Sin descarga HF/Zenodo/AWS ni credenciales. |

Las tres regresiones iniciales fallaron antes de corregir sus causas; quedaron
verdes después. Los 11 casos adicionales de denegación de symlinks mantienen
cobertura real de guards; 12 pruebas específicas nuevas: 463 pruebas acumuladas.
No cambian dependencias, políticas científicas ni contratos de adquisición,
construcción o publicación. Los 22 documentos publicados permanecen intactos.

## Recibos y ejecución

`pipeline/tools/check_portability.py` invoca lock, sync, Ruff, pytest completo,
suite específica y los cuatro CLI oficiales desde la raíz, secuencialmente y sin
shell. Solo añade `--junitxml` para medir pruebas reales. Requiere árbol limpio
antes/después; un fallo, suite vacía u omisión impide PASSED. Logs y XML quedan
ignorados en `pipeline/data/portability/`; solo `receipt.json` se exporta.

El colector vuelve a ejecutar el smoke y N=3 mediante las APIs existentes para
obtener sus resultados en memoria, además de los cuatro CLI obligatorios. No
reimplementa productores. El recibo incluye versiones, OS/CPU/Python/uv, commit,
árbol, lock SHA, gates/duración, advertencias, capacidad nativa de symlinks,
resultados y hashes. No incluye hostname, HOME, variables completas ni datos.

Identidades exactas que deben conservarse:

- Lock: `353cb1a567ce5038e4d41d9009e40a674603f6a87df198eb8a28116c6093b3cd`.
- Canónico, tres veces: `4ca14c3c07079130606a91274a516e083b513c6a1a7afe41d8df92be9b3bb046`.
- Digest semántico, tres veces: `26cc689566b05ffaf46a42aaa8311cca0ffc3137e31af6f64cfb1e9834f6b957`.
- Publicación: hashes congelados de `pipeline/tests/fixtures/publication_receipt.json`.
- Smoke: MAE=5, MSE=25, una fila artificial; JSON de métricas ordenado/canónico en recibo.

Contratos, esquema, claves y artefactos diseñados byte-estables exigen igualdad
exacta. Se conservan las tolerancias numéricas de tests existentes; no se exige
identidad de modelos serializados ni de timestamps, PIDs, SQLite o entornos.

## Matriz y Colab

Se conserva el job/check `Pipeline quality`. Los nuevos checks son
`Pipeline portability (Ubuntu)`, `Pipeline portability (Windows)` y
`Pipeline portability (macOS)`, con fail-fast=false, Python 3.12, uv 0.11.19,
lock existente, caché deshabilitada, sin secretos/proveedores/datos reales.
Solo se sube un JSON por plataforma durante 14 días, incluso ante gates fallidos.
No se afirma que la definición YAML haya ejecutado esos checks.
La configuración usa la [acción oficial upload-artifact](https://github.com/actions/upload-artifact)
y la [integración oficial uv](https://docs.astral.sh/uv/guides/integration/github/).

`pipeline/tools/colab_runner.py` se llama desde una celda de código. Verifica el
módulo del kernel Colab, exige SHA completo, instala uv==0.11.19 y Python 3.12
administrado por uv si el host difiere. Delega al mismo coordinador; agrega al
recibo el Python anfitrión y el módulo del kernel. Esto complementa la observación
del runtime real; una variable de entorno no es evidencia suficiente.

Para commits locales sin push puede transferirse un bundle Git incremental de
fuentes revisadas desde la referencia pública conocida; fetch + merge --ff-only
conservan identidad del commit. No publica refs remotas ni requiere credenciales.
No se incluyen microdatos, cachés, entornos o stores en el bundle/recibo. El
notebook operativo contiene exclusivamente código; no duplica lógica científica.
