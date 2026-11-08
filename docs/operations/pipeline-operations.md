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

El modo `canonical.mode=approved` consume una caché real ya verificada del
manifiesto aprobado, sin descargar desde el nodo científico. Su sintaxis y
confinamiento están en `pipelines/canonical/nodes.py:build_input`; **no ejecutarlo
ni repetir la certificación real T16 como diagnóstico rutinario**. El esquema,
las identidades y los recursos reales están en
[la reproducción histórica](../decisions/task16-reproduction.md).

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

La autoridad es [`approved-raw.json`](../../pipeline/conf/releases/approved-raw.json),
revisión inmutable y cinco nombres/tamaños/SHA-256 de
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
