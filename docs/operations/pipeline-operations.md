# Operación del pipeline SAT DENGUE V3

Esta es la entrada operativa para integrantes y agentes. El [manual de
experimentos](../experiments/manual_pipeline.md) es la autoridad para nuevos
entrenamientos, aprobaciones, conclusiones y repeticiones. [plan.md](../../plan.md)
controla tareas/estados; la [arquitectura](../architecture/pipeline-e2e.md) controla
fronteras. Los ejemplos privados de este documento son instrucciones para una
operación futura aprobada: no son autorización para ejecutarlos ahora.

Para escoger una capacidad de agente, usar el
[catálogo de skills](../agents/skills-catalog.md). Los límites científicos y de
exposición se resumen en la [revisión científica](../reviews/scientific-review.md)
y la [revisión de seguridad](../security/security-review.md); ambos documentos
son auditorías cerradas y no sustituyen el estado vigente de `plan.md`.

El [reporte ejecutivo](../reports/pipeline-e2e-executive-report.md) resume
capacidades y limitaciones; esta guía conserva los procedimientos operacionales.

## Directorios y responsabilidades

| Ruta | Responsabilidad |
|---|---|
| `app/` | API de lectura y tablero desplegados, sin Kedro ni dependencias científicas. |
| `pipeline/` | Subproyecto científico independiente, herramientas, configuración y lock. |
| `datos/datos-crudos/` | Entrada privada local ignorada por Git; no es publicación. |
| `pipeline/data/` | Inbox/cachés, canónico, trabajo y recuperación locales ignorados. |
| `datos/resultados/` | Única frontera publicada a la API; los 22 JSON históricos se conservan. |
| `docs/experiments/` | Registro, protocolo, conclusiones y manual. Configuración ejecutable en `pipeline/conf/experiments/`. |
| `docs/evidence/` | Evidencia pequeña y agregada; los paquetes experimentales son exclusivos e inmutables. |

Flujo permitido: `pipeline/ → datos/resultados/ → app/api/ → app/dashboard/`.
El pipeline no importa ni escribe en `app/`. El S3 opcional de la API transporta
JSON ya publicados; no es el origen científico de entrenamiento.

## Preparación desde un clon limpio

Requisitos del proyecto: Python 3.12, uv 0.11.19, Git y, para validar el producto,
Bun/Node según sus workflows y lock. El lock científico no instala bibliotecas
nativas del sistema. En macOS, antes de importar XGBoost, instalar `libomp`
mediante Homebrew (`brew install libomp`), como hace la CI. Ubuntu/Linux y Windows
x64 usan el mismo lock; una distribución sin el runtime OpenMP necesario debe
resolver ese requisito del sistema antes de continuar, sin cambiar la receta.

Clonar la rama existente y ejecutar desde la raíz (terminal macOS/Linux o
PowerShell con estas herramientas disponibles):

```sh
git clone --branch feature/pipeline-e2e https://github.com/sramirezc2/sat-dengue-despliegue.git sat-dengue
cd sat-dengue
git status --short --branch
uv --version
uv lock --check --project pipeline
uv sync --locked --project pipeline
uv run --directory pipeline python -c "import sys, xgboost; assert sys.version_info[:2] == (3, 12); print(xgboost.__version__)"
uv run --directory pipeline ruff check .
uv run --directory pipeline python -m sat_dengue_pipeline.experiment_management validate
uv run --directory pipeline python tools/check_experiment_preservation.py
```

`--directory pipeline` cambia cwd para Kedro; `--project pipeline` solo selecciona
el entorno y se usa en lock/sync o en el wrapper de publicación de la raíz.
Conservar los finales LF y UTF-8 de los archivos identificados por hash. Si un
checkout cambia sus bytes, investigar atributos/EOL antes de recalcular hashes.
No normalizar recibos ni reescribir una receta cerrada para hacer pasar un guard.

En Windows usar rutas relativas del proyecto y PowerShell; no depender de
`pipeline/.venv/bin/python`, una ruta POSIX. Un error CP1252 no se resuelve
ocultando el retorno fallido: conservar logs, usar las lecturas UTF-8 del código
y el runner portable. La matriz actual debe consultarse en el PR: una ejecución
histórica verde no acredita un HEAD nuevo. La auditoría T18 registra el fallo
Windows de checkout de `00c5404`; el gate de cierre exige nueva CI verde.

