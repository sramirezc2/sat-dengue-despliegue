# Verificación de priorización configurable en Streamlit

Fecha: 2026-11-21. Verificación de software con datos artificiales, no evidencia
científica nueva ni aprobación sanitaria.

Estado de esta segunda iteración: **PASS local**. Preservación resuelta con
procedencia, demo y suite completa aprobadas. Cierre mediante dos commits locales
coherentes, sin publicación. Alojamiento público y evidencia visual diferidos.

## Revisión y alcance

`git fetch origin main` confirmó como base
`2debfb4e3297755bd62fcff1b0ae2bbef3e62172`. Rama local:
`feature/streamlit-configurable-prioritization`, creada desde `origin/main`.
El trabajo existente se conservó y auditó. El cierre se identifica mediante los
commits locales de esta rama; no se hace push, PR ni merge. El informe pertenece
al commit de implementación que lo contiene, sin autorreferenciar su propio SHA.
La corrección de identidad del registro está en el commit local `f923cc6`;
el segundo commit conserva e integra las mejoras de Streamlit y el mecanismo de contexto.

Aplicabilidad: el presupuesto configurable actúa después del orden científico;
no cambia coeficientes, escaladores, predictores aprobados, receta, población,
elegibilidad, desempate ni publicación. No se ejecutaron experimentos científicos reales, ajustes del modelo aprobado,
adquisiciones privadas, reconstrucciones de contexto o publicaciones reales.
Las suites sí ejercitan ajustes y publicaciones con fixtures artificiales aislados.
`prioritize` conserva cupo ocho y rechazo previo a scoring si no alcanza.
`rank_eligible` comparte exactamente su núcleo de validación/ordenamiento y
permite informar pocos o ningún elegible en la demo. La selección posterior es
una función pura que solo añade un booleano sobre posiciones existentes.

La configuración solo cambia ubicaciones. El SHA del modelo está fijado en
código y el cargador científico permanece intacto. Se valida el contexto entero
antes de ofrecer inferencia. La sesión conserva ranking; la caché compartida
contiene únicamente modelo y contexto, no cargas de visitantes.

## Archivos del cambio

- `.github/workflows/pipeline-ci.yml`: detección de `demo/`, entorno aislado,
  Ruff y ejecución explícita de `demo/tests`.
- `README.md`: identificación de entrega final/legado, instalación, flujo,
  entrada/salida, configuración, muestras y limitaciones.
- `demo/app.py`: selector, conteos, advertencias, descargas, selección en tabla/mapa.
- `demo/inferencia.py`: carga configurada/verificada, ranking sin selección,
  funciones puras de cupo/selección/advertencia.
- `demo/configuracion.py`: resolución segura de directorios y archivos locales.
- `demo/contexto_paquete.py`: ZIP offline determinista y bootstrap HTTPS/caché
  con el mismo sistema de rutas y el cargador de contexto existente.
- `demo/ejemplos.py`: plantilla y muestra artificial deterministas.
- `demo/requirements.lock`: transitivas de la demo con versiones/hashes,
  compatibles con las dependencias compartidas del lock científico.
- `demo/tests/conftest.py`, `demo/tests/test_inferencia.py`,
  `demo/tests/test_app.py`, `demo/tests/test_contexto_paquete.py`: regresiones,
  transporte loopback, caché y smoke nativo/HTTP.
- `pipeline/src/sat_dengue_pipeline/risk/inference.py`: extracción del núcleo
  compartido, sin duplicar ordenamiento ni modificar la selección histórica.
- `docs/decisions/risk-2025-preservation.json`: solo el literal del registro,
  justificado mediante historial y main limpio.
- `docs/reports/streamlit-registry-audit.md`: diagnóstico independiente del gate.
- `docs/operations/streamlit-demo.md` y este informe: operación y verificación.

## Criterios de aceptación

Los nombres siguientes pertenecen a `demo/tests/test_inferencia.py`, salvo que
se indique `test_app.py`.

