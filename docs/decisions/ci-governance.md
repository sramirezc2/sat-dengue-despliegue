# Gobernanza y CI por componentes

Fecha: 2026-11-07. Cierre de tarea 15: PR [#1](https://github.com/sramirezc2/sat-dengue-despliegue/pull/1)
abierto en `feature/pipeline-e2e`, HEAD remoto `61159d9b96c0bfd76cd1af7b5b6dc9e7cc4d4849`.
Los cinco commits locales fueron publicados con autorización explícita del usuario,
mediante push normal; no hubo merge, force push ni PR adicional.

| Check aprobado | Run real de GitHub Actions |
| --- | --- |
| API tests | [42424636017](https://github.com/sramirezc2/sat-dengue-despliegue/actions/runs/42424636017) |
| Dashboard quality | [42424636020](https://github.com/sramirezc2/sat-dengue-despliegue/actions/runs/42424636020) |
| Publication contract | [42424636002](https://github.com/sramirezc2/sat-dengue-despliegue/actions/runs/42424636002) |
| Pipeline quality | [42424636145](https://github.com/sramirezc2/sat-dengue-despliegue/actions/runs/42424636145) |
| Pipeline portability (Ubuntu) | [42424636145](https://github.com/sramirezc2/sat-dengue-despliegue/actions/runs/42424636145) |
| Pipeline portability (Windows) | [42424636145](https://github.com/sramirezc2/sat-dengue-despliegue/actions/runs/42424636145) |
| Pipeline portability (macOS) | [42424636145](https://github.com/sramirezc2/sat-dengue-despliegue/actions/runs/42424636145) |

Logs revisados y tres artefactos descargados/verificados por SHA-256. Los recibos
registran el merge temporal del PR `21346107449ff9fdec5aa425dc2bb75128d16eb6`,
cuyo árbol coincide exactamente con el HEAD remoto 61159d9; no fue un merge a main.
El snapshot se conserva en `docs/evidence/task15/github-portability.json`.
PR abierto, no fusionado, técnicamente fusionable; lista de revisiones vacía.
Ruleset no verificado en esta consulta. Ruleset, aprobación independiente y checks
verdes sobre la revisión final siguen siendo obligatorios antes del merge.
El cierre documental adicional es local: la autorización de push especificó los
cinco commits hasta 61159d9. No se extiende a ese nuevo commit.
Las referencias posteriores a CI remota pendiente describen evidencia histórica
de tareas anteriores; las notas basales de 1bad249 siguen en
`docs/evidence/task15/github-baseline.json`.
La arquitectura compartida está en [pipeline-e2e.md](../architecture/pipeline-e2e.md)
y el avance en [plan.md](../../plan.md).

## Propiedad y revisión

El propietario inicial verificado es `@sramirezc2` (cuenta GitHub y propietario
del repositorio). `CODEOWNERS` lo asigna a todas las rutas. Los demás integrantes
se agregarán al confirmar sus usuarios y acceso de escritura; no se inventan equipos.
La política exige al menos **una aprobación independiente**, revisión del dueño
del código, conversaciones resueltas y aprobaciones invalidadas si cambia el diff.
El autor no puede aprobar su propio PR: si el autor es el único code owner,
se deberá incorporar otro integrante verificado con escritura antes del merge.

## Checks y comandos

Los nombres de los jobs son los contextos que debe exigir el ruleset:

| Workflow | Check requerido | Validación |
| --- | --- | --- |
| `api-ci.yml` | `API tests` | `python -m pip install -r app/api/requirements-dev.txt`; desde `app/api`, `python -m pytest`. |
| `dashboard-ci.yml` | `Dashboard quality` | Desde `app/dashboard`, `bun install --frozen-lockfile`, `bun run lint`, `bun run test`, `NITRO_PRESET=node_server bun run build`. |
| `publication-contract.yml` | `Publication contract` | Reutiliza `construir_indice` y `RepositorioDirectorio.get` para validar todos los JSON, sus nombres y claves; ejecuta la prueba Zod existente indicada abajo. |
| `pipeline-ci.yml` | `Pipeline quality` | Desde la raíz: `uv lock --check --project pipeline`, `uv sync --locked --project pipeline`, `uv run --directory pipeline ruff check .`, `uv run --directory pipeline pytest` y `uv run --directory pipeline kedro run --pipelines synthetic`. |

La validación del consumidor se ejecuta desde `app/dashboard` con:

```sh
bun run test -- src/test/dashboard-integration.test.tsx -t 'todos los resultados publicados cumplen el contrato'
```

La prueba recorre todos los JSON publicados. El paso Python del workflow usa el
contrato existente, sin copiar esquemas ni lógica científica. La lectura de
resultados históricos de 2025 comprueba compatibilidad; no desarrolla modelos,
no consume datos científicos externos ni convierte 2025 en un holdout intacto.
El contrato no regenera ni certifica científicamente el retroanálisis: un cambio
en `datos/retro/` dispara la validación de las publicaciones existentes.

Los cuatro workflows se ejecutan en PR hacia `main` y permiten `workflow_dispatch`.
Filtran rutas **dentro del job**, conservando un check exitoso explícito cuando
no aplica: filtrar el evento completo dejaría checks requeridos en pendiente.
API cubre `app/api/`, resultados y su workflow; tablero cubre `app/dashboard/`
y su workflow; publicación cubre resultados, retroanálisis, generador, API,
tablero y su workflow. El filtro de publicación es deliberadamente conservador
para incluir schemas, loaders, contratos y configuración sin listas frágiles.
La ejecución manual siempre valida todo el componente; GitHub solo ofrece
`workflow_dispatch` cuando el workflow existe en la rama predeterminada.
Pipeline cubre `pipeline/` y su propio workflow, con el mismo filtro dentro del job.
Instala el entorno propio desde `uv.lock`, verifica su vigencia y ejecuta el E2E
artificial sin datos externos. El comando usa `--directory pipeline` para que
Kedro descubra la raíz del subproyecto; `--project` no cambia el directorio.

Se usan Python 3.12, Node 22 y Bun 1.4.4 (alineado con Docker).
Acciones oficiales verificadas: [checkout v7](https://github.com/actions/checkout),
[setup-python v7](https://github.com/actions/setup-python),
[setup-node v7](https://github.com/actions/setup-node) y
[setup-bun v2](https://github.com/oven-sh/setup-bun).
Permisos: solo `contents: read`; sin secretos, matrices ni cachés añadidas.
`pipeline-ci.yml` se incorpora en la tarea 4 junto con Kedro (DEC-005).
Usa Python 3.12 y [setup-uv v10.3.3](https://github.com/astral-sh/setup-uv/releases/tag/v10.3.3)
con uv 0.11.19 y caché desactivada. `Pipeline quality` se valida localmente;
su ejecución en GitHub Actions continúa pendiente por DEC-006.

## Estado remoto comprobado

Inspección de solo lectura con GitHub CLI el 7 de noviembre de 2026:

- `gh api repos/sramirezc2/sat-dengue-despliegue`: propietario `sramirezc2`, rama
  predeterminada `main`; cuenta disponible con `pull=true`, `push=false`, `admin=false`.
- `gh api repos/sramirezc2/sat-dengue-despliegue/rulesets`: `[]`.
- `gh api repos/sramirezc2/sat-dengue-despliegue/rules/branches/main`: `[]`;
  no hay reglas efectivas de ruleset para `main`.
- `gh api repos/sramirezc2/sat-dengue-despliegue/branches/main/protection`:
  HTTP 404. Con acceso limitado, ese 404 no demuestra por sí solo ausencia de
  protección clásica; no permite verificarla. No acredita los requisitos solicitados.

**Pendiente administrativo antes del merge:** la inspección anterior no encontró
un ruleset activo verificable y la cuenta no puede administrarlo. DEC-006 cerró
la tarea 2 respecto a implementación y validación local, y aplazó la activación
remota hasta publicar el único PR. No se modificó configuración remota ni se
repitió esa inspección en la tarea 4. Los workflows aún no se ejecutaron en
GitHub Actions porque no se ha publicado la rama ni abierto el PR.

## Activación manual exacta por el propietario

Seguir la [guía oficial de creación de rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/creating-rulesets-for-a-repository)
y las [reglas disponibles](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets):

1. En `sramirezc2/sat-dengue-despliegue`, abrir **Settings → Rules → Rulesets →
   New ruleset → New branch ruleset**. Nombre: `main-quality-gates`.
2. Seleccionar **Enforcement status: Active**. Mantener **Bypass list vacía**,
   sin administradores, roles o apps con bypass rutinario.
3. En **Target branches → Add target → Include by pattern**, escribir `main`;
   no agregar exclusiones.
4. Activar **Restrict deletions** y **Block force pushes**.
5. Activar **Require a pull request before merging**; fijar **Required approvals: 1**,
   **Dismiss stale pull request approvals when new commits are pushed**,
   **Require review from Code Owners** y **Require conversation resolution before merging**.
6. Activar **Require status checks to pass** y **Require branches to be up to date
   before merging**. Agregar exactamente `API tests`, `Dashboard quality`,
   `Publication contract` y `Pipeline quality`, con origen GitHub Actions.
7. Guardar con **Create** y volver a consultar las reglas efectivas de `main`.
   Verificar todos los campos anteriores, no solo la existencia del ruleset.

Si los checks no aparecen en el selector, deberán registrarse mediante una
primera ejecución del futuro **único PR**, cuando se autorice publicar la rama;
no se abrirá un PR auxiliar. No desactivar la protección para fusionar.
El merge permanece bloqueado hasta que los cuatro contextos estén exigidos y se
pueda verificar la configuración completa. `CODEOWNERS` se interpreta desde la
rama base: para este primer PR, el propietario deberá revisar explícitamente
el diff aunque todavía no haya solicitud automática de code owner.

Antes del merge: ruleset activo y verificado, cuatro checks verdes en el último
estado del PR, rama actualizada, aprobación independiente válida, revisión de
propiedad y conversaciones resueltas. También deben completarse las tareas
restantes de `plan.md`; esta etapa no autoriza fusionar una implementación parcial.

## Evidencia local y límites

- Pipeline (tarea 4): lock vigente, instalación bloqueada, Ruff, 7 pruebas y
  ejecución Kedro sintética verdes localmente. Se actualizó la CLI a
  `--pipelines`; persisten avisos internos de deprecación de OmegaConf.
  No se ejecutó ni se esperó GitHub Actions (DEC-006).
- API: 22 pruebas verdes; advertencia existente de deprecación de TestClient/httpx.
- Tablero: 33 pruebas verdes; lint sin errores y seis advertencias de Fast Refresh;
  build `node_server` correcto, con advertencia existente sobre tamaño de chunks.
- Publicación: 22 JSON aceptados por la API y prueba Zod sobre todos los publicados verde.
- Bun 1.4.4 probado desde caché local aislada, sin cambiar la instalación global.
  Vitest se ejecuta con Node según su comando normal; forzarlo con `--bun` falló
  al importar Zod y no corresponde al comando configurado en CI.
- `actionlint` no está instalado: no se instaló globalmente. Se validó YAML con
  Ruby/Psych disponible, estructura, permisos, eventos y nombres de checks;
  esto no sustituye actionlint ni una ejecución remota en Linux.
- Se verificaron filtros de rutas, sintaxis shell y el diff; sin cambios de
  producto, datos, dependencias versionadas, scripts, Docker o notebooks.