### Autenticación segura

Solo en una operación privada autorizada, configure un token individual de lectura
en el entorno del proceso. No use login persistente o credenciales cacheadas como
fallback; no escriba el valor en argumentos, archivos, notebooks, logs o prompts.
La entrada siguiente queda oculta y no contiene el secreto en el historial.

PowerShell en Windows:

```powershell
$env:HF_TOKEN = [System.Net.NetworkCredential]::new("", (Read-Host "Token HF de lectura" -AsSecureString)).Password
```

Bash en Linux/macOS:

```bash
read -r -s -p "Token HF de lectura: " HF_TOKEN
export HF_TOKEN
printf '\n'
```

zsh en macOS:

```zsh
read -rs "HF_TOKEN?Token HF de lectura: "
export HF_TOKEN
printf '\n'
```

Al terminar, use `Remove-Item Env:HF_TOKEN` en PowerShell o `unset HF_TOKEN`
en Bash/zsh. El helper retira esa variable del entorno del proceso científico.
El ejemplo de autenticación del manual también es específico de zsh.

### Colab

Usar un clon limpio fuera de Drive y el helper existente
[`pipeline/tools/colab_runner.py`](../../pipeline/tools/colab_runner.py). Desde el
kernel real de Colab, una celda **solo de código**, con el clon disponible,
delega toda la lógica; sustituir el marcador por el SHA completo revisado:

```python
import runpy
from pathlib import Path
run_colab = runpy.run_path("sat-dengue/pipeline/tools/colab_runner.py")["run_colab"]
receipt = run_colab(Path("sat-dengue"), expected_commit="SHA_COMPLETO_REVISADO")
```

El helper valida commit/árbol limpio, instala uv fijado y Python administrado
3.12 si hace falta, y delega al runner común. No copiar transformaciones a
notebooks, montar Drive ni introducir credenciales para los fixtures. Exportar
solo el recibo pequeño. Sintaxis y gates del helper están probados localmente;
la evidencia Colab anterior está en [portabilidad](../decisions/portability.md).
Esta tarea no abrió una sesión Colab nueva ni modificó celdas.

## Flujos y comandos

### Fixtures y canónico

Los defaults de `pipeline/conf/base/parameters.yml` son **synthetic**. Estos
comandos no descargan datos privados ni entrenan modelos científicos reales:

```sh
uv run --directory pipeline kedro run --pipelines synthetic
uv run --directory pipeline kedro run --pipelines canonical_build
uv run --directory pipeline kedro run --pipelines canonical_reproducibility
uv run --directory pipeline kedro run --pipelines deployment_publication
```

`canonical_build` genera un provisional; `canonical_reproducibility` reconstruye
N=3 en procesos/inboxes distintos y libera un solo certificado tras igualdad
exacta. El fixture es de dos municipios y 84 meses, no el panel nacional real.
No sustituir la certificación por escoger una de varias salidas divergentes.

### Canónico aprobado

Con entorno bloqueado y autenticación explícita, desde la raíz:

```sh
uv run --locked --directory pipeline python tools/build_approved_canonical.py
```

Coordina adquisición → `canonical_build` aprobado con el mismo intérprete, listas
de argumentos y cwd del subproyecto; se detiene al primer fallo y devuelve su
código. `--help` no adquiere ni escribe. No usa shell, login implícito o una CLI
científica nueva. Kedro solo recibe rutas locales/metadatos neutrales y no descarga.

DEC-029 fija el default del helper al nuevo release operacional
`173d5856874b89d8aeb0566accc65ce7f6759820`, declarado en
`pipeline/conf/releases/operational-raw-173d5856.json`. Solo cambia la identidad
de integridad del archivo climático. El manifiesto histórico `approved-raw.json`
se conserva byte a byte. DEC-032 unifica el helper, el adquiridor directo y
Kedro real en ese release corregido por defecto; las dos rutas de construcción
seleccionan `operational_full`. La selección se declara una sola vez en
`acquisition/raw_manifest.py`. Para el histórico, usar
`--manifest conf/releases/approved-raw.json --profile approved`. El helper transmite
la misma selección a adquisición y al parámetro `canonical.manifest`; las cachés se
separan por `release_id` y digest del manifiesto. DEC-031 añade el perfil
canónico completo; T16 mantiene manifiesto, perfil y configuración históricos.

