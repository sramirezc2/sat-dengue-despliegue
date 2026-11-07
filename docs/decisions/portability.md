# Portabilidad — tarea 15 (COMPLETA)

Solo fixtures artificiales. No habilita tarea 16 ni certifica reproducción
científica real. El PR único es [#1](https://github.com/sramirezc2/sat-dengue-despliegue/pull/1).
El usuario autorizó explícitamente publicar los cinco commits hasta `61159d9` y
ejecutar la matriz remota. Ese push normal se completó; no hubo force push, merge
ni PR adicional. El cierre documental posterior permanece local, porque la
autorización enumeró esos cinco commits.

## Evidencia y criterio

Una prueba de encoding/CRLF o un doble de symlink prueba una condición concreta;
no valida Windows. Un recibo identifica exactamente el commit/árbol ejecutados.
Los cambios documentales posteriores no se atribuyen a esa ejecución.

| Entorno | Evidencia real disponible | Estado de tarea 15 |
| --- | --- | --- |
| Mac local | macOS 26.6.2 / Apple M2 Pro / Darwin arm64; Python 3.12.13; uv 0.11.19; revisión 5cb8b98: 463 + 12 específicas, cuatro CLI, 62,61 s, árbol limpio | APROBADA local; recibo en docs/evidence/task15/macos-arm64.json |
| Ubuntu Actions | [run 42424636145](https://github.com/sramirezc2/sat-dengue-despliegue/actions/runs/42424636145), job 128560175842; ubuntu-26.04 x86_64, Python 3.12.16, uv 0.11.19; 463 + 12, cuatro CLI, 147,85 s | APROBADA; ubuntu-actions.json |
| Windows Actions | Mismo run, job 128560175981; imagen windows-2025-vs2026, Windows Server 2025/10.0.26100 AMD64, Python 3.12.10, uv 0.11.19; 463 + 12, cuatro CLI, 230,52 s | APROBADA; windows-actions.json |
| macOS Actions | Mismo run, job 128560176027; imagen macos-26-arm64, macOS 26.7.2 arm64, Python 3.12.10, uv 0.11.19; 463 + 12, cuatro CLI, 121,65 s | APROBADA; macos-actions.json |
| Colab | GCE real Linux x86_64, host 3.13.18; uv administró Python 3.12.13; 5cb8b98, 463 + 12 pruebas, cuatro CLI, 205,31 s, árbol limpio | APROBADA; recibo docs/evidence/task15/colab-x86_64.json |

DEC-006/019 conservan ruleset, revisión independiente y checks verdes antes del
merge. La lista de reviews del PR estaba vacía al inicio; mergeable=true es solo
una condición técnica. Ahora los cuatro checks originales y los tres de matriz
están aprobados sobre `61159d9b96c0bfd76cd1af7b5b6dc9e7cc4d4849`; sus URLs están en
[ci-governance.md](ci-governance.md). El snapshot basal de 1bad249 se conserva;
no se alteran las bitácoras de tareas 1–14.

El clon temporal nuevo de `5cb8b98` instaló su propio entorno desde lock y pasó
los mismos gates: 463 pruebas, 12 específicas, cuatro CLI y hashes exactos,
112,26 s, árbol limpio antes/después. Recibo:
`docs/evidence/task15/macos-clean-clone.json`.

Validaciones externas finales locales: API 28 (una advertencia Starlette), tablero
33, lint sin errores/seis advertencias existentes y build node_server; wrapper
con dos hashes congelados; Pydantic y Zod aceptan dos generados y 22 históricos.
Cuatro workflows YAML y 26 bloques run revisados sintácticamente con Bash donde
aplica; scripts shell válidos. Esto no ejecuta PowerShell ni certifica Windows.
AST de 95 Python/imports, patrones de secretos, tamaños de archivos cambiados,
exclusión de crudos/cachés/stores, 22 JSON idénticos en bytes y diff verificados.

Colab real se ejecutó desde el [notebook operativo de código](https://colab.research.google.com/drive/1uUR3QPnYFV2xO_18-rG5wX-oJ9Z2BZBs),
observando en la UI el backend Google Compute Engine conectado y PASSED. El
kernel anfitrión `google.colab._shell` fue Python 3.13.18; el venv usó Python
3.12.13 administrado por uv. Se transfirió un bundle incremental de 29.020 bytes
con los cuatro commits locales, se aplicó fast-forward y se verificó el SHA
completo. En esa ejecución Colab previa no hubo push, permisos de proveedores
ni Drive montado; la publicación posterior fue autorizada separadamente.
El recibo descargado (3.237 bytes) conserva el UTC de finalización
`2026-11-07T23:13:51.868602+00:00`, 463 pruebas sin fallos/errores/skips, 12
específicas y cuatro advertencias Kedro ya existentes. Todos los gates devolvieron
0. El lock, tres SHA canónicos, tres digests semánticos, hash de métricas y dos
hashes de publicación coinciden exactamente con los recibos macOS local/clon.
Solo se versionan recibos pequeños y esta evidencia textual, sin notebook,
entornos, logs pesados ni artefactos científicos.

**Cierre verificado:** existen ejecuciones verdes de macOS local, Colab real y
matriz nativa Ubuntu/Windows/macOS. Todos los siete checks están completed/success,
sin cancelaciones ni fallos; se revisaron logs y artefactos. Tarea 15 COMPLETA,
15/21, ninguna tarea activa; tarea 16 PENDIENTE.

GitHub hizo checkout del merge temporal del PR
`21346107449ff9fdec5aa425dc2bb75128d16eb6`. Su árbol
`0e9d724682658a4ecd2870b430e28f6eeb237820` es idéntico al de 61159d9:
no se confundió ese checkout con un merge a main. Los recibos locales/Colab
registran 5cb8b98; entre esa revisión y 61159d9 solo cambiaron documentación y
recibos, no código, pruebas, herramientas, workflow ni lock del pipeline.

Los tres ZIP descargados contienen únicamente `receipt.json`; sus SHA-256 se
contrastaron con los digests de la API de GitHub antes de leerlos. Todos registran
árbol limpio antes/después, 463 pruebas sin fallos/errores/skips, 12 específicas,
diez gates con código 0 y cuatro pipelines. Capacidad nativa de symlink disponible
en los tres; la alternativa controlada se ejecutó también. Windows registró dos
advertencias, Ubuntu/macOS cuatro; no afectan los resultados ni los contratos.
Las seis ejecuciones documentadas (incluido clon local) comparten exactamente
lock, tres SHA/digests N=3, métricas y hashes de publicación.

| Artefacto remoto | ID | SHA-256 del ZIP |
| --- | --- | --- |
| pipeline-portability-Ubuntu | 13594821952 | d07ebadbd4a9863eba10a1599e9e34515f8b3ae2e4cff6bc1432881cc7b8beb0 |
| pipeline-portability-Windows | 13594986854 | 7840e8fc188dad16fb3a8f801ce010481f5510fe2fbd860bdd0769b8d9dee8cb |
| pipeline-portability-macOS | 13595301387 | 7a7a83235e6634b950378d4b0316be1509baf49b4f5444780a3c8f6da098ff5e |

Recibos persistentes en `docs/evidence/task15/`; snapshot de siete checks, pasos,
IDs y URLs sin firmar en `github-portability.json`. No se versionan los ZIP ni
URLs temporales firmadas. Los artefactos de Actions tienen retención de 14 días.
API remota: 28 pruebas/una advertencia; tablero remoto: 33, lint sin errores/seis
advertencias existentes, build correcto; contrato remoto: Pydantic/Zod 24 válidos.
La prueba Zod seleccionada del workflow de contrato omite intencionalmente otras
24 pruebas; la suite completa del tablero ejecutó sus 33. No se ocultan omisiones
en las suites de portabilidad, que tienen skipped=0.

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
| Longitud de rutas | Workspaces relativos cortos, TemporaryDirectory y SHA de 64 caracteres. El runner Windows real instaló el venv y pasó N=3/cleanup en sus rutas. No se promete soporte universal de raíces arbitrariamente profundas fuera de los entornos probados. |
| Archivos abiertos y os.replace | Adquisición/canónico cierran streams antes de reemplazar; publicación prepara/cierra archivos antes de promoción. Pruebas existentes cubren corrupción, fallos antes/después de rename y rollback. Ningún cambio especulativo. Windows puede negar reemplazo de un archivo abierto por terceros: el error debe propagarse, sin garantía de recuperación del SO. |
| Atomicidad y locks | Reemplazo por archivo en el mismo filesystem; publicación usa lock exclusivo y rollback de excepciones. No garantiza aislamiento multiarchivo ni recuperación frente a apagado/fallo del filesystem (DEC-018). |
| Orden del filesystem | Conjuntos de nombres/clave y serialización ordenada; glob del colector se convierte en mapping y JSON sort_keys. No se utiliza orden de directorio para ciencia o selección. |
| Timestamps | Reloj operacional UTC explícito; fixture de publicación mantiene fecha congelada. UTC y duración no forman parte del hash científico. |
| Procesos | N=3 usa `sys.executable -m ...` con listas y main guard, sin fork ni herencia implícita de objetos. Workers nuevos y directorios nuevos; guard existente bloquea red, proveedores, publicación, crudos reales y V2. |
| TemporaryDirectory | Contextos cierran procesos/streams antes de cleanup; no se usan nombres de un archivo temporal todavía abierto para reabrirlo en Windows. N=3 copia el certificado fuera del temporal antes de salir. |
| SQLite/MLflow | Backend explícito local opt-in, engine.dispose al cerrar y prueba existente de mover store cerrado/releer. No se cambia la URI ni el SDK por hipótesis; la suite Windows real confirmó los casos existentes de locks, movimiento y cleanup con el store cerrado. |
| Wheels y dependencias | Lock existente conserva 94 resoluciones/hashes. Kedro, MLflow-skinny, jsonschema son universales; NumPy/pandas/SciPy/sklearn/SQLAlchemy/Ruff incluyen wheels de las familias Linux, Windows amd64 y macOS en el lock. La presencia estática se complementó con instalación real desde lock y suite completa en los tres runners nativos y Colab. |
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
La definición fue ejecutada en run 42424636145; los tres checks completaron success y se inspeccionaron sus logs/recibos.
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