| # | Criterio | Evidencia de software |
| --- | --- | --- |
| 1 | Default 10 % selecciona ocho | `test_capacity_keeps_ranking_without_scoring`, `test_app.py::test_sample_budget_and_restart` |
| 2 | 5/10/15/20 % → 4/8/12/16 | Parametrización de `test_capacity_keeps_ranking_without_scoring` y recorrido UI |
| 3 | Posiciones invariables | Igualdad exacta de todas las columnas salvo selección; scoring prohibido/contador igual a uno al cambiar capacidad |
| 4 | Coincidencia con selección histórica | `test_default_matches_historical_selection`; cotejo adicional contra implementación original del SHA base |
| 5 | Ineligibles nunca seleccionados | `test_priority_order`, `test_priority_with_insufficient_eligible` |
| 6 | Déficit sin reposición, con advertencia | Casos 0/5/7 elegibles; `test_app.py::test_insufficient_eligible_warning` comprueba advertencia y 71 exclusiones con motivo |
| 7 | Empates por DIVIPOLA | `test_priority_order` con predictores idénticos; regresión determinista del pipeline, incluida permutación de filas |
| 8 | Sin puntuación/probabilidad pública | Esquema exacto del DataFrame en `test_capacity_keeps_ranking_without_scoring`; comprobación UI y mapa generado solo desde posiciones/selección |
| 9 | Defaults locales conservados | `test_default_directories`: modelo real versionado; fallback de contexto ejercitado con paquete artificial, sin necesitar contexto privado |
| 10 | Variables de rutas funcionan | `test_configured_directories`: copia íntegra del modelo, contexto artificial y ruta relativa independiente del cwd |
| 11 | Hash incorrecto rechazado | `test_configured_model_rejects_tamper`: bytes distintos y luego manifiesto sustituido, ambos rechazados |
| 12 | Contexto alterado/release ajeno rechazados | `test_context_checks_digest`, `test_context_rejects_other_release`, índice inválido, mes ajeno, enlaces y error sanitizado en UI |
| 13 | Plantilla completada procesable | `test_template_and_artificial_sample_end_to_end` |
| 14 | Muestra recorre todo el flujo | Misma prueba y AppTest: 24 registros, seis municipios, ambos departamentos/eventos, contexto artificial verificado y modelo aprobado |
| 15 | Publicación y presupuesto ocho intactos | Igualdad con `prioritize`, `procedure()["budget"] == 8`, cotejo original y preservación byte a byte descrita abajo |

Comparación adicional con `prioritize` original obtenido con `git show` del SHA
base: diez comprobaciones (muestra/cero, empates/valores distintos, orden
original/permutado y déficit). Ocho devolvieron filas y digest exactamente
iguales; dos rechazaron el déficit con la misma excepción. No se imprimieron
puntuaciones, predictores reales ni probabilidades.

## Gates locales

Python 3.12.13, uv 0.11.19, Streamlit 1.67.0, pytest 9.2.0 y Ruff 0.17.4
en el entorno bloqueado de demo/pipeline. Bun local 1.4.0, frente a 1.4.4 fijado
en CI; instalación del dashboard con lock congelado.