El helper recomendado selecciona ahora `operational_full`: 1.122 municipios ×
216 meses, `2007-01`–`2024-12`, 242.352 claves. El perfil histórico `approved`
permanece explícito, con 163 meses y 182.886 claves. No se aceptan fechas libres.
Ambos conservan reserva `2025-01` y comparten nodos/productores. El constructor
Kedro real usa `operational_full` cuando no se especifica `canonical.profile`;
el helper transmite su selección explícitamente. Sin `canonical.mode=approved`,
Kedro conserva el modo sintético predeterminado.

Para reproducir el perfil histórico desde su release original:

```sh
uv run --locked --directory pipeline python tools/build_approved_canonical.py --manifest conf/releases/approved-raw.json --profile approved
```

Para seleccionar el completo directamente en Kedro después de adquirir su caché:

```sh
uv run --locked --directory pipeline kedro run --pipelines canonical_build --params canonical.mode=approved,canonical.profile=operational_full,canonical.manifest=conf/releases/operational-raw-173d5856.json,canonical.workspace=data/canonical-full-manual,canonical.tracking=false
```

El helper produce un provisional; la certificación N=3 se ejecuta separadamente
sobre crudos verificados, con tres procesos/directorios y sin reutilizar derivados.
La cobertura cruda declarada operacional comienza en `2007-01-01` y termina en
`2025-12-31`; la salida canónica termina en `2024-12`. La ventana de entrenamiento
sigue desde `2018-01`, sin adelantar cinco roles o evaluación. El arnés rolling
mantiene primer origen `2019-01`; T16 mantiene primer objetivo de evaluación
`2024-01` (orígenes `2023-12` para T+1 y `2023-11` para T+2).
No se autoriza entrenamiento ni se crea EXP003 al construir o certificar.

Las dos etapas manuales equivalentes al comando único permiten aislar fallos:

```sh
uv run --locked --directory pipeline python tools/acquire_private_raw.py
uv run --locked --directory pipeline kedro run --pipelines canonical_build --params canonical.mode=approved,canonical.workspace=data/canonical-approved-manual,canonical.tracking=false
```

Ambas etapas seleccionan `satd-raw-173d5856` y `operational_full` por defecto.
Una caché solo histórica produce un error accionable, nunca una sustitución
silenciosa. Para reproducir el histórico mediante las dos etapas:

```sh
uv run --locked --directory pipeline python tools/acquire_private_raw.py --manifest conf/releases/approved-raw.json
uv run --locked --directory pipeline kedro run --pipelines canonical_build --params canonical.mode=approved,canonical.manifest=conf/releases/approved-raw.json,canonical.profile=approved,canonical.workspace=data/canonical-historical-manual,canonical.tracking=false
```

`VERIFIED` requiere el inventario físico exacto y la integridad de los cinco
archivos, conforme al preflight y validador que usa Kedro. Antes de escribir
crudos se rechazan enlaces en raíz, ancestros y archivos de caché. Los faltantes
y corruptos pueden recuperarse por adquisición; los adicionales se informan y
conservan, sin borrado automático. Los errores que recomiendan adquirir incluyen
el `--manifest` solicitado, también para una selección histórica explícita.
No se incluyen nombres privados de archivos adicionales en el diagnóstico.

El helper crea un workspace relativo único `pipeline/data/canonical-approved/<id>`;
el comando manual usa un workspace explícito distinto. El modo predeterminado de
Kedro sigue siendo sintético: no omita `canonical.mode=approved` en el diagnóstico real.
**La salida es provisional**, no certificada ni entrenable automáticamente. No se
invocan N=3, entrenamiento, experimentos o publicación. No ejecutar estos comandos
privados como parte de validación rutinaria ni repetir la ciencia cerrada de T16.

Cada adquisición escribe `pipeline/data/acquisition/<id>/receipt.json`, exclusivo,
UTF-8 e ignorado por Git, con estado, duración, hashes permitidos y tipo de error
sanitizado. Conserva intentos fallidos sin tocar `docs/evidence/`. No admite destino
arbitrario. Ante falta de permisos/espacio se devuelve `ReceiptError`; un filesystem
fallido puede impedir guardar el recibo y exige investigar, sin borrar historia.