| Comando o comprobación | Resultado |
| --- | --- |
| `uv lock --check --project pipeline` | PASS, lock científico sin cambios |
| `uv sync --locked --project pipeline` | PASS |
| Entorno demo nuevo + `uv pip install --require-hashes -r demo/requirements.lock` | PASS |
| Entorno adicional limpio `--no-dev`, instalación de ambos locks y recorrido AppTest | PASS, muestra/inferencia/cupos 4/8/12/16 sin dependencias de desarrollo |
| `uv run --locked --directory pipeline ruff check .` | PASS |
| Ruff con configuración del pipeline sobre Python cambiado de demo/tests | PASS |
| `demo/.venv/bin/python -m pytest demo/tests -q` | 64 PASS; incluye AppTest y dos arranques de procesos con salud/página HTTP y reinicio |
| Revalidación final de UI y mecanismo tras ajustar el mensaje al usuario | 28 PASS, sin skips; los otros 36 casos de demo no cambiaron |
| Pytest focalizado: `test_risk_2025.py` y `test_private_tool_preservation.py` | 72 PASS; inferencia, configuración, modelo congelado y preservación normal/-O |
| `uv run --locked --directory pipeline pytest` | 896 PASS, sin skips, 462,43 s; seis avisos heredados de OmegaConf |
| API `.venv/bin/python -m pytest` | 54 PASS; aviso heredado de deprecación httpx/Starlette |
| Dashboard `bun install --frozen-lockfile`, lint, test, build con `NITRO_PRESET=node_server` | PASS; 72 PASS/1 skip condicionado a respuesta E2E externa, seis avisos heredados de Fast Refresh y aviso de plugin tsconfig de Vite |
| `kedro run --pipelines synthetic` | PASS, cinco nodos, datos artificiales |
| `experiment_management validate` | VALID |
| `check_experiment_preservation.py`, normal y `python -O` | PASS después de corregir un único pin obsoleto, con diagnóstico independiente |
| Preservación de tarea contra SHA inicial | PASS: 196 archivos protegidos sin cambios, incluidos modelo, evidencia, configuraciones y publicaciones |
| `git diff --check origin/main...HEAD` y `git diff --check` | PASS; la segunda comprobación incluye los cambios sin commit |
| Enlaces locales nuevos y tamaños | PASS; ningún dato privado, modelo nuevo ni archivo pesado añadido |

Los logs y recibos agregados de software están en
`pipeline/data/demo-validation/`, ignorados por Git. La instalación limpia usó
un contexto artificial separado, nunca el directorio privado predeterminado.
En esta iteración se verificó además el entorno mínimo sin pytest/dependencias
de desarrollo, con los doce contextos artificiales y todos los cupos. AppTest
usa rutas absolutas; las pruebas versionadas pasaron con su límite de 15 s.
No se acredita CI remota ni validación nativa Windows/macOS de GitHub Actions.

## Preservación y resolución del fallo preexistente

Las 49 protecciones originales coinciden con su snapshot. Los 22 JSON históricos
conservan el digest agregado
`4d3ddd3890a6a622b658fc2b1ef0159d0da6bc855cacc2c5b62854290623e16e`.
El snapshot extendido verifica 126/127 archivos; el único desacuerdo es
`docs/experiments/registry.yml`, idéntico byte a byte a `origin/main` y al estado
inicial de esta tarea:

- SHA actual y de main: `7421fe9f914883b8be9ec2a777a9e2418a580a52b50bc732be838cba15fee1a0`.
- SHA esperado por el snapshot: `8f0740dc4657519746384d44ce47f93bf1f2dcc0e9d595469254281333416e37`.

El fallo se reprodujo con el mismo comando en un worktree detached limpio de
`origin/main`, con registro, script y snapshot idénticos. El historial demuestra
que el PR #15 (`c1d364d`) agregó EXP315 después de congelar la expectativa en
`00fd0e8`, preservando EXP001/EXP002. Se cotejaron también los hashes de protocolo
y configuración. Se actualizó únicamente el literal del registro; los otros
126 pins, las 49 protecciones originales, los 22 JSON y los recibos permanecen
intactos. El registro no cambió y su estado no recibe aprobación científica.
Diagnóstico completo y limitación de EXP315 en la
[auditoría del registro](streamlit-registry-audit.md). Preservación posterior
normal/-O PASS. El worktree temporal se retiró y los demás quedaron intactos.

El artefacto sigue en
`d0a883a7528afd5d3d1fdbe43d44e5c5a396c109ab20ed49845a198ccdb75c8c`;
su manifiesto, el cargador congelado, `risk/configuration.py`, receta, contrato
`satd-risk-ranking-v1`, procedimiento `SATD-RISK-2025-LOG-CLIMATE-v1`,
`procedure()["budget"] == 8` y evidencia científica permanecen intactos.

## Alojamiento pendiente

No se desplegó ni se verificó ninguna URL pública. Faltan elección del proveedor,
servicio/permiso de administración, contexto autorizado en volumen privado y
dominio/URL HTTPS con WebSocket. La [guía de operación](../operations/streamlit-demo.md)
especifica comandos de instalación, provisión, preflight, inicio, salud,
reinicio/rollback y los siete pasos de comprobación pública. El siguiente paso
externo es habilitar ese destino y suministrar el contexto mediante un canal
privado autorizado; no se necesita HF_TOKEN en el proceso Streamlit.


## Mecanismo de contexto de la segunda iteración

El CSV mensual del tutor no sustituye el contexto: los derivados offline usan
historia desde 2007 para los doce orígenes 2024-11–2025-10. Streamlit exige el
conjunto completo; no construye predictores, adquiere crudos ni ejecuta Kedro.

Un módulo `contexto_paquete.py` valida y empaqueta esos archivos ya construidos.
Formato ZIP_STORED `satd-demo-context-v1`, inventario cerrado de catorce miembros
(trece archivos de contexto más metadatos), orden/timestamps/permisos fijos y
recibo externo con fecha UTC. El paquete artificial generado por la CLI tiene
SHA-256 **`6a9f7e3c3d842d7b5a8d3a1ccddcf4d7a4d751894e443ae95c6d1e12a490fddb`**
y tamaño **157.700 bytes**.
Paquete y recibo de prueba quedan bajo `pipeline/data/demo-validation/iteration2/`,
ignorados; no son un release científico ni un paquete privado listo para alojar.

Configuración: `SATD_DEMO_MODEL_DIR`, `SATD_DEMO_CONTEXT_DIR`,
`SATD_DEMO_CONTEXT_BUNDLE_URL`, `SATD_DEMO_CONTEXT_BUNDLE_SHA256`,
`SATD_DEMO_CONTEXT_TOKEN` opcional Bearer y `SATD_DEMO_CONTEXT_CACHE_DIR`.
Prioridad: directorio local existente válido; en su ausencia, caché íntegra
identificada por SHA; si falta, descarga HTTPS del paquete con ese pin.
Un local/caché corrupto detiene la carga; no oculta errores con otra fuente.

Hash externo antes de abrir ZIP, límites 16 MiB descargados/32 MiB expandidos,
TLS validado, redirecciones bloqueadas, extracción por allowlist sin enlaces ni
traversal, validación interna posterior y promoción atómica. Temporales fallidos
se retiran y el ZIP corrupto de caché se descarta sin continuar. Se valida la
caché de nuevo en otro arranque; `st.cache_resource` evita nuevas descargas por
interacción y la selección pura evita nuevos scorings al cambiar capacidad.

Errores públicos sin URL, credenciales ni excepción de transporte encadenada.
El tutor no ingresa credenciales. URL y token reales se configurarán como secretos
del servidor en la siguiente iteración. No se configuró ni probó un proveedor.

### Aceptación adicional del contexto

Pruebas en `demo/tests/test_contexto_paquete.py`:

| # | Contrato | Evidencia |
| --- | --- | --- |
| 1 | Mismos archivos → mismos bytes/hash | `test_package_is_deterministic_and_receipt_is_minimal` |
| 2–5 | Rechazar mes faltante, población distinta, CSV alterado y release ajeno | `test_packaging_rejects_invalid_context`, parametrizada |
| 6 | Directorio local válido prioritario | `test_local_valid_context_takes_precedence`; local corrupto no hace fallback |
| 7–9 | Transporte loopback, hash externo y paquete corrupto | `test_download_cache_restart_and_inference`, `test_bad_download_is_not_installed_or_kept` |
| 10 | Rechazar traversal, absolutos y enlaces | `test_archive_rejects_escape_and_links` |
| 11 | Caché reutilizada sin otra descarga | Recarga sin URL; alteración coordinada índice/CSV se rechaza; ZIP corrupto se descarta |
| 12–13 | Sin token: error controlado; sin secretos en errores/logs/recibos | `test_authorization_and_errors_do_not_expose_secrets` |
| 14 | Error comprensible en UI | `test_app.py::test_missing_context_is_sanitized` y contexto corrupto |
| 15–16 | Ranking vigente, cupos sin nuevo scoring/descarga | `test_streamlit_bootstrap_caches_across_interactions_and_restart`, más regresiones de selección |
| 17 | Cupo científico ocho | Aserción sobre `procedure()` y regresiones históricas |
| 18 | Modelo/evidencia/publicaciones intactos | 196 archivos protegidos iguales al inicio, más preservación normal/-O |