El preflight reconoce caché inexistente, ruta no directorio, faltantes, adicionales
y enlaces de caché/ancestros/archivos. La integridad (tamaño/SHA, encabezados y
procedencia) sigue en `raw_contract_validation`. Ningún productor se inicia si
falla la entrada; los errores no muestran rutas absolutas o excepciones externas.
Ante ausencia/faltantes, ejecute el adquiridor indicado; ante adicionales revise
el inventario antes de mover nada; ante corrupción confirme el manifiesto y haga
una readquisición autorizada, sin aceptar hashes nuevos por conveniencia. Kedro
no borra ni repara automáticamente la caché.

### Recursos medidos

El bundle contiene **2.614.987.120 bytes** (aproximadamente 2,615 GB / 2,435 GiB).
Reserve además espacio para temporales, cachés y derivados; la cifra del bundle
no es una garantía de espacio total. Las siguientes son mediciones históricas,
no tiempos ni memoria garantizados para otro equipo o release:

| Procedimiento real T16 | Tiempo observado | Pico RSS por proceso | Fuente |
|---|---:|---:|---|
| Adquisición validada | 43,63 s | No medido en este recibo | [acquisition.json](../evidence/task16/acquisition.json) |
| Construcción directa | 258,45 s | 9,84 GiB | [build-real.json](../evidence/task16/build-real.json) |
| Construcción Kedro | 258,17 s | 12.259.475.456 bytes | [kedro-real.json](../evidence/task16/kedro-real.json) |
| Certificación canónica N=3 histórica | 757,55 s; workers 248,25 / 248,30 / 248,76 s | Máximo 11,43 GiB por worker | [certify-real.json](../evidence/task16/certify-real.json) |

Estas medidas reales proceden del [entorno T16](../evidence/task16/resources.json):
macOS 26.6.2 ARM64 con **32 GiB** de RAM. El controlador N=3 midió por separado
1.273.790.464 bytes RSS. RSS por proceso no equivale al consumo total de la máquina.
El código lee bloques pero concatena DataFrames y materializa clima diario:
**no tiene memoria constante**. **8 GB no están acreditados**; la evidencia tampoco
establece 16 o 32 GB como mínimo universal. No paralelice construcciones reales
para intentar acelerar sin evaluar recursos.

Como referencia de otros equipos, T15 midió `canonical_build` **sintético**:

| Entorno | Tiempo del fixture | Procedencia |
|---|---:|---|
| macOS ARM64 local | 1,46 s | [macos-arm64.json](../evidence/task15/macos-arm64.json) |
| macOS ARM64 Actions | 3,55 s | [macos-actions.json](../evidence/task15/macos-actions.json) |
| Ubuntu x86_64 Actions | 2,12 s | [ubuntu-actions.json](../evidence/task15/ubuntu-actions.json) |
| Windows AMD64 Actions | 2,67 s | [windows-actions.json](../evidence/task15/windows-actions.json) |
| Colab Linux x86_64 | 2,63 s | [colab-x86_64.json](../evidence/task15/colab-x86_64.json) |

Los recibos identifican sus commits y entornos. Son fixtures, no benchmarks del
bundle privado ni una comprobación nativa del helper nuevo. No extrapolar sus
tiempos al canónico nacional. La portabilidad remota de los commits locales nuevos
se verificará en T26 después de una publicación autorizada.

### Experimentos

El [manual](../experiments/manual_pipeline.md) describe los archivos, hashes,
revisión humana y recetas válidas. Esta tabla solo ubica la interfaz; `EXP003`
es un identificador ilustrativo nuevo, no una receta existente autorizada:

| Etapa | Comando desde raíz |
|---|---|
| Registrar propuesta preparada | `uv run --directory pipeline python -m sat_dengue_pipeline.experiment_management register --entry docs/experiments/EXP003/registration.yml` |
| Aprobar después de revisión | `uv run --directory pipeline python -m sat_dengue_pipeline.experiment_management transition EXP003 APPROVED` |
| Ejecutar aprobado | `uv run --directory pipeline kedro run --pipeline experiment_run --params experiment_id=EXP003` |
| Cerrar con conclusiones válidas | `uv run --directory pipeline python -m sat_dengue_pipeline.experiment_management transition EXP003 COMPLETED --result INCONCLUSIVE` |
| Comparar agregados | `uv run --directory pipeline python -m sat_dengue_pipeline.experiment_management compare --horizon 2 --candidate xgboost_onset` |