También se comprueban límites de tamaño, redirecciones, HTTP solo en pruebas y
exclusión de archivos privados ajenos al inventario. No se conecta a Internet:
los paquetes y el servidor HTTP son artificiales y locales.

Pendientes expresamente diferidos: **(1)** proveedor y URL pública,
**(2)** validación externa, **(3)** wireframe, mockup y evidencia final.


## Cierre local y archivos excluidos

Se preservaron los cambios iniciales de la rama y solo se añadieron los del
alcance autorizado. Son 17 archivos de código, pruebas, documentación, workflow
y lock; el inventario completo está arriba. Paquete/recibo artificiales,
contextos, cachés, logs y entornos quedan ignorados bajo el espacio de trabajo;
no se agregan a Git. El escaneo de los archivos del diff no encontró candidatos
de secretos ni rutas absolutas de esta máquina. Enlaces locales y diff PASS.
El árbol se deja limpio tras los commits locales; no se abre PR ni se hace push
o merge. La comprobación remota de CI queda diferida, sin atribuirle este PASS.

## Corrección de CI: lock condicionado por plataforma

El job **136864140792**, `Pipeline quality` del PR #18 sobre `794cf2b`, falló
en `Install isolated demo environment`: `uv sync` terminó correctamente, pero
`uv pip install --require-hashes -r demo/requirements.lock` devolvió código 2
porque faltaba el pin de `watchdog`. Streamlit 1.67.0 lo requiere fuera de Darwin;
el lock anterior se había compilado en macOS sin resolución universal.

Se reprodujo el mismo error localmente resolviendo para Linux en un entorno
vacío. Se regeneró el lock con `--universal`, manteniendo hashes y constraints
del pipeline: las 35 versiones previas permanecen iguales y se añade únicamente
`watchdog==7.1.1 ; sys_platform != 'darwin'`, con sus hashes. No se cambia la
dependencia directa de Streamlit ni el lock científico. La guía documenta el
comando correcto y CI ahora resuelve de forma explícita Linux x64, macOS arm64
y Windows x64 con `--require-hashes --reinstall --dry-run --only-binary=:all:`.
`--reinstall` impide que paquetes ya instalados oculten dependencias omitidas.

Verificación de esta corrección:

- Resolución cruzada completa de los tres destinos: PASS.
- Instalación cruzada real de los 36 paquetes/wheels Linux con hashes, en un
  entorno vacío separado: PASS. No se ejecutó código Linux ni se afirma un
  smoke nativo Linux; el daemon Docker local no estaba disponible.
- Instalación con hashes en macOS y `pytest demo/tests`: **64 PASS**, 19,36 s,
  incluidos smoke HTTP y reinicio. YAML, Ruff del pipeline, lock check y diff: PASS.
- Preservación normal/-O: PASS, 49 protecciones originales, 127 extendidas y
  22 JSON intactos. Sin cambios de modelo, evidencia, contratos ni presupuesto.
- No se repiten las suites completas pipeline/API/dashboard: solo cambian el
  lock de la demo, su guard de instalación y documentación. Los resultados
  acumulados anteriores corresponden a su revisión, no a una nueva ejecución.

Los logs locales quedan en `pipeline/data/demo-validation/ci-watchdog/`, ignorados.
El resultado remoto de la corrección requiere publicar el commit y ejecutar CI;
no se hace push ni merge aquí. La revisión humana requerida del PR permanece
vigente y no es un fallo de instalación ni una regla que deba desactivarse.