No ejecutar EXP001/EXP002 o `factory_validation`: son evidencia cerrada. Para una
repetición, seguir el manual y obtener otro ID aprobado. Un cálculo exitoso deja
el experimento RUNNING esperando conclusiones; el recibo de ejecución puede estar
COMPLETED. Los terminales fallidos no se convierten en éxito ni autorizan reintento.
Los hashes identifican bytes; no prueban por sí solos calidad de una hipótesis.
La configuración nativa efectiva de XGBoost también se coteja después del ajuste.

### Herramientas auxiliares históricas y preservación

`reproduce_private_raw.py` conserva explícitos `approved-raw.json` y el perfil
`approved` (`2011-06`–`2024-12`); no selecciona el operacional completo.
Solo bajo autorización para repetir la operación privada, estos comandos usan
la caché local verificada, sin adquisición:

```sh
uv run --locked --directory pipeline python tools/reproduce_private_raw.py build
uv run --locked --directory pipeline python tools/reproduce_private_raw.py certify
```

Cada invocación reserva `pipeline/data/private-raw-<fase>-<id>/`. Allí quedan
`<fase>-real.json`, la referencia `<fase>-artifact.json` y los artefactos de ese
intento; el recibo indica `workspace` relativo al subproyecto y el estado
`PASSED`/`FAILED`. Se conserva el fallo incluso si no se resolvió la entrada.
El observador entrega metadatos sin persistir en el store compartido de tracking.
No se reabren carpetas anteriores ni se escribe en `docs/evidence/task16/`.
`certify` ejecuta N=3: no forma parte de una comprobación rutinaria ni de esta
reparación. Estos recibos auxiliares no sustituyen la certificación fijada en
una receta de `experiment_run`.

Para validar el resultado de una certificación histórica nueva, sustituir el
marcador `<id>` por el `workspace` informado por `certify`:

```sh
uv run --locked --directory pipeline python tools/validate_private_canonical.py --certification data/private-raw-certify-<id>/certify-real.json --artifact data/private-raw-certify-<id>/certify-artifact.json
```

Sin opciones, el validador lee el recibo cerrado
`docs/evidence/task16/certify-real.json` y la referencia local antigua
`pipeline/data/task16-real/certify-artifact.json`. Ambas entradas siguen siendo
solo de lectura. Cada intento escribe un `canonical-quality.json` nuevo bajo
`pipeline/data/private-canonical-validation-<id>/`, incluso ante fallo. La
validación reutiliza carga, roundtrip y guards temporales; no entrena ni certifica
N=3 de nuevo. Las referencias locales a artefactos no se versionan ni publican.
Un error al reservar o escribir la salida devuelve código 1 y `ReceiptError`;
se rechazan enlaces en la ruta de salida antes de escribir.

El control de preservación no ejecuta ciencia y compara los 49 archivos
protegidos, 22 JSON e identidad N=3 de T16 con el snapshot versionado. Las rutas
relativas se comparan en formato POSIX también en Windows, y las comprobaciones
siguen activas con Python optimizado:

```sh
uv run --locked --directory pipeline python tools/check_experiment_preservation.py
uv run --locked --directory pipeline python -O tools/check_experiment_preservation.py
```

Una discrepancia produce código no nulo; no recalcular el snapshot para aceptar
una alteración. La evidencia cerrada se conserva byte a byte para consulta.

### Publicación y contratos

`experiment_run` no promociona ni publica modelos. El publicador consume panel,
predicciones y comparación locales aprobados; no convierte automáticamente los
agregados de una ejecución en un resultado municipal. El wrapper compatible tiene
esta interfaz, comprobada mediante `--help` y fixtures:

```sh
uv run --project pipeline python scripts/construir_resultados.py --help
```

Requiere `--panel`, `--predicciones`, `--comparacion`, `--procedimiento` y
`--version-datos`; admite `--generado`, `--candidato`, `--retroanalisis` y
`--justificacion`. Para revisar, fijar explícitamente
`--salida pipeline/data/publication-review/results`, fuera de la publicación
vigente. El [procedimiento de publicación](../decisions/deployment-publication.md)
y [README del pipeline](../../pipeline/README.md#publicación-del-despliegue-tarea-14)
son la autoridad sobre formato de entradas, staging, validación y promoción.
Publicar en `datos/resultados/` necesita autorización; esta tarea no reemplaza
ninguno de sus JSON.

Después del fixture de publicación, validar ambos consumidores. En macOS/Linux,
con dependencias de API instaladas en el Python de la terminal:

```sh
uv run --directory pipeline python tools/validate_publication_consumers.py --directory data/deployment-publication/results --directory ../datos/resultados --api-python "$(python -c 'import sys; print(sys.executable)')"
```

En PowerShell, obtener el intérprete de API explícitamente:

```powershell
$satdApiPython = python -c "import sys; print(sys.executable)"
uv run --directory pipeline python tools/validate_publication_consumers.py --directory data/deployment-publication/results --directory ../datos/resultados --api-python $satdApiPython
```

El destino del fixture vive bajo `pipeline/data/`; los 22 archivos existentes
solo se leen para contratos/regresiones, sin uso científico de 2025.

## Gate de producto

Desde raíz instalar las dependencias de desarrollo de API con
`python -m pip install -r app/api/requirements-dev.txt`. Las dependencias
científicas quedan únicamente en el lock de `pipeline/`.

En macOS/Linux:

```sh
(cd app/api && python -m pytest)
(cd app/dashboard && bun install --frozen-lockfile && bun run lint && bun run test)
(cd app/dashboard && NITRO_PRESET=node_server bun run build)
uv run --directory pipeline pytest
git diff --check origin/main...HEAD
git status --short
```

En PowerShell usar los mismos programas, con cambios de cwd/env explícitos:

```powershell
Push-Location app/api
python -m pytest
Pop-Location
Push-Location app/dashboard
bun install --frozen-lockfile
bun run lint
bun run test
$env:NITRO_PRESET = "node_server"
bun run build
Remove-Item Env:NITRO_PRESET
Pop-Location
```

Para recoger un recibo completo de portabilidad desde un árbol limpio:
`uv run --directory pipeline python tools/check_portability.py`. Incluye suites
y cuatro CLI artificiales; no sustituye la consulta de checks nativos del PR.

## Release crudo y autenticación

La operación por defecto usa
[`operational-raw-173d5856.json`](../../pipeline/conf/releases/operational-raw-173d5856.json),
con revisión inmutable y cinco nombres/tamaños/SHA-256. El histórico
[`approved-raw.json`](../../pipeline/conf/releases/approved-raw.json) permanece
explícito e intacto, con el inventario de
[plan.md §4.1](../../plan.md#41-contrato-crudo-aprobado-para-la-tarea-13): DIVIPOLA y
su procedencia, dengue, dengue grave y clima completo de 18 columnas. Excel,
clima recortado, canónicos remotos, matrices y revisiones mutables se rechazan.
Nunca distribuir públicamente microdatos epidemiológicos completos.

El [manual](../experiments/manual_pipeline.md#preparar-el-entorno) explica el
secreto de entorno; su ejemplo de lectura interactiva es de zsh. En otras
terminales usar el mecanismo local de secretos del equipo. No poner el valor en
argumentos, historial, archivos, notebooks, logs ni prompts. No imprimir el entorno
ni recurrir a login/token cacheado para sortear un fallo. En esta tarea no se
consulta ni usa HF_TOKEN. El adaptador actual verifica privacidad/SHA con la
credencial explícita antes de resolver el release.

La caché común vive bajo `pipeline/data/01_raw/`, por release y digest de
manifiesto. Cada hit verifica tamaño/hash; las descargas van a temporal y solo se
promueven con integridad aprobada. La tabla canónica es un derivado local
reconstruible: cuarentena antes de productores, guards V3, tipos/nulos y hashes.
Los consolidados históricos no prueban disponibilidad en tiempo real.

## Recuperación y troubleshooting

Investigar y conservar recibos antes de borrar, editar, repetir o quitar locks.

| Síntoma | Acción segura |
|---|---|
| Descarga interrumpida | Revisar retorno y espacio; conservar la copia previa. El resolver descarta su temporal y solo promueve bytes verificados. Reintentar transporte únicamente bajo autorización vigente, sin iniciar otro aprendizaje accidental. |
| Hash incorrecto | Contrastar manifiesto/versión y EOL. No actualizar el hash para aceptar bytes desconocidos ni usar un canónico alternativo. La copia corrupta previa no se expone como válida. |
| Receta/protocolo alterado | Revisar diff contra Git y aprobación. Restaurar solo con revisión humana; una receta ya ejecutada no se modifica. |
| No APPROVED | Detenerse: registrar, revisar y aprobar según manual; no editar estado a mano. |
| Evidencia incompleta | Inventario ausente/incorrecto impide cierre/comparación. Conservar carpeta; ante fallo de escritura buscar `pipeline/data/experiments/<execution_id>/evidence-failure.json`. Nunca completar campos inventados. |
| Lock abandonado | Confirmar proceso/etapa y que no hay otro escritor antes de cualquier retirada manual. Un lock persistente no acredita por sí solo que esté abandonado. |
| BLOCKED/FAILED/KILLED | Leer etapa, tipo y agregados de validación, sin publicar excepciones/entorno privados. No convertir el terminal en COMPLETED. Nueva ejecución requiere nuevo ID y aprobación. |
| MLflow ausente | Instalar el grupo fijado del lock: `uv sync --locked --no-dev --group tracking --project pipeline`. La ejecución registrada falla explícitamente sin SDK; no simular tracking. |
| SQLite/MLflow dañado | Conservar store y evidencia Git; la historia se reconstruye desde registro, protocolos, conclusiones e inventarios. No existe un comando de reparación/replay automático: obtener revisión antes de recuperar/copiar/retirar el store. |
| Rutas o encoding | Ejecutar desde raíz con `--directory`, conservar UTF-8/LF y usar rutas relativas. No copiar rutas POSIX de un venv a Windows ni ocultar la causa del gate. |
| Falta de memoria | T16 midió hasta 11,43 GiB RSS por worker en equipo de 32 GiB; no acredita 8 GiB ni memoria constante. Revisar recibos/recursos antes de operar; no paralelizar construcciones reales ni reducir fuentes/soportes para hacerlas caber. |
| Colab desconectado | Verificar persistencia del clon/cache y recibo FAILED/incompleto al volver. Una VM nueva no conserva necesariamente archivos. No relanzar una identidad cerrada ni repetir automáticamente la reproducción privada. |

## Límites y migración de almacenamiento

No hay promoción/champion automático ni inferencia operativa en línea. 2025 es
evidencia consumida, no holdout independiente. MLflow es un índice local; una
comparación de métricas no establece equivalencia científica. Las restricciones
de baselines, incertidumbre, latencias y complete-case se detallan en
[la auditoría científica](../reviews/scientific-review.md).

Hugging Face es el origen privado fijado actual. Zenodo será una copia académica
futura: el adaptador existente es público y no acredita privacidad; no se pueden
subir allí los CSV completos bajo la configuración actual. S3 tiene solo un
cliente inyectado y pruebas simuladas; no hay backend AWS científico operativo.

Una migración aprobada cambia **adaptador, manifiesto y configuración**, manteniendo
los cinco tamaños/hashes y el contenido exacto. Requiere comprobar identidad y
privacidad del nuevo transporte, control de acceso/ownership, cifrado, auditoría
y recuperación de acceso. El soporte de privacidad que hoy solo admite HF debe
extenderse dentro de adquisición antes de habilitar otro remoto privado. No
cambiar canónico, roles, preparación, entrenamiento, calibración ni evaluación.
Las pruebas comunes de adquisición y de identidad deben seguir pasando. No se
aprovisionan buckets ni se mueven datos reales en esta tarea.

## Verificación de esta guía

Interfaz contrastada con ayuda de Kedro, CLI experimental, publicador y validador
de consumidores; modos privados y Colab inspeccionados en código/pruebas. Se
verificaron los cuatro CLI artificiales y los contratos de consumidores. Los
comandos de aprobación, entrenamiento real, publicación vigente y recuperación
privada no se ejecutaron. [Recibo de validación](../evidence/task19/operations-validation.json).

### Correcciones operativas T22–T24

El helper y los errores/recibos se verificaron con dobles y fixtures pequeños,
gate local acumulado y checkout limpio en una ruta con espacios. Se conservó por
hash toda evidencia previa y el producto. El [recibo de T24](../evidence/task24/operational-validation.json)
identifica el código validado y sus límites. No se adquirieron datos privados ni
se reconstruyó el canónico real. CI nativa de estos commits queda para T26 tras
autorización de publicación; el cierre local no autoriza merge.

La publicación posterior autorizada y la primera CI del código operacional constan
en el [recibo T26](../evidence/task26/publication-validation.json). Cada cierre
documental requiere verificar nuevamente su HEAD; `plan.md` controla el estado.
