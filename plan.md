# Hoja de ruta de implementación — Pipeline E2E SAT DENGUE

**Versión:** 1.5
**Fecha de creación:** 7 de noviembre de 2026
**Estado general:** 21/27; T1–T21 COMPLETAS; T22–T27 PENDIENTES; ninguna tarea activa ni bloqueada
**Repositorio definitivo:** `sramirezc2/sat-dengue-despliegue`
**Rama única de implementación:** `feature/pipeline-e2e`
**Entrega:** un único Pull Request

### Corrección de CI posterior al cierre de tarea 16

El run [42441799695](https://github.com/sramirezc2/sat-dengue-despliegue/actions/runs/42441799695)
de `4a3a803` aprobó Ubuntu/Pipeline quality, pero falló en macOS por ausencia de
`libomp` al importar XGBoost y en Windows por UnicodeEncodeError al mostrar el
log de pytest, ocultando su fallo original. La lectura del documento normativo
con encoding implícito también falla bajo CP1252 (byte UTF-8 0x81), reproducido
mediante una regresión controlada; no se atribuye ese ensayo a un runner Windows.

Corrección: instalar OpenMP solo en el runner macOS; leer la especificación y
el YAML de pruebas en UTF-8; emitir logs con escapes reversibles cuando la
consola no admite sus caracteres y fijar UTF-8 solo para stdio de procesos hijos.
Se conservan fallos/códigos de los gates, parámetros, lock y evidencia científica
existente. Cuatro regresiones inicialmente rojas, ahora verdes; 491 pruebas
locales aprobadas (seis avisos OmegaConf), lock/sync y Ruff verdes. Los 22 hashes
publicados permanecen intactos. La comprobación nativa de la corrección en
Windows/macOS queda pendiente de publicar y ejecutar la nueva revisión; no se
repite ninguna reproducción privada ni se inicia tarea 17.

## 1. Objetivo

Implementar en el repositorio definitivo un pipeline E2E reproducible que permita
adquirir y validar fuentes crudas, construir y certificar la tabla canónica,
preparar datos, entrenar candidatos, evaluarlos y publicar resultados compatibles
con la API y el tablero existentes.

La fábrica también deberá administrar múltiples experimentos aprobados sin
reescribir la validación cerrada de tarea 16: registro central, protocolo y
configuración congelados, ejecución identificable, evidencia agregada append-only,
tracking MLflow local, conclusiones y comparación reproducible entre experimentos.

La implementación debe conservar la separación:

```text
pipeline/ -> datos/resultados/ -> app/api/ -> app/dashboard/
```

`pipeline/` será un proyecto Kedro autocontenido. La adquisición de datos estará
desacoplada mediante adaptadores intercambiables. Inicialmente Hugging Face
distribuirá de forma privada las fuentes crudas y Zenodo podrá conservar releases
académicos aprobados, con una extensión compatible con AWS S3 para una migración
futura. Ningún proveedor entregará la tabla canónica: Kedro la reconstruirá de
forma determinista antes de cada experimento o reutilizará únicamente un derivado
cuya identidad completa haya sido certificada.

## 2. Reglas obligatorias

- Toda la implementación se acumula en la misma rama y termina en un único PR.
- Ningún cambio se realiza directamente sobre `main`.
- Antes de cada tarea se revisan `AGENTS.md`, este documento y el estado de Git.
- Se conservan los cambios preexistentes del usuario.
- No se reorganizan innecesariamente `app/`, `docker/`, `datos/` ni `scripts/`.
- Se evita el sobredimensionamiento y la sobreingeniería.
- El código debe aplicar DRY, SOLID, tipado y responsabilidades claras.
- El código Python debe usar docstrings estilo Google.
- No se crean ni editan celdas Markdown en notebooks sin autorización formal.
- Los archivos Markdown de documentación del repositorio sí están permitidos.
- No se agregan datos, modelos, secretos o artefactos pesados a Git.
- `datos/datos-crudos/` es únicamente la entrada local ignorada por Git;
  `pipeline/data/` contiene caché y trabajo ignorados.
- Cada cambio de comportamiento debe tener pruebas proporcionales.
- Una tarea no se marca como completa si sus validaciones no están verdes.
- `datos/resultados/` es la única frontera de publicación hacia la API.
- La API no importa código de `pipeline/` y el pipeline no escribe dentro de
  `app/`.
- El bundle crudo puede contener 2025, pero su cuarentena debe ocurrir antes de
  normalizar, agregar, unir, imputar o ajustar cualquier transformación.
- V3 reutiliza `TemporalPolicy` y `guard_development` como autoridades temporales;
  no se implementará un segundo guard paralelo.
- Ninguna observación, origen, objetivo o etiqueta desde `2025-01` participa en
  construcción canónica de desarrollo, preparación, entrenamiento, calibración,
  selección, umbrales o evaluación presentada como independiente.
- La tabla canónica es un derivado local reconstruible; no se publica como fuente
  de entrenamiento ni se incorpora DVC en esta implementación.
- `factory_validation` y `T16-FACTORY-XGB-S53-v1` permanecen cerrados e inmutables;
  la ejecución de otros experimentos utilizará un pipeline separado.
- Ningún experimento científico real se ejecutará sin registro, protocolo,
  configuración, hashes y estado `APPROVED` verificables.

## 3. Estados permitidos

| Estado | Significado |
|---|---|
| `PENDIENTE` | La tarea todavía no ha comenzado. |
| `EN CURSO` | Es la única tarea activa en este momento. |
| `BLOQUEADA` | No puede continuar; debe registrar causa y decisión requerida. |
| `COMPLETA` | Cumple criterios, validaciones y evidencia. |

Solo puede existir una tarea `EN CURSO`. Las tareas se ejecutan en orden. Para
cambiar el alcance se debe registrar primero la decisión en la sección 7.

## 4. Hoja de ruta

| # | Tarea | Estado | Dependencia | Evidencia de cierre |
|---:|---|---|---|---|
| 1 | Formalizar arquitectura y fronteras | `COMPLETA` | — | Documento central aprobado: `pipeline/`, contrato de publicación, fuentes y tratamiento de 2025. |
| 2 | Activar gobernanza y CI por componentes | `COMPLETA` | 1 | Implementación y validaciones locales completas; CI remota y ruleset siguen pendientes antes del merge (DEC-006). |
| 3 | Congelar y proteger la línea base del despliegue | `COMPLETA` | 2 | Compose arranca desde clon limpio; salud y consulta válida funcionan; brechas existentes quedan corregidas o documentadas. |
| 4 | Crear el subproyecto `pipeline/` con Python, Kedro y uv | `COMPLETA` | 3 | Estructura autocontenida, lock, CLI, E2E sintético mínimo y `.github/workflows/pipeline-ci.yml` ejecutable y validado sin afectar `app/`. |
| 5 | Implementar releases y adquisición desacoplada | `COMPLETA` | 4 | `DataSource`, `ResolvedBundle`, manifiestos, caché, hashes y adaptadores local, Hugging Face, Zenodo y S3 simulado. Es transporte neutral; la restricción a fuentes crudas se conecta en la tarea 13. |
| 6 | Migrar el panel canónico desde V2 | `COMPLETA` | 5 | Dominio canónico migrado con procedencia y paridad exacta sobre muestra artificial de 167 filas; no incluye ingestión real desde crudos. |
| 7 | Implementar etiquetas y controles temporales | `COMPLETA` | 6 | Inicio T+1/T+2, elegibilidad solo en T, ausencias, roles, `TemporalPolicy` y `guard_development` como autoridades de V3; 47 pruebas nuevas. |
| 8 | Recuperar o reimplementar el arnés rolling-origin | `COMPLETA` | 7 | Arnés mensual expansivo, madurez estricta, digest y 19 pruebas nuevas; protocolo histórico de ocho ventanas `NOT_REPRODUCED`. |
| 9 | Implementar adaptadores de modelos | `COMPLETA` | 8 | Protocol, configuración/semilla, registro neutral, protección de entradas y probabilidades; 28 pruebas nuevas. Estimadores reales pendientes. |
| 10 | Implementar calibración, umbrales y líneas base | `COMPLETA` | 9 | Cinco roles disjuntos, disponibilidad estricta, sigmoide, grilla/umbral congelados y referencias de inicio; 25 pruebas nuevas antífuga. |
| 11 | Implementar métricas e incertidumbre | `COMPLETA` | 10 | AP/AUROC/Brier, sensibilidad/FAR/volumen, soporte emparejado, estratos y bootstrap municipal descriptivo; 29 pruebas nuevas. |
| 12 | Agregar trazabilidad de corridas | `COMPLETA` | 11 | MLflow local opt-in, manifiestos, linaje y 33 pruebas nuevas verdes; el bloqueo concurrente quedó resuelto sin versionar datos (DEC-015). |
| 13 | Construir y certificar la tabla canónica desde fuentes crudas | `COMPLETA` | 12 | Arquitectura sincronizada; contrato crudo cerrado y productores registrados; 83 pruebas nuevas/356 totales. N=3 exacto sobre 168 claves artificiales y prueba de cuadrícula artificial de 182.886 claves (DEC-017). Cuarentena previa, guards T+1/T+2, conservación/nulos, atomicidad y tracking agregado verificados. Reproducción real pendiente en tarea 16. |
| 14 | Migrar la publicación sin romper el despliegue | `COMPLETA` | 13 | Publicador puro, wrapper compatible y deployment_publication registrados; equivalencia byte a byte en cuatro casos caracterizados. Staging, contrato, manifiesto SHA-256 y rollback probados; 84 pruebas nuevas/440 totales. Los 22 JSON originales conservan sus hashes y Pydantic/Zod aceptan los generados. |
| 15 | Cerrar portabilidad | `COMPLETA` | 14 | macOS local y Colab real verdes; matriz nativa Ubuntu/Windows/macOS sobre 61159d9 aprobada en run 42424636145. Cada runner: 463 pruebas, 12 específicas, cuatro CLI, árbol limpio y hashes idénticos. Siete checks del PR verdes; recibos/logs revisados. DEC-019; docs/decisions/portability.md. |
| 16 | Conectar el release crudo y ejecutar reproducción sintética y real | `COMPLETA` | 15 | Construcción real/N=3 canónico y evidencia previa conservadas. [T16-FACTORY-XGB-S53-v1](docs/decisions/task16-experiment-specification.md): tres procesos E2E desde cinco fuentes, diez soportes aprobados, modelos independientes S53, identidades completas exactamente iguales. Lock/sync/Ruff, 487 pruebas pipeline, API 28, tablero 33/lint/build y 24 contratos verdes; 22 JSON publicados intactos. Evidencia agregada en docs/evidence/task16/factory-experiment/ y [reproducción](docs/decisions/task16-reproduction.md). Sin G, presupuesto, campeón o autorización operativa. La generalización experimental se incorpora como tarea 17. |
| 17 | Generalizar la fábrica y administrar experimentos reproducibles | `COMPLETA` | 16 | Registro y configuración cerrados, hashes, estados, pipeline separado `experiment_run`, evidencia exclusiva e inventarios, MLflow local padre/hijos, conclusiones obligatorias y comparación JSON. EXP001/EXP002: fixtures completos con recetas distintas y conclusiones NOT_APPLICABLE; sin ciencia real. 536 pruebas (45 nuevas), lock/sync/Ruff, API 28, tablero 33/lint/build, Pydantic/Zod 24 y cuatro CLI previos verdes. 49 archivos protegidos idénticos: 22 JSON, 16 recibos previos y demás evidencia T16; identidad N=3 intacta. [Diseño y límites](docs/decisions/experiment-management.md), [validaciones](docs/evidence/task17/validation.json). |
| 18 | Realizar revisión científica independiente | `COMPLETA` | 17 | [Auditoría científica](docs/reviews/scientific-review.md): APPROVED_WITH_LIMITATIONS, sin hallazgos científicos bloqueantes. Código/contratos/bitácora contrastados; 536 pruebas y 1.134 casos analíticos, 49 hashes y N=3 histórico íntegros. Tandas G, disponibilidad operativa y privacidad remota actual no verificadas; referencias científicas/intervalos de fábrica limitados. [Recibo](docs/evidence/task18/scientific-review.json). |
| 19 | Documentar operación, límites y migraciones | `COMPLETA` | 18 | [Guía central](docs/operations/pipeline-operations.md) enlazada al manual, sin duplicar sus recetas. Preparación multiplataforma, comandos reales, publicación, recuperación, privacidad, memoria y migración de proveedores. Ayudas/AST/código, cuatro CLI artificiales, Pydantic/Zod 24 y 80 enlaces locales verificados. [Recibo](docs/evidence/task19/operations-validation.json). |
| 20 | Ejecutar revisión de seguridad | `COMPLETA` | 19 | [Revisión de seguridad](docs/security/security-review.md): APPROVED_WITH_LIMITATIONS, sin CRITICAL/HIGH abiertos. Zod 4.6.6 compatible, logs SDK protegidos y LF de identidades/referencias POSIX; 541 pruebas pipeline, API 35, tablero 55/lint/build, lock/sync/Ruff, contratos 24+24, registro y 68 hashes verdes. Avisos moderados, backup privado exclusivamente local y controles externos documentados con responsables. [Recibo](docs/evidence/task20/security-review.json). |
| 21 | Registrar capacidades reutilizables | `COMPLETA` | 20 | Cuatro skills canónicas para experimentos, revisión científica, verificación y recuperación; catálogo, integración Codex/Claude, manual, pruebas estructurales, evaluaciones secas y recibos de [validación](docs/evidence/task21/skills-validation.json) y [auditoría documental](docs/evidence/task21/documentation-audit.json). |
| 22 | Corregir caché y recibos de adquisición | `PENDIENTE` | 21 | Preflight seguro, recibos exclusivos bajo pipeline/data/, regresiones locales y preservación histórica. |
| 23 | Agregar operación portable y comando canónico E2E | `PENDIENTE` | 22 | Helper adquisición → canonical_build provisional, comandos portables y recursos medidos; sin ciencia nueva. |
| 24 | Validar las correcciones operativas acumuladas | `PENDIENTE` | 23 | Gate local acumulado, checkout temporal limpio, hashes y árbol limpio; sin fuentes privadas. |
| 25 | Elaborar reporte ejecutivo final | `PENDIENTE` | 24 | Antigua T22: resumen final de entregables, validaciones, limitaciones y decisiones pendientes. |
| 26 | Publicar cambios y validar el PR #1 | `PENDIENTE` | 25 | Fase 2: solo con autorización posterior; push normal al PR existente y CI remota del HEAD publicado. |
| 27 | Ejecutar auditoría final de merge | `PENDIENTE` | 26 | Fase 2: ruleset, aprobación independiente, conversaciones y checks finales; no autoriza merge automático. |

### 4.1. Contrato crudo aprobado para la tarea 13

El adaptador local leerá desde `datos/datos-crudos/`. Los adaptadores remotos deben
materializar exactamente el mismo bundle verificado bajo
`pipeline/data/01_raw/inbox/`; las etapas científicas solo reciben rutas locales y
metadatos neutrales.

| Identificador | Archivo | Bytes | SHA-256 |
|---|---|---:|---|
| `divipola_catalog` | `Divipola-municipios.md` | 209.867 | `72eabcea0ff26370d23b9688e8d8f2246946cc815c040ccf1a6966b37a1de9f3` |
| `divipola_provenance` | `divipola-provenance.json` | 925 | `92091306f0130910f27de999776b5cf4ed36b7dd7c89bd724d58caeb74f8c158` |
| `dengue_notifications` | `dengue.csv` | 875.694.283 | `58d277cfef7a60c28d488eefe4e7a1a7bf0f7b0df3dd88245971cd7b3d32c84b` |
| `severe_dengue_notifications` | `dengue_grave.csv` | 24.537.734 | `3d60e96ccbedc35a19a8f5f54be8d786aa599813259c914f131522bf17dd1d70` |
| `daily_climate` | `google_earth_engine.csv` | 1.714.544.311 | `dfe20fa02b6d6068c04744b5c86f44112048400a7fde637368c0d4effc88cb3f` |

`Listados_DIVIPOLA.xlsx` queda como evidencia auxiliar del release, no como insumo.
DEC-021 autoriza ignorarlo durante la descarga; se elige no descargarlo. El
inventario del repositorio remoto puede incluirlo, pero el manifiesto científico
y el bundle entregado a Kedro contienen exclusivamente los cinco archivos de la
tabla. El Excel no participa en construcción canónica ni aprendizaje. El archivo
`google_earth_engine-selected-columns.csv`, el release derivado existente en
Hugging Face y cualquier tabla canónica remota se rechazan como entradas. Los
microdatos epidemiológicos completos permanecen privados aunque el equipo haya
confirmado que no requieren licencia ni autorización adicional.

### 4.2. Orden obligatorio de construcción canónica

La tarea 13 debe implementar, como nodos pequeños y funciones puras, esta cadena:

1. `raw_contract_validation`: validar lista cerrada, tamaños, SHA-256, encabezados,
   esquemas y `release_kind: raw_sources`; fallar antes de leer datos científicos
   si el contrato no coincide.
2. `raw_temporal_projection` y `raw_temporal_quarantine`: leer primero solo claves
   territoriales y temporales, separar todo periodo desde `2025-01` y registrar
   conteos/digests sin exponer filas. La cuarentena ocurre antes de productores.
3. `geography_normalization`: interpretar `Divipola-municipios.md` como el JSON
   aprobado, verificar su procedencia y producir la dimensión única de 1.122
   municipios.
4. `epidemiology_normalization`: mantener separados los eventos 210 y 220, usar
   residencia (`COD_DPTO_R` + `COD_MUN_R`) e `INI_SIN`, sin fallback a `FEC_NOT`
   ni deduplicación por `CONSECUTIVE`.
5. `climate_daily_normalization` y `climate_monthly_aggregation`: exigir el archivo
   de 18 columnas, validar días completos y producir cuatro sumas y cinco medias
   mensuales; un mes incompleto queda nulo, nunca se rellena con cero.
6. `canonical_sources` y `canonical_panel`: construir la cuadrícula municipio-mes,
   aplicar joins con cardinalidad declarada y reutilizar `domain/canonical.py` sin
   duplicar sus reglas.
7. `canonical_validation` y `canonical_serialization`: validar cobertura,
   unicidad, tipos, nulos, conservación de conteos y digest semántico; T+1 termina
   en origen `2024-11` y T+2 en `2024-10` para objetivos hasta `2024-12`.
8. `canonical_reproducibility`: reconstruir N=3 desde los crudos en directorios y
   procesos aislados, sin reutilizar derivados; liberar una única salida local
   solo si esquema, orden, tipos, claves, valores, nulos y hashes coinciden.
9. Conectar al tracking el manifiesto crudo, la configuración del constructor, el
   lock, los digests de cuarentena y el digest canónico, sin registrar microdatos.

El registro Kedro debe exponer al menos `canonical_build` y
`canonical_reproducibility`. Las pruebas usarán un bundle sintético pequeño; la
descarga y reproducción científica real corresponden a la tarea 16.

## 5. Secuencia de integración

Aunque toda la implementación terminará en un solo PR, los commits deben conservar
esta secuencia lógica:

```text
arquitectura y gobernanza
        -> línea base del despliegue
        -> esqueleto de pipeline
        -> adquisición y contratos
        -> validación y cuarentena cruda
        -> construcción canónica certificada
        -> preparación científica
        -> entrenamiento y evaluación
        -> administración y comparación de experimentos
        -> publicación
        -> portabilidad y reproducción
        -> revisión, documentación y cierre
```

No se mezclará en un mismo commit:

- estabilización del despliegue con creación de Kedro;
- cambios de modelos con migración del publicador;
- refactorizaciones cosméticas con cambios científicos;
- correcciones de API con adquisición de datos de entrenamiento.

## 6. Control de avance

Actualizar esta sección al cerrar cada tarea.

| Indicador | Valor |
|---|---:|
| Tareas completas | 21/27 |
| Tarea activa | Ninguna |
| Tareas bloqueadas | Ninguna |
| Última tarea completada | T21 — Registrar capacidades reutilizables |
| Próxima tarea | T22 — Corregir caché y recibos de adquisición (`PENDIENTE`) |
| Última actualización | 9 de noviembre de 2026 |

### Registro de ejecución

| Fecha | Tarea | Estado nuevo | Commit | Validaciones | Observaciones |
|---|---:|---|---|---|---|
| 2026-11-07 | 1 | COMPLETA | `e794bce` (arquitectura); `60692c3` (hoja de ruta y cierre, sustituye a `fd9eae7`) | Rutas y enlaces revisados; diff documental sin errores de espacios; plan versionado. | Arquitectura y hoja de ruta compartidas. |
| 2026-11-07 | 2 | COMPLETA | `f67d1c6` | API: 22 pruebas; tablero: lint sin errores (6 advertencias), 33 pruebas y build; publicación: 22 JSON en API y prueba Zod verde; YAML, shell, filtros y diff validados localmente. | Implementación y validación local completas. GitHub Actions no fue ejecutado ni validado remotamente. CI remota, ruleset, aprobación independiente y checks requeridos siguen pendientes y son obligatorios antes del merge (DEC-006). |
| 2026-11-07 | 3 | COMPLETA | `5ec813e` | API: 28 pruebas; tablero: instalación con lockfile congelado, lint sin errores (6 advertencias), 33 pruebas y build; Docker Compose construido sin caché desde checkout temporal, 3 servicios activos, 22 resultados, Meta y Tolima disponibles, consultas y smoke test verdes; volumen verificado tras recrear contenedores; diff sin errores. | El estado inicial arrancaba con volumen vacío, 0 resultados y consultas 404. La imagen ahora siembra el volumen; S3 descarga siempre a temporal, comprueba tamaño y contrato, y reemplaza atómicamente. SHA-256 queda diferido a la tarea 13 porque aún no existe un hash remoto confiable. Recursos Docker temporales eliminados. |
| 2026-11-07 | 4 | COMPLETA | `20897e9` | `uv lock --check --project pipeline`, `uv sync --locked --project pipeline`, `uv run --directory pipeline ruff check .`, `uv run --directory pipeline pytest` (7 pruebas) y `uv run --directory pipeline kedro run --pipelines synthetic`: verdes, también desde clon temporal limpio del commit con entorno nuevo. Métricas sintéticas: 1 fila, MAE 5, MSE 25. Regresión: API 28 pruebas; tablero lint sin errores (6 advertencias), 33 pruebas y build node_server; YAML, shell, filtros, enlaces y diff válidos. | `Pipeline quality` implementado y validado localmente; no se ejecutó remotamente por DEC-006. Python 3.12, Kedro 1.7.0, pytest 9.2.0, Ruff 0.17.4 y uv 0.11.19. Adaptación CLI registrada en DEC-007. CLI actualizada en `1dad0ec`; solo persisten avisos internos de OmegaConf. Sin publicación, datos reales, secretos ni artefactos pesados generados fuera del entorno ignorado; árbol del clon limpio. |
| 2026-11-07 | 5 | COMPLETA | `1dad0ec` (CLI Kedro vigente); `a308c78` (adquisición) | `uv lock --check --project pipeline`, `uv sync --locked --project pipeline`, Ruff, pytest (71 pruebas: 64 nuevas) y `kedro run --pipelines synthetic` verdes, también desde clon temporal limpio de `a308c78` con entorno nuevo. API: 28 pruebas; tablero: lint sin errores (6 advertencias), 33 pruebas y build node_server. YAML, filtros, shell, diff y exclusión de `pipeline/data/` verificados. | Contratos inmutables, fábrica única y caché común por release/digest; cada hit verifica tamaño y SHA-256; transferencias temporales y reemplazo atómico por archivo. Local, HF y Zenodo probados con archivos/dobles locales; S3 con cliente falso y claves bajo prefijo de revisión, sin AWS. Integración del resolver como nodo Kedro con configuración temporal, sin pipeline de adquisición pendiente de datos reales. Solo se agregó huggingface_hub 2.4.0 y sus dependencias transitivas; Zenodo usa HTTP de biblioteca estándar. Guard global de pytest bloquea red, DNS, imports inversos y acceso a publicaciones. No hubo descargas científicas reales ni credenciales. La conexión del inventario y release privado crudo corresponde a la tarea 16. CI remota y ruleset pendientes por DEC-006. |
| 2026-11-07 | 6 | COMPLETA | `3ff23a560388c24b6eabe3a1427f6376c867da87` (implementación); `d5355e9` (cierre e inicio de 7) | Lock/sync, Ruff, 92 pruebas y E2E sintético verdes; verificación optativa de referencia V2 exacta; API 28; tablero lint sin errores (6 advertencias), 33 pruebas y build; diff sin errores. | V2 `j-mauro-r/SAT-Dengue-V2@916a69f3bb73f2ffbb0ec038b8bef887ee91adf1`, blobs y SHA-256 documentados en `docs/decisions/v2-scientific-migration.md`. 167 filas artificiales 2018–2024, Meta/Tolima; igualdad de tabla, tipos, nulos, roles, X y cobertura. NumPy 2.5.4 y pandas 3.0.6 fijados. Pruebas normales bloquean V2/red/app/publicaciones; no CSV de 426 MB ni datos científicos reales/2025. No se escribió en V2; cambios externos de ese árbol registrados en DEC-008. La evidencia es sintética; reproducción real pendiente en tarea 16. |
| 2026-11-07 | 7 | COMPLETA | `8ed8293391620a955f8756c92b8a0b64a74eb0e9` | Lock/sync, Ruff, 139 pruebas (47 nuevas), E2E y siete centinelas explícitos verdes; clon temporal con entorno nuevo, árbol idéntico al commit de implementación, instalación, Ruff, 139 pruebas, centinelas y E2E verdes. API 28; tablero lint sin errores (6 advertencias), 33 pruebas y build; cuatro YAML, filtros y 19 bloques shell válidos; diff/imports/patrones de secretos/tamaños revisados. | Mismo commit histórico V2; referencia adicional de siete estados artificiales hasta junio de 2024 con paridad exacta en ambos horizontes. Inicio = anterior 0 y objetivo 1; ausencia preservada, elegibilidad solo en T. Rechazo por objetivo antes de leer etiquetas o invocar consumidor; no se leyó ni utilizó ninguna observación/etiqueta científica de 2025 en el pipeline. Centinelas solo con claves/marcadores artificiales. X/y separados, disponibilidad explícita, selecciones fijas sin rolling-origin ni reserva rígida de 2024. Ninguna escritura en V2; estado externo final documentado en DEC-008. Las regresiones de producto consultan JSON publicados históricos (DEC-009). Sin CSV de 426 MB, modelos, datos reales nuevos, notebooks, push o PR. Reproducción real pendiente en tarea 16; CI remota y ruleset pendientes (DEC-006); CLI conserva DEC-007. Tarea 8 no iniciada. |
| 2026-11-07 | 8 | COMPLETA | `672c8aaf1d863d6562686b67d560af7625876999` | Estado inicial exacto `f5c8768`, árbol limpio y 139 pruebas verdes; gate de tarea: lock/sync, Ruff, 158 pruebas (19 nuevas), suite específica y E2E sintético verdes; diff sin errores. | Fuente histórica fijada `916a69f3bb73f2ffbb0ec038b8bef887ee91adf1`, archivos/hashes/reglas en `docs/decisions/temporal-experiments.md`. Desarrollo artificial 2018–2024: 2018 calentamiento, folds mensuales desde 2019, T+1/T+2 separados, etiquetas disponibles estrictamente antes del consumo. Protocolo de ocho ventanas/cohortes/preparadores históricos `NOT_REPRODUCED`; sin paridad ni reproducción real. Sin nuevas dependencias, datos reales/2025, modelos científicos, notebooks, acceso a publicaciones o escrituras V2. Tarea 16, CI remota y ruleset pendientes. |
| 2026-11-07 | 9 | COMPLETA | `1b16058e3975b0003ade9fd4e7ccff61a542f8e7` | Lock/sync, Ruff, 186 pruebas (28 nuevas), 47 pruebas específicas de tareas 8–9 y E2E sintético verdes; diff sin errores. | Contrato neutral con identidad/configuración JSON/semilla, instancia nueva por fold, esquema/orden/tipos congelados, inferencia solo X, probabilidades y enlaces validados. Backend mutante rechazado y entrada original protegida. Misma ejecución rolling-origin para dos familias dobles. Procedencia/hashes históricos en `docs/decisions/temporal-experiments.md`. Sin dependencias nuevas ni estimadores reales; XGBoost/LightGBM/GAM, preparación y replay históricos pendientes/NOT_REPRODUCED. No modelos entrenados versionados, escrituras V2, publicaciones ni datos reales/2025. |
| 2026-11-07 | 10 | COMPLETA | `651fcabaacddaed1c546680af0f4f8d376c8de4f` | Lock/sync, Ruff, 211 pruebas (25 nuevas), 72 específicas de tareas 8–10 y 11 centinelas explícitos verdes; E2E sintético verde. Checkout temporal con entorno nuevo y árbol idéntico al commit: instalación bloqueada, Ruff, 211 pruebas, 72 específicas y E2E verdes. API 28; tablero instalación con lock congelado, lint sin errores (6 advertencias), 33 pruebas y build. Cuatro YAML, filtros y 19 bloques shell válidos; 20 hashes V2 verificados, imports/diff/patrones de secretos/tamaños revisados. | Roles por objetivo train/calibration_fit/calibration_selection/threshold_selection/evaluation, disponibilidad estricta y embargo explícito; lectores espía prueban cero accesos a evaluation.y durante ajuste/selección/inferencia. Modelo y sigmoide ajustados una vez; configuración, representación y umbral congelados antes de evaluación. JSON/digest estable sin pickle o modelos versionados. Muestra artificial T+1/T+2 selecciona sigmoide y 0,3 con grilla/cota de test, sin valor operativo. Prevalencia solo train y persistencia adaptada a no inicio con soporte común. scikit-learn 1.7.2/SciPy 1.18.1 fijados; justificación y NOT_REPRODUCED en `docs/decisions/temporal-experiments.md` (DEC-010/011). V2 conservó árbol limpio; ninguna escritura V2 ni CSV de 426 MB/datos científicos reales/2025. Regresiones de publicaciones solo contractuales (DEC-009). Tarea 11 no iniciada; tarea 16, CI remota/ruleset, aprobación independiente y único PR pendientes. Sin push/PR. |
| 2026-11-07 | 11 | COMPLETA | `92d81305c98b029dc698be9e05d5d3b83b93b5a6` | Estado inicial exacto 4646316/10 de 20/árbol limpio; 211 pruebas, Ruff, lock y E2E verdes. Gate final: lock/sync, Ruff, 240 pruebas (29 nuevas), suite específica 29 y E2E verdes; diff sin errores. | Evaluación posterior al freeze, claves explícitas, soporte común, ausencias visibles y denominador de inicios intacto ante predicciones ausentes. AP agrupada, AUROC medio crédito, Brier, sensibilidad/FAR/volumen; diferencias emparejadas, global/horizonte/departamento, curvas diagnostic_only. Bootstrap por municipio con réplicas comunes, semilla, percentiles y estados insuficientes/indefinidos; sin intervalos calibrados ni campeón. Procedencia/hashes y NOT_REPRODUCED en docs/decisions/paired-evaluation.md; ocho ventanas históricas y bootstrap de cuatro ventanas no reproducidos. Sin dependencias nuevas ni datos reales/2025; tarea 16 y revisión científica siguen pendientes. |
| 2026-11-07 | 12 | COMPLETA | `293e6481db392ce89a3068d25a54c2c4424b088d` | Gate final: lock/sync, Ruff, 273 pruebas (33 nuevas), 62 específicas de evaluación/tracking y E2E verdes. Checkout temporal con entorno nuevo/árbol idéntico: instalación sin dev, SDK MLflow ausente y E2E verde; luego instalación completa desde lock, Ruff, 273 pruebas, 62 específicas y E2E verdes. API 28; tablero instalación congelada, lint sin errores (6 advertencias), 33 pruebas y build. Cuatro YAML/filtros y 19 bloques shell válidos; once nuevas huellas V2 verificadas; imports, secretos, rutas/SQLite/artefactos, tamaños y exclusión de stores revisados. | SDK oficial mínimo mlflow-skinny 3.17.2 + SQLAlchemy 2.0.57/Alembic 1.20.1/sqlparse 0.6.1 en grupo opcional tracking incluido en dev. Un padre real por invocación; recibo separado con ID real, lifecycle FINISHED/FAILED/KILLED y DISABLED sin almacenamiento. Solo agregados/configuración/linaje e inventario SHA-256; nada de X/y/filas/códigos/modelos/secretos/rutas privadas. Git/dirty, release/hash/proveedor de orquestación, cobertura, semillas/configuración/digests/bootstrap/lock/versiones/UTC registrados. Igualdad exacta de bytes científicos encendido/apagado y repetición con ID distinto; store recuperable tras mover workspace. Sin API fluida/autologging/registry global; SDK opt-outs explícitos y guard de red/DNS. Protecciones de symlinks y fallos tras rename probadas. NOT_REPRODUCED y riesgos de APIs SDK fijadas en docs/decisions/local-mlflow.md. Sin escrituras V2 (solo blobs), CSV de 426 MB, datos científicos reales/2025, notebooks o publicaciones. Tareas 13–21 pendientes; CI remota/ruleset, revisión independiente y único PR pendientes antes de merge. Sin push/PR. |
| 2026-11-07 | 12 | BLOQUEADA | `293e648` (implementación verde); `a450c52` (cierre seguido de cambio concurrente) | Tras a450c52, git status estaba vacío. En la comprobación final apareció `?? datos/resultados/datos-crudos/`; persistió en una segunda consulta. Solo se leyó metadato del directorio: mtime UTC 2026-11-07T18:26:48.727294+00:00; no se abrió contenido. No hay referencias a datos-crudos en app/pipeline/src/scripts/docker/docs antes de registrar este incidente. | Los gates de código (273 pruebas, 62 específicas, checkout limpio, SDK opcional y regresiones) permanecen verdes. La condición final de árbol limpio ya no se cumple. No se incorpora, ignora, borra, mueve o lee la carpeta ajena en ruta protegida. Se detiene el cierre; tarea 13 no iniciada. Resolver el cambio concurrente fuera de esta implementación y comprobar árbol limpio antes de volver a cerrar 12; no es necesario atribuir o reproducir datos. |
| 2026-11-07 | 12 | COMPLETA | `4d775ae` (protección de datos crudos; conserva `293e648` y `a450c52`) | Los datos crudos quedaron fuera de Git bajo `datos/datos-crudos/`; `.gitignore` protege la entrada local; el árbol versionado quedó limpio en el commit. | DEC-014 se conserva como incidente histórico y queda resuelta por DEC-015. La implementación y sus gates no cambiaron. Tarea 13 puede comenzar después de sincronizar `docs/architecture/pipeline-e2e.md` con DEC-016. |
| 2026-11-07 | 13 | COMPLETA | `c55df32` (cambios aprobados); `90db147` (arquitectura e inicio); `df4e541` (implementación); `9b4f47b` (pruebas) | Lock/sync, Ruff, 356 pruebas (83 nuevas), suite específica 83 y tres CLI Kedro verdes. Clon temporal limpio de 9b4f47b, árbol idéntico y entorno nuevo: instalación sin dev/MLflow ausente, canonical_build, canonical_reproducibility y synthetic verdes; después instalación completa desde lock, Ruff, 356 pruebas y 83 específicas verdes, árbol limpio. API 28; tablero instalación congelada, lint sin errores (6 advertencias), 33 pruebas y build node_server. Cuatro workflows YAML/filtros y 21 bloques shell válidos; scripts shell, imports/AST, secretos/pesos, exclusión de crudos/caché/stores y diff revisados. | Contrato raw_sources con cinco archivos/hashes fijos; revisiones mutables y derivados rechazados antes de adquisición. Proyección de claves y cuarentena antes de productores; tres registros reservados artificiales excluidos y fechas inválidas conciliadas. Guards existentes rechazan cruces T+1/T+2 a 2025, admitiendo últimos orígenes noviembre/octubre 2024. Residencia/INI_SIN/eventos separados, sin fallback ni deduplicación; clima incompleto nulo, joins y conteos conciliados. JSON direccionado por contenido, lectura exacta de tipos/esquema/nulos, reemplazo atómico y detección de cambios concurrentes. N=3 en procesos/directorios nuevos, sin derivados, bytes/digests idénticos y consumidor bloqueado ante divergencia. Fixture: 2 municipios/84 meses/168 claves; cuadrícula 1122×163=182886 comprobada separadamente con dimensión artificial (DEC-017). Tracking local real FINISHED/PASSED_N3, run 75d54c022ebf4f29b1cff1e9ed6561a5, Git 9b4f47b/dirty=false; tres SHA 4ca14c3c0707… y semántica 26cc689566b0… (huellas completas en docs/decisions/raw-canonical-build.md). Archivos reales usados solo para inventario/bytes/encabezados/hashes; ninguna transformación científica real, lectura V2 o descarga derivada. Sin cambios en API/tablero/Docker/publicación ni dependencias nuevas. Tareas 14–21 pendientes; autenticación/cobertura/formatos/rendimiento y N=3 real corresponden a tarea 16; CI remota y revisión independiente pendientes. Sin push/PR. |
| 2026-11-07 | 14 | COMPLETA | `ad6801b` (inicio); `73d9418` (caracterización); `734639f` (migración); `b420fa0` (wrapper); `37de562` (desempate estable separado); `9fee695` (gates/contratos/CI local) | Inicio exacto 32b6d06/árbol limpio/13 de 21: lock, Ruff, 356 pruebas, API 28, tablero 33/lint/build, 22 JSON Pydantic/Zod y diff verdes. Gate final: lock/sync, Ruff, 440 pruebas (84 nuevas) y 84 específicas verdes; cuatro CLI Kedro verdes: synthetic, canonical_build, canonical_reproducibility y deployment_publication. Clon temporal limpio de 9fee695, mismo árbol y entorno nuevo: instalación bloqueada sin dev, MLflow/Pydantic ausentes y cuatro smoke verdes; luego instalación completa, Ruff, 440 pruebas, 84 específicas, instalación congelada del tablero y 24 documentos Pydantic/Zod verdes. Clon permanece limpio después de los smoke y suites. API 28; tablero instalación congelada, lint sin errores (6 advertencias), 33 pruebas y build node_server. Cuatro YAML, filtros cruzados y 25 bloques shell válidos; scripts shell, imports/AST, secretos, tamaños y exclusiones verificados; diff sin errores. | Fuente de comportamiento: publicador V3 32b6d06, hash/fecha/salidas congelados antes de modificar el script. Entradas artificiales para 76 municipios: dos JSON exactos; equivalencia byte a byte auto/forzado y retro presente/ausente. Wrapper conserva flags/defaults/códigos 0/1/2 y mensajes esenciales; fecha UTC inyectable, UUID estables y override auditable. Dominio sin reloj/entorno/red/Git/I/O/consumidores; JSON Schema derivado e invariantes autónomos, contrastados con API y Zod externos. Reemplazos atómicos por archivo con staging, validación completa, SHA-256, lock, backups y rollback incluso tras rename efectivo; corrupción, symlinks, escapes, duplicados, fallos de escritura/promoción y manipulación posterior al gate probados. Manifiesto .publication/manifest.json no altera el índice. Se conserva NOT_APPROVED/NOT_SELECTED y el fallback legado de ineligible; desempate físico corregido aparte (DEC-018). Los 22 hashes versionados permanecen idénticos; sin cambios en app/datos/Docker, modelos, entrenamiento o fuentes crudas; ningún acceso V2 o proveedor remoto. Actualizados filtros y guías de índice/caché, sin afirmar aislamiento multiarchivo o recuperación frente a fallo del filesystem. jsonschema 4.23.0 fijado solo en pipeline. Tareas 15–21 pendientes; matriz multiplataforma, reproducción/conexión real y revisión científica siguen diferidas. CI remota/ruleset pendientes por DEC-006. Sin push/PR. |


| 2026-11-07 | 15 | EN CURSO | `e16b2f1` inicio; `b8abb11` correcciones/gates; `ea99b9f` matriz; `5cb8b98` bootstrap/guía Colab | Línea base local completa: 440, API 28, tablero 33/lint/build, cuatro CLI y 24 documentos Pydantic/Zod. Revisión 5cb8b98: macOS 26.6.2 Apple M2 Pro arm64, Python 3.12.13, uv 0.11.19: 463 pruebas (23 casos nuevos: 12 específicos + 11 guards con denegación de symlink), 12 específicas, cuatro CLI, 62,61 s; clon temporal limpio con entorno nuevo: mismos gates/hashes, 112,26 s. Colab GCE real Linux x86_64, host 3.13.18, Python 3.12.13 administrado por uv, uv 0.11.19: 463 + 12, cuatro CLI, 205,31 s; recibo finalizado 23:13:51 UTC. Tres recibos PASSED/dirty=false, cuatro advertencias Kedro; N=3, semántica, métricas y publicación idénticos entre entornos. API final 28, tablero 33/lint/build, wrapper y Pydantic/Zod 24 verdes. Cuatro YAML/26 bloques run, scripts shell, 95 AST/imports, secretos/tamaños/exclusiones y diff revisados. Los 22 JSON y lock conservan bytes. | Auditoría y recibos pequeños en docs/decisions/portability.md y docs/evidence/task15/. Tres regresiones inicialmente rojas: encoding implícito, CRLF histórico y autocrlf de Git; correcciones sin cambios científicos/dependencias/contratos. Guards de symlinks sin skips, capacidad nativa separada. PR #1 sigue abierto, no fusionado, fusionable técnicamente, sin reviews; cuatro checks originales success en 1bad249, Linux Ubuntu 26.04 x64 real basal. **Falta Windows real y ejecución de matriz nueva Ubuntu/Windows/macOS/checks sobre cambios nuevos. No hay autorización de push: cuatro commits locales y cierre documental, sin publicar.** Colab recibió solo bundle incremental de código revisado, sin push/credenciales/Markdown/Drive montado. Progreso 14/21 y tarea 16 PENDIENTE; no release privado, proveedores, V2 ni reproducción científica real. Ruleset y aprobación independiente siguen pendientes antes del merge. |


| 2026-11-07 | 15 | COMPLETA | Publicados los cinco commits hasta `61159d9`; cierre documental adicional local | Matriz real [42424636145](https://github.com/sramirezc2/sat-dengue-despliegue/actions/runs/42424636145) completada success: Pipeline quality y portability Ubuntu/Windows/macOS. Cada plataforma pasó 463 pruebas + 12 específicas, cuatro CLI, collector N=3, lock/sync/Ruff y árbol limpio. Ubuntu 26.04 x86_64/Python 3.12.16/147,85 s; Windows Server 2025 AMD64/Python 3.12.10/230,52 s; macOS 26.7.2 arm64/Python 3.12.10/121,65 s; uv 0.11.19 en los tres. Mac local y Colab real conservan recibos verdes de 5cb8b98 con código de pipeline idéntico. Tres ZIP remotos verificados contra digest de GitHub y JSON comparados: lock, tres SHA canónicos, tres digests semánticos, métricas y dos publicaciones exactos; sin fallos/errores/skips. Capacidad nativa de symlinks disponible en los tres runners; modos controlados también cubiertos. API tests 28 en run 42424636017, Dashboard quality 33/lint/build en 42424636020 y Publication contract/Pydantic-Zod 24 en 42424636002, todos success y pasos ejecutados. | Push normal de cinco commits autorizado explícitamente en el chat; no force push, merge ni PR adicional. PR #1 abierto en 61159d9, reviews vacías, mergeable técnico; ruleset sin verificar. Checkout PR ejecutó el merge temporal 21346107449ff9fdec5aa425dc2bb75128d16eb6; su árbol 0e9d724682658a4ecd2870b430e28f6eeb237820 coincide con 61159d9. Recibos y snapshot sin URLs firmadas en docs/evidence/task15/. El commit de cierre contiene solo documentación/recibos y no se publica, pues la autorización enumeró los cinco anteriores. Progreso 15/21, ninguna tarea activa; tarea 16 PENDIENTE. Solo fixtures científicos, sin release privado/proveedores/V2, sin modificar los 22 JSON ni dependencias/contratos. Revisión independiente/ruleset siguen siendo gates de merge, que no fue autorizado. |


| 2026-11-07 | 16 | BLOQUEADA | Base `48f3d666fd9b1d0bd7e0a434f3200b8a6b856dae`; solo registro documental local | Preflight: rama feature/pipeline-e2e sincronizada y árbol inicialmente limpio; tarea 15 COMPLETA/15 de 21; recibos reales macOS/Windows/Linux/Colab PASSED. Consulta nueva: PR #1 abierto, no fusionado y HEAD 48f3d66; siete checks completed/success, Pipeline CI run 42425574475 y API/tablero/contrato runs 42425574467, 42425574507, 42425574505. Los 22 SHA-256 publicados coinciden con HEAD. Recursos preliminares: Apple M2 Pro, 32 GiB RAM total y 640,38 GiB de disco libre; memoria disponible/pico y estrategia de bloques no diagnosticados. Se comprobó solo la presencia booleana de HF_TOKEN, sin revelar valor: ausente o vacío. parameters.yml mantiene modo synthetic y no declara un nuevo dataset/revisión privada. | Se detiene por la precondición 8 antes del preámbulo de implementación y de la línea base local completa; no se afirma haber repetido esas suites en esta tarea. Sin identidad aprobada ni HF_TOKEN no se consulta/descarga ningún release ni se prueba acceso anónimo/autenticado; existencia, privacidad y revisión remotas quedan sin verificar, no se declaran inexistentes. No se usan credenciales implícitas/cacheadas ni release derivado anterior; no se leen microdatos locales. Sin cambios de código/configuración, ejecución científica, N=3 real, experimentos o tracking. No se acredita reproducción real ni suficiencia de memoria a partir de RAM total. Para reanudar: identificar el nuevo dataset privado aprobado y su SHA completo, y disponer de HF_TOKEN en el entorno del agente sin escribirlo en archivos/argumentos/chat; repetir preflight y luego el preámbulo completo, incluido diagnóstico de recursos y suficiencia de la especificación experimental. Progreso permanece 15/21; ninguna tarea activa; tarea 17 PENDIENTE. Sin push, merge ni force push; datos, credenciales, publicación/API/tablero/Docker intactos. |

| 2026-11-07 | 16 | EN CURSO | Base `aed6346`; inicio documental local | Rama feature/pipeline-e2e y árbol inicialmente limpio. AGENTS.md, plan y arquitectura revisados; DEC-020 retomada. HF_TOKEN disponible: comprobación booleana de variable no vacía, sin imprimir ni almacenar el valor ni consultar credenciales cacheadas. | El pedido incluye literalmente <DATASET_ID> y <COMMIT_SHA>, sin valores concretos. Se solicita aclaración de ambos; no se infiere identidad/revisión ni se consulta el proveedor. La precondición de identidad inmutable continúa pendiente antes del preámbulo de implementación. |

| 2026-11-07 | 16 | BLOQUEADA | Base `aed6346`; cierre documental local de esta reanudación | HF_TOKEN disponible; bloqueo de credencial anterior resuelto. Identidad/revisión no verificables porque <DATASET_ID> y <COMMIT_SHA> son marcadores literales. git diff --check verde para el registro documental de inicio. | Se conserva DEC-020: pendiente recibir organización/dataset y SHA completo explícitos. No se consultó HF ni se descargaron datos, leyeron microdatos o ejecutaron experimentos/tracking. No se implementó código ni configuración; línea base local completa, diagnóstico de recursos, adquisición privada y N=3 real siguen pendientes. Progreso 15/21; tarea 17 PENDIENTE. Solo plan.md modificado, sin commit/push/PR/merge. |

| 2026-11-07 | 16 | EN CURSO | Base `aed6346`; conserva el registro documental previo local | Dataset y SHA completos recibidos explícitamente. DEC-020 permite reanudar el preflight de identidad/acceso y el preámbulo. | DEC-021 registrada antes de adquirir: ignorar Listados_DIVIPOLA.xlsx; no ampliar el contrato científico de cinco archivos. Evidencia detallada en docs/decisions/task16-reproduction.md. |

| 2026-11-07 | 16 | BLOQUEADA | Base `aed6346`; cierre documental local de reanudación | Primer preflight autenticado: revisión exacta, private=false; cinco tamaños y tres SHA LFS CSV coinciden; hashes de archivos pequeños sin verificar. Tras informar el usuario cambio a privado, segunda consulta autenticada al mismo dataset/SHA devuelve RepositoryNotFoundError/HTTP 404; no permite confirmar private=true ni inferir inexistencia. HF_TOKEN comprobado solo como disponible, sin revelar/persistir valor. Lock/sync/Ruff y pytest: 463 passed, cuatro advertencias Kedro, 51,64 s. git diff --check verde antes del cierre. | Acceso privado por resolver; se solicitó verificar cuenta/permisos de lectura del token en el entorno, sin compartirlo. Cero descargas y cero procesamiento de crudos; sin credenciales cacheadas, acceso anónimo, cambios de visibilidad o código/configuración. DEC-021 documenta Excel auxiliar ignorado y bundle científico cerrado de cinco fuentes. Metadatos/recibos y diagnóstico preliminar en docs/decisions/task16-reproduction.md y docs/evidence/task16/. No se completó el preámbulo local de API/tablero/CLI ni diagnóstico de pico/estrategia de memoria. Sin N=3 real, experimentos, modelos o tracking. Progreso 15/21; tarea 17 PENDIENTE. Sin commit/push/PR/merge. |

| 2026-11-07 | 16 | BLOQUEADA | Base `aed6346`; conserva cambios documentales previos | Nuevo preflight autenticado con HF_TOKEN del entorno al dataset/SHA aprobado: HTTP 404, RepositoryNotFoundError. Consulta de metadatos fuera del sandbox autorizada tras ConnectError de red dentro del sandbox. private=true y acceso al commit siguen sin confirmar; cero archivos descargados. Recibo separado: docs/evidence/task16/hf-private-access-preflight-retry.json. git diff --check verde; sin repetir suites de la reanudación anterior. | Se mantiene 15/21, tarea 17 PENDIENTE. Revisar permiso de lectura del token sobre el dataset privado y revisión aprobada antes de reintentar. Sin credenciales cacheadas, acceso anónimo, procesamiento, cambios de código/configuración, commit, push, PR ni merge. |

| 2026-11-07 | 16 | BLOQUEADA | Base `aed6346`; conserva cambios documentales previos | Usuario informa whoami validado para mauro114 y organización sat-dengue; no se repite identidad. HF_TOKEN no vacío del entorno pasado explícitamente a HfApi. Tras ConnectError del sandbox, dos consultas de metadatos autorizadas fuera de él: dataset sin revisión y SHA aprobado, ambas RepositoryNotFoundError/HTTP 401 (2026-11-08 00:13:22/00:13:42 UTC). private y SHA resuelto ausentes; cero descargas. Recibo: docs/evidence/task16/hf-private-access-preflight-after-whoami.json. JSON y git diff --check verificados; uv lock --check no llegó a ejecutarse por restricción de acceso a caché. Sin suites repetidas. | Mantener 15/21 y tarea 17 PENDIENTE. Resolver acceso con la credencial efectiva del proceso antes de confirmar private=true y SHA; whoami informado no acredita acceso observado al dataset. Sin imprimir/persistir token, credenciales cacheadas, solicitudes anónimas, descargas, procesamiento, cambios de código/configuración, commit, push, PR ni merge. |

| 2026-11-07 | 16 | EN CURSO | Base `aed6346`; conserva cambios documentales previos | whoami observado con HF_TOKEN: mauro114/sat-dengue. Preflight dataset y commit exitoso: private=true, SHA exacto aprobado; cinco tamaños y tres hashes LFS CSV coinciden. | Usuario autoriza adquisición exclusiva de cinco archivos y reproducción real con controles temporales, N=3, mediciones y validaciones. Excel ignorado; token nunca impreso ni persistido. Detenerse antes de tarea 17. |

| 2026-11-07 | 16 | BLOQUEADA | Base `aed6346`; implementación y cierre locales sin commit | Dataset privado y commit exacto; cinco archivos completos con tamaño/SHA-256 y encabezados/JSON correctos. Construcción medida 258,45 s; Kedro real 14 nodos/258,17 s y bytes iguales al certificado. N=3: 248,25/248,30/248,76 s, total 757,55 s, tres procesos y huellas/auditorías idénticas; máximo RSS 11,43 GiB. 182.886 claves únicas, 1.122 municipios/163 meses; 529.927 filas desde 2025 y 136 fechas inválidas en cuarentena previa. Roundtrip exacto; T+1/T+2 terminan en origen 2024-11/2024-10 y objetivo 2024-12, rechazan cruces a 2025; 89.143/88.470 ejemplos utilizables en 1.120 municipios. Lock/sync/Ruff, 469 pruebas pipeline, API 28, tablero 33/lint/build, cuatro CLI y 24 contratos verdes; 22 JSON idénticos; JSON/diff/secretos/pesos revisados. | DEC-022 adapta medianoche localizada con evidencia día/mes y bloqueo de fuentes sin fechas válidas; optimización de selectores/fechas preserva las reglas. Fuente de verdad: docs/decisions/task16-reproduction.md y recibos agregados. Falta candidato real predeclarado, hiperparámetros, calendario de roles/disponibilidad/embargo/soporte y grilla/cota FAR; no sustituir por parámetros sintéticos ni inventados. Por ello 16 no se marca COMPLETA; progreso 15/21 y 17 PENDIENTE. Excel ignorado; token no impreso/persistido; sin modelos, publicación, commit, push, PR ni merge. |

| 2026-11-07 | 16 | BLOQUEADA | Cambio documental local; sin commit | Se revisaron solo blobs V2 del commit 916a69f3bb73f2ffbb0ec038b8bef887ee91adf1, contratos/guards V3 y agregados certificados existentes. Propuesta científica creada con procedencia HEREDADO, ADAPTACIÓN_PROPUESTA, DECISIÓN_REQUERIDA y NO_REPRODUCIDO, sin atribuir fixtures como políticas. Gates técnicos previos aprobados; evidencia docs/evidence/task16/ conservada sin sobrescritura. git diff --check y git status --short al cierre. | [task16-experiment-specification.md](docs/decisions/task16-experiment-specification.md) es la única fuente humana para discutir/aprobar el experimento, estado PROPUESTA — NO APROBADA, ejecución NO. Único bloqueo: aprobación de candidato, hiperparámetros, calendario de roles, disponibilidad/embargo/soporte y grilla/cota FAR. Mantener 15/21, 16 BLOQUEADA y 17 PENDIENTE; no crear parameters_experiment.yml, registrar candidato, entrenar, evaluar, modificar publicaciones, push, merge ni otro PR. Esperar aprobación explícita del equipo. |

Cierres documentales independientes: tarea 8 en `39ba8d8`; tarea 9 en `9ce154d`;
tarea 10 en `4646316`; tarea 11 en `31f1e4b`. El cierre de tarea 12 es el commit
documental `a450c52`, posteriormente invalidado por DEC-014 y restablecido mediante
`4d775ae` y DEC-015.

### Cierre de fábrica de tarea 16

| Fecha | Tarea | Estado nuevo | Commit | Validaciones | Observaciones |
|---|---:|---|---|---|---|
| 2026-11-07 | 16 | COMPLETA | `0d3f30a` (implementación); cierre documental local | Lock/sync/Ruff, 487 pruebas pipeline, CLI synthetic, API 28, tablero 33/lint/build, Pydantic/Zod 24 documentos y checks de integridad verdes. factory_validation: PASSED, 871,8 s, tres procesos limpios secuenciales, sin cuarta corrida. | Los diez soportes cumplen; identidad común 899ba8b2c48b69dbf2e9094a6efedfa838cbfe4c800bed25fa1823503d06d52f. JSON completo de modelos, claves/matrices/probabilidades/decisiones/métricas/configuración/linaje idénticos. Etiquetas de evaluación diferidas; ningún objetivo 2025 consumido. FAR posterior T+2=0.8007614213 se reporta sin reajuste y no determina cierre técnico. 16 recibos previos y 22 JSON publicados intactos; sin secretos, datos/modelos pesados, campeón, cambios API/tablero/contratos, push/merge/otro PR. Evidencia y métricas en docs/decisions/task16-reproduction.md; 16/21, tarea 17 PENDIENTE. |

### Ampliación autorizada posterior a tarea 16

| Fecha | Tarea | Estado nuevo | Commit | Validaciones | Observaciones |
|---|---:|---|---|---|---|
| 2026-11-07 | 17 | PENDIENTE | — | Consistencia documental y dependencias revisadas; no se ejecutó implementación. | Se inserta la administración multi-experimento antes de la revisión científica. Las antiguas tareas 17–21 pasan a 18–22; progreso 16/22 y ninguna tarea activa. |
| 2026-11-07 | 17 | BLOQUEADA | Base `daf6ed5`; registro documental local sin commit | Lectura de AGENTS.md, hojas de ruta y arquitectura; rama feature/pipeline-e2e; T16 COMPLETA. No existe 14-05-01-194.md en la raíz. Cambios preexistentes conservados: .gitignore, plan.md y plan detallado sin seguimiento. | Precondición 4 del pedido: detener ante contradicciones. El plan detallado exige ruleset como gate cero antes de implementar, pero su sección 6 y DEC-006 lo exigen antes del merge. El cierre final denominado vigente aún dice 16/21 frente al progreso actual 16/22. Registrar y resolver estas discrepancias antes de iniciar código; sin suites, adquisición, reproducción T16, push, merge o PR. |
| 2026-11-07 | 17 | PENDIENTE | — | Documentos reconciliados; `git diff --check`, estados, conteos y referencias vigentes revisados. | DEC-026 resuelve DEC-025: ruleset obligatorio antes del merge, no como precondición de implementación; cierre vigente 16/22. Ninguna implementación iniciada y ninguna tarea activa. |

| 2026-11-07 | 17 | EN CURSO | Base `daf6ed5`; inicio local | Preflight documental y Git repetido; DEC-026 consistente; rama obligatoria y T16 COMPLETA. Snapshot SHA-256 de T16/publicaciones y copia de los tres cambios preexistentes fuera del repositorio. | Únicamente alcance T17; sin reproducción privada, push, merge ni nuevo PR. |

| 2026-11-07 | 17 | COMPLETA | `b19a92e` preflight; `84e6067` implementación; `6910efa` regresiones; `7c4004a` guard de bytes; cierre documental local | Lock/sync/Ruff, 536 pruebas (45 nuevas), API 28, tablero 33/lint/build y 24 contratos Pydantic/Zod verdes. Cuatro pipelines sintéticos previos y EXP001/EXP002 por CLI Kedro aprobados; tracking real SQLite y comparación de 42 filas T+2 verificados. Secretos/pesos/notebooks y diff revisados. | 17/22, ninguna tarea activa o bloqueada; 18 PENDIENTE. Los 49 hashes protegidos y N=3 T16 permanecen iguales; regresión artificial del adaptador exacta frente a daf6ed5, sin repetir T16 real ni adquirir fuentes privadas. Recibos CLI conservan código 6910efa; el guard posterior se valida con la suite E2E temporal completa. Sin push, merge, force push ni PR adicional. CI remota/ruleset/aprobación siguen como gates de merge. |

| 2026-11-07 | 18 | EN CURSO | Base `00c5404`; preflight completo | Repositorio/rama correctos, árbol limpio, manual versionado y HEAD remoto 00c5404; PR #1 abierto hacia main. Lectura documental requerida completada. Checks consultados: API/tablero/contratos verdes; Pipeline quality/Ubuntu/macOS verdes y Windows fallido (run 42447138122), hash de protocolo/configuración rechazado tras checkout. | Auditoría de código/pruebas/evidencia sin fuentes privadas, token ni nuevas corridas científicas. El fallo de portabilidad se investigará sin alterar hashes/evidencia histórica. Secuencia autorizada 18→19→20; detenerse ante un bloqueo científico. |

| 2026-11-07 | 18 | COMPLETA | `19cd9e7` cierre; `00c5404` auditado | Lock/sync/Ruff; 536 pruebas y 1.134 casos analíticos contra sklearn; firmas, proporciones, inventarios y 49 hashes protegidos íntegros. | APPROVED_WITH_LIMITATIONS. No nueva ciencia, descargas, token ni repetición real. Limitaciones y responsables en docs/reviews/scientific-review.md; Windows pendiente por conversión de Markdown en checkout, sin relajar integridad. Progreso 18/22; T19 PENDIENTE. |

| 2026-11-07 | 19 | EN CURSO | Tras `19cd9e7` | T18 COMPLETA/APPROVED_WITH_LIMITATIONS, 18/22; rama correcta y árbol limpio. Arquitectura y estados vigentes revisados. | Guía central enlazada al manual existente; verificar sintaxis con ayuda/código/fixtures. No ejecutar comandos privados ni experimentos cerrados. |

| 2026-11-08 | 19 | COMPLETA | `498583b` cierre; tras `19cd9e7` | Cuatro ayudas CLI y código de modos privados/Colab; cuatro pipelines artificiales; Pydantic/Zod 24, registro, preservación, ocho bloques y 80 enlaces locales verdes. | Guía central, navegación y recibo; no comandos privados, nuevos experimentos ni cambios a manual/fixtures/evidencia histórica. Progreso 19/22; T20 PENDIENTE. |

| 2026-11-08 | 20 | EN CURSO | Tras `498583b` | T19 COMPLETA/19 de 22, rama correcta y árbol limpio. Plan/arquitectura y fronteras revisados; estados secuenciales consistentes. | Auditar activos, credenciales, datos/evidencia, dependencias/red/Git/CI. Corregir solo defectos locales de seguridad e integridad sin alterar ciencia ni evidencia. Gate acumulado y push normal al único PR al cerrar; T21 no se inicia. |

| 2026-11-08 | 20 | COMPLETA | `0f4fc20` correcciones; `5d90929` cierre documental inicial | Gate acumulado: lock/sync/Ruff, 537 pipeline, API 35, tablero 55/frozen/lint/build, registro VALID, 24+24 contratos; 49 baseline y 68 extendidos idénticos. Consulta OSV 693 versiones: sin CRITICAL/HIGH abierto; cinco avisos moderados con mitigaciones. | APPROVED_WITH_LIMITATIONS; informe y recibo de seguridad, sin cambiar ciencia ni evidencia. Crudos históricos solo en backup local, excluidos de ramas de entrega; no borrar ni publicar. Progreso 20/22; T21 PENDIENTE, ninguna activa/bloqueada. Push normal al único PR autorizado tras cierre; checks nuevos por verificar, revisión humana/ruleset antes del merge. |

| 2026-11-08 | 20 | EN CURSO | Tras `5d90929`; run 42451673280 | Nuevo HEAD: API/tablero/contratos, quality, Ubuntu/macOS verdes; Windows 526 pasan/11 fallan. LF solucionó los fallos de hashes previos; quedan rutas generadas con separador nativo y encoding de una conclusión artificial. | Reabrir únicamente el cierre técnico T20, 19/22; corregir serialización POSIX y UTF-8 sin relajar rechazo de rutas externas ni tocar evidencia. Revalidar y push normal; T21 PENDIENTE. |

| 2026-11-08 | 20 | COMPLETA | `bb03e65` corrección CI; cierre documental en este commit | Gate acumulado repetido: 541 pipeline, API 35, tablero 55/frozen/lint/build, lock/sync/Ruff, registro, 24+24 contratos y 49/68 hashes verdes. Cuatro regresiones POSIX inicialmente rojas y caso CP1252 verdes. | APPROVED_WITH_LIMITATIONS; serialización portable sin aceptar entradas ambiguas ni tocar ciencia/evidencia. 20/22, T21 PENDIENTE, ninguna activa/bloqueada. Segundo push normal y todos los checks del nuevo HEAD deben verificarse; sin merge. |

| 2026-11-08 | 21 | EN CURSO | Tras `5eee835`; base funcional `0ed1363` | Preflight repetido: repositorio/rama correctos, árbol limpio, PR #1 abierto hacia main, T20 COMPLETA y 20/22. Documentación obligatoria leída; `$skill-creator` y su validador disponibles. | Crear únicamente cuatro skills canónicas bajo `.agents/skills/`, catálogo, integración breve con agentes/Claude, capítulo del manual, pruebas estructurales y evaluaciones secas. Sin ciencia real, datos privados, secretos, publicación, push ni T22. |

| 2026-11-08 | 21 | COMPLETA | `396d262` skills; `09fe3fc` manual; `91e8baf` pruebas; `766e5d5` cierre | Cuatro validaciones oficiales y cuatro evaluaciones secas verdes; lock/sync/Ruff, 549 pipeline, API 35, tablero 55/frozen/lint/build, registro VALID, contratos 24+24, checkout Windows y 127 enlaces verdes. | [Recibo de skills](docs/evidence/task21/skills-validation.json). T16, EXP001/EXP002, 49 archivos protegidos, 16 recibos previos, identidad N=3 y 22 JSON intactos. Sin entrenamiento, datos privados, secretos, push, merge, nuevo PR ni T22. Progreso 21/22; ninguna tarea activa o bloqueada. |

| 2026-11-08 | 21 | COMPLETA | `1cca905` reconciliación; recibo y registro en este commit | Auditoría documental posterior al cierre: enlaces, comandos y cuatro skills verdes; gate acumulado con 549 pipeline, API 35, tablero 55, registro VALID, contratos 24+24 e integridad protegida aprobada. | [Recibo de auditoría](docs/evidence/task21/documentation-audit.json). Se corrigieron solo documentos vigentes; historia y evidencia cerradas intactas. Persisten limitaciones científicas/de seguridad documentadas y gates externos antes del merge. Estado 21/22, T22 PENDIENTE, ninguna activa/bloqueada. |

### Riesgos de la extensión operacional

- Un recibo operativo no puede reemplazar historia: destino exclusivo bajo pipeline/data/.
- Un error de caché no autoriza reparación automática ni debilitar hashes o inventario.
- El helper no certifica ni entrena; el canónico resultante continúa provisional.
- CI histórica no valida commits nuevos: T26 debe comprobar su HEAD remoto.
- Las numeraciones históricas se conservan; DEC-027 controla la nueva secuencia.

## 7. Decisiones y desviaciones

Toda desviación debe registrarse antes de continuar.

| ID | Fecha | Decisión o desviación | Motivo | Impacto | Aprobación |
|---|---|---|---|---|---|
| DEC-001 | 2026-11-07 | Implementar todo en una sola rama y un único PR. | Regla del proyecto. | Exige commits pequeños y validaciones acumulativas. | Aprobada |
| DEC-002 | 2026-11-07 | Usar inicialmente Hugging Face y Zenodo con adquisición desacoplada. | Acceso público, reproducibilidad y migración futura. | Requiere manifiestos y adaptadores comunes. | Aprobada |
| DEC-003 | 2026-11-07 | Crear el E2E bajo `pipeline/` sin reorganizar el despliegue existente. | Mantener el repositorio ordenado y reducir riesgo. | Dependencias y pruebas separadas. | Aprobada |
| DEC-004 | 2026-11-07 | Prohibir celdas Markdown hasta autorización formal. | Regla del proyecto. | Los notebooks no incorporarán narrativa Markdown inicialmente. | Aprobada |
| DEC-005 | 2026-11-07 | El workflow pipeline-ci se incorporará en la tarea 4 junto con el proyecto Kedro, de modo que nazca ejecutable y validado, no como un placeholder. | Evitar sobreingeniería y checks rotos sobre archivos inexistentes. | Evidencia de tarea 4 ampliada; tarea 2 cubre componentes existentes. | Aprobada por el prompt 2 |
| DEC-006 | 2026-11-07 | Aplazamiento original hasta publicar el único PR, ahora resuelto para CI: PR #1 abierto; siete checks aprobados sobre 61159d9, incluidos los cuatro originales y matriz Ubuntu/Windows/macOS. | Runs 42424636017, 42424636020, 42424636002 y 42424636145; logs y tres artefactos revisados. Se conserva evidencia histórica de tareas anteriores. | Ruleset, aprobación independiente y checks verdes de la revisión final siguen siendo obligatorios antes del merge. Reviews vacías; ruleset no verificado. El usuario autorizó solo publicar los cinco commits y ejecutar CI, sin merge ni force push. | Aplazamiento aprobado por prompt 3; actualización y autorización explícitas del chat de tarea 15 |
| DEC-007 | 2026-11-07 | Ejecutar los comandos de herramientas desde la raíz con `uv run --directory pipeline ...`; mantener `--project pipeline` en lock y sync. | En uv 0.11.19, `--project` selecciona el entorno sin cambiar cwd: Kedro no descubre el subproyecto y responde No such command run. `--directory` funciona y limita Ruff y pytest al subproyecto. | Un único comando documentado para el E2E: `uv run --directory pipeline kedro run --pipelines synthetic`; sin wrapper ni configuración Kedro en la raíz. | Adaptación reproducible permitida por el prompt 4 |
| DEC-008 | 2026-11-07 | Migrar desde blobs inmutables de V2 `916a69f3bb73f2ffbb0ec038b8bef887ee91adf1`, sin escribir en V2. | El árbol V2 ya estaba sucio y su inventario cambió externamente durante la tarea 6. | Se preservaron esos cambios; no se afirma identidad del árbol ajeno. Al control posterior estaba limpio, HEAD externo `e5fc87ae79efa87e8526643626ecb494d1dcbb76`, origin/main aún en el commit autorizado. Esta implementación no creó ese commit ni cambió referencias V2. Huellas y paridad verificadas; no se usó el CSV local de 426 MB. | Fuente fijada y solo lectura autorizadas por el prompt de tareas 6–7; concurrencia registrada |
| DEC-009 | 2026-11-07 | Distinguir exclusión científica de 2025 y regresiones del producto publicado. | Las suites existentes de API/tablero, cuya ejecución completa es obligatoria, leen JSON históricos publicados de 2025 para validar contratos y servicio. | No se afirma ausencia global de lecturas de esos artefactos. El pipeline y sus tests bloquean publicaciones y no leen/utilizan observaciones o etiquetas científicas de 2025; esos JSON no participan en preparación, selección o ajuste. | Alcance de regresiones exigido por el prompt y separación científica de la arquitectura; distinción registrada |
| DEC-010 | 2026-11-07 | Adoptar arnés mensual mínimo con calentamiento 2018, folds desde 2019 y disponibilidad estrictamente anterior al origen. | Las fuentes V2 describen ocho ventanas y permiten igualdad al cierre mensual, sin reconstrucción autorizada de cohortes/preparadores privados en estas tareas. | Protocolo V3 reproducible sobre datos artificiales 2018–2024; ocho ventanas, selección interna y replay originales NOT_REPRODUCED. No se atribuye paridad científica. | Contrato mínimo y declaración NOT_REPRODUCED autorizados por el prompt de tareas 8–10 |
| DEC-011 | 2026-11-07 | Calibración mínima original/sigmoide, Brier con empate a original, grilla fija y cota FAR absoluta explícita; persistencia de no exceso adaptada a no nuevo inicio. | La etiqueta es inicio y la persistencia de exceso histórica no define una referencia equivalente; sin alertas, FAR es ausente. El contrato mínimo no migra bins/gap ni utilidad relativa humana de V2. | Sin defaults operativos ni override silencioso. scikit-learn 1.7.2 evita optimizador casero; SciPy 1.18.1 aplica expit estable y es dependencia de sklearn, ambas fijadas como en V2. Diferencias y soporte artificial NOT_REPRODUCED documentados; decisiones sintéticas no autorizan modelos/umbrales/campeón. | Implementación mínima y adaptación explícita autorizadas por el prompt; sin aprobación científica u operativa |
| DEC-012 | 2026-11-07 | Evaluar sobre soporte común de etiquetas conocidas/contexto explícito, conservando predicciones ausentes como invalidez compartida, y bootstrap municipal descriptivo. | Evitar denominadores distintos, cambios de umbral en evaluación e intervalos engañosos con pocos conglomerados. | AP/AUROC/Brier/sensibilidad/FAR/volumen, estratos y curvas solo diagnósticas. Mínimo configurable de cinco municipios por defecto; réplicas indefinidas no se sustituyen. Bootstrap histórico por cuatro ventanas/cohortes V2 NOT_REPRODUCED; revisión y reproducción real pendientes. | Protocolo municipal y límites solicitados por prompt tareas 11–12; sin aprobación científica |
| DEC-013 | 2026-11-07 | Tracking local opt-in con mlflow-skinny y backend SQL mínimo fijado; store/repositorio SDK explícitos y URI lógicas sin rutas privadas. | La API fluida/URI file estándar añade estado implícito y normaliza rutas; no se requieren servidores, UI o modelos. | Ciencia no importa MLflow; allowlists y agregados inmutables, recibo separado, telemetría desactivada y errores propagados. Grupo opcional, E2E probado sin SDK. APIs de store/repositorio requieren revalidación en upgrades; recuperación por adaptador, no UI/resolver genérico. Experimentos/jerarquías/replay V2 NOT_REPRODUCED, sin backend remoto. | Adaptador local mínimo autorizado por prompt, probado con instalación limpia; sin validación científica |
| DEC-014 | 2026-11-07 | Reabrir como BLOQUEADA la tarea 12 por cambio concurrente posterior al commit de cierre. | Apareció una carpeta no versionada datos/resultados/datos-crudos/ después de verificar árbol limpio en a450c52. No pertenece a los cambios preparados/validados y está bajo una ruta protegida que puede contener datos no autorizados. | En ese momento se conservaron código y pruebas verdes, el progreso volvió a 11/20 y la antigua tarea 13 no comenzó. DEC-015 resolvió posteriormente el incidente. | Detención y preservación exigidas por las restricciones del prompt; sin autorización para alterar datos ajenos |
| DEC-015 | 2026-11-07 | Resolver DEC-014 ubicando la entrada local en `datos/datos-crudos/` y excluyéndola explícitamente de Git. | Separar datos de entrada de la frontera publicada `datos/resultados/` y evitar versionar microdatos pesados. | Tarea 12 vuelve a `COMPLETA`; el incidente histórico permanece registrado; el progreso pasa a 12/21. | Aprobada por la nueva ubicación de datos y materializada en `4d775ae` |
| DEC-016 | 2026-11-07 | Distribuir solo las cinco fuentes crudas mediante un release privado y construir la tabla canónica dentro de Kedro. | Evitar depender de derivados preparados fuera del E2E y garantizar trazabilidad y repetibilidad desde la fuente. | Se inserta la tarea 13; las antiguas 13–20 pasan a 14–21. `raw_temporal_quarantine` se ejecuta antes de productores; `domain/canonical.py` y `guard_development` se reutilizan; la certificación reconstruye N=3 en espacios aislados y falla ante cualquier diferencia. El release derivado previo queda prohibido. | Aprobada por el equipo; diseño v6 |
| DEC-017 | 2026-11-07 | Certificar tarea 13 con perfil sintético explícito de dos municipios/84 meses y JSON determinista sin pérdida; probar separadamente la cuadrícula aprobada de 182.886 claves con dimensión artificial. | Los hashes y tamaños reales no pueden sustituirse por fixtures pequeños; la reproducción científica real pertenece a tarea 16. | El perfil aprobado mantiene inventario y cobertura fijos. Los CLI habilitan solo el fixture; cada worker copia cinco crudos a inbox nuevo, verifica integridad antes y después y reconstruye sin derivados. Serialización incluye esquema/tipos/orden/nulos/valores exactos; N=3 compara bytes completos. No se afirma reproducción ni rendimiento del release real. | Adaptación sintética y formatos locales autorizados por el prompt de tarea 13; sin aprobación científica |
| DEC-018 | 2026-11-07 | Migrar el publicador con caracterización fija, contrato JSON Schema autónomo derivado de API e invariantes, y manifiesto en .publication/manifest.json. | No importar app desde pipeline, conservar el glob de resultados y auditar overrides. | jsonschema 4.23.0 fijado en pipeline; pruebas externas contrastan snapshot y salidas con Pydantic/Zod. El desempate físico demostrado en 32b6d06 se corregirá en commit separado usando identificador solo ante empate exacto, sin cambiar cobertura/coste; se ordenarán listas de forma estable. INELIGIBLE no producido por legado se conserva como NOT_CALCULATED, con aceptación contractual probada. Staging completo, reemplazo por archivo, backups/rollback ante excepciones; sin aislamiento multiarchivo ni garantía de recuperación ante fallo del filesystem/pérdida eléctrica. | Determinismo, validación y publicación segura solicitados por el prompt; sin promoción científica |

| DEC-019 | 2026-11-07 | Portabilidad cerrada exclusivamente con fixtures y evidencia real por plataforma. | Tras autorizar el usuario el push de los cinco commits, CI nativa Ubuntu/Windows/macOS aprobó 463 + 12 pruebas y cuatro CLI; Mac local y Colab real ya estaban verdes. | Siete checks success; artefactos ZIP verificados por SHA-256; lock, N=3, semántica, métricas y publicación idénticos entre sistemas. Tarea 15 COMPLETA, 15/21; tarea 16 no comienza. El cierre documental adicional queda local porque la autorización de push especificó cinco commits. | Alcance y autorización explícitos del prompt/chat de tarea 15; sin autorización de merge o force push |


| DEC-020 | 2026-11-07 | Bloquear tarea 16 antes de implementar o adquirir datos por precondiciones incompletas. | HF_TOKEN no está disponible en el entorno del agente; la configuración versionada sigue siendo sintética y no fija el nuevo dataset privado/revisión. La disponibilidad, autorización e inventario remotos no pueden acreditarse. | Mantener 15/21 y tarea 17 PENDIENTE. No inferir identidad/revisión, recuperar tokens cacheados ni sustituir por el release derivado prohibido. Solo registrar el bloqueo; preámbulo, línea base local completa, diagnóstico de memoria, adquisición y reproducción real pendientes. Reanudar cuando estén declaradas identidad inmutable y credencial de entorno; la suficiencia experimental se verificará antes de cualquier experimento. | Detención y registro exigidos explícitamente por las precondiciones del prompt de tarea 16 |

| DEC-021 | 2026-11-07 | Fijar tarea 16 a `sat-dengue/data_raw@a1a7f237a4baa6ffa848fabeef474f811f3b3f33` y admitir Listados_DIVIPOLA.xlsx solo como auxiliar remoto. | Identidad y revisión aprobadas por el usuario; Excel presente en el release, sin autorización de uso científico. | Se elige ignorar su descarga. El adaptador adquiere exclusivamente los cinco archivos aprobados y Kedro rechaza cualquier sexto archivo en el bundle/manifiesto científico. Ninguna lectura del Excel para construcción canónica, transformaciones o aprendizaje; hashes/tamaños del contrato se conservan. | Autorización explícita del usuario en la reanudación de tarea 16 |

| DEC-022 | 2026-11-07 | Admitir estrictamente fechas epidemiológicas día/mes/año con medianoche localizada `12:00:00 a. m.` y espacio normal o NBSP. Bloquear una fuente no vacía sin ninguna fecha interpretable. | Perfil completo de INI_SIN: dengue 1.705.471 fechas localizadas + 133 vacías; grave 50.098 + 3 vacías. En 1.042.282 registros el primer componente supera 12; ninguno tiene segundo componente mayor que 12. La convención es día/mes, sin inferencia ni fallback. | Se conserva INI_SIN y cuarentena previa; fechas imposibles o formatos distintos siguen inválidos. Parser puro con caché acotada dentro de cada proceso; ninguna caché derivada compartida por N=3. Se reinicia la construcción; no se certifican los pilotos interrumpidos. | Adaptación de formato sustentada por inspección de claves y autorizada por la ejecución/diagnóstico de tarea 16; sin cambio de política científica |

### Autorización vigente de fábrica

| ID | Fecha | Decisión o desviación | Motivo | Impacto | Aprobación |
|---|---|---|---|---|---|
| DEC-023 | 2026-11-07 | Adoptar T16-FACTORY-XGB-S53-v1 únicamente para reproducibilidad E2E de fábrica V3; V2 queda como procedencia. | Aprobación explícita del equipo comunicada por el usuario. | Resuelve el bloqueo anterior; receta fija, sin G, presupuesto, HPO, refit, campeón, G5 o uso operativo. FAR se selecciona sin evaluación y el resultado posterior se reporta sin reajuste. Cierre técnico por procedimiento reproducible, no por rendimiento; detener antes de tarea 17. | Autorización explícita del chat; mecanismo y fecha de registro en el documento normativo, sin inventar integrantes o fecha formal del acta. |
| DEC-024 | 2026-11-07 | Insertar como tarea 17 la generalización de la fábrica para registrar, ejecutar, conservar y comparar múltiples experimentos aprobados; desplazar las antiguas tareas 17–21 a 18–22. | La validación T16 demostró reproducibilidad de una receta, pero el ejecutor actual está cerrado a esa única especificación y el tracking V3 aún no reproduce el registro experimental de V2. | T16 continúa inmutable. Un pipeline separado incorporará registro y estados cerrados, protocolos/configuraciones con hashes, evidencia append-only, MLflow local padre/hijos, conclusiones y comparación. No incluye nuevas familias, HPO, campeón, modelos pesados, servicio remoto ni ejecución científica real. Las referencias históricas a tareas anteriores a DEC-024 conservan su numeración original. | Autorización explícita del usuario para actualizar las hojas de ruta antes de continuar. |
| DEC-025 | 2026-11-07 | Detener T17 en preflight por contradicciones documentales, sin modificar código. | PLAN_pipeline_e2e_experimentos_sat_dengue.md, sección 9, exige ruleset verificado como gate cero antes de implementar; su sección 6 y DEC-006 sitúan ese requisito antes del merge. Además, el párrafo final de este plan denomina vigente un cierre 16/21, mientras cabecera, tabla y DEC-024 establecen 16/22. | T17 BLOQUEADA, progreso 16/22 y ninguna tarea activa. Pendiente reconciliar el momento exigido para verificar ruleset y actualizar o identificar como histórico el cierre final; se conservan los textos en conflicto para revisión. T16 y cambios preexistentes intactos; no se ejecutan suites ni experimentos. | Detención exigida por precondición 4 del pedido actual y sección 9 de plan.md; no se elige silenciosamente una interpretación. |
| DEC-026 | 2026-11-07 | Resolver DEC-025: el ruleset y la aprobación independiente son gates obligatorios antes del merge, no antes de implementar en la rama; el conteo vigente es 16/22. | DEC-006 y la sección de gobernanza del diseño ya fijan el momento correcto. El texto de riesgo era demasiado estricto y el cierre 16/21 no había incorporado la renumeración de DEC-024. | T17 vuelve a `PENDIENTE`, sin tarea activa ni bloqueada. La implementación puede comenzar; merge continúa prohibido hasta verificar ruleset, aprobación independiente y checks finales verdes. Los registros históricos 15/21 y 16/21 anteriores a DEC-024 no se reescriben. | Reconciliación documental solicitada tras el preflight de T17. |

| DEC-027 | 2026-11-09 | Ampliar la hoja de ruta a 27 tareas por revisión humana: insertar T22–T24 operativas, trasladar la anterior T22 a T25 y reservar T26–T27 para fase 2. | La auditoría encontró caché sin diagnóstico controlado, recibos que sobrescriben T16 y una interfaz operacional no portable. | Fase 1 autorizada solo para caché/recibos, helper adquisición → canonical_build provisional, documentación y gates locales. T16, EXP001/EXP002, identidades y 22 JSON son inmutables. Sin cambios científicos, ampliación temporal, canal condicionado, EXP003 ni investigación climática. El trabajo científico posterior requerirá otro alcance después del merge. T25–T27 quedan pendientes; esta autorización no permite push, publicación remota, entrenamiento ni merge. | Instrucción explícita del usuario de 2026-11-09; sin aprobación científica implícita. |

## 8. Condición de finalización

El trabajo solo puede considerarse terminado cuando:

- las 27 tareas estén `COMPLETA`;
- T22–T24 acrediten caché controlada, recibos exclusivos ignorados, comando portable
  de adquisición/construcción provisional y gate acumulado sin datos privados;
- los gates incluyan regresiones, clon limpio, preservación de evidencia y contratos;
- T26–T27 se ejecuten solo bajo autorización posterior, con CI remota del HEAD final,
  ruleset verificado, aprobación independiente y conversaciones resueltas;
- la fábrica pueda registrar, ejecutar y comparar experimentos aprobados sin
  sobrescribir T16 ni depender exclusivamente de un store MLflow local;
- el clon limpio ejecute el E2E sintético con un comando;
- los cuatro integrantes puedan adquirir el release privado crudo con cuentas y
  credenciales individuales, sin depender de otro integrante en cada corrida;
- el pipeline funcione con proveedor local, Hugging Face, Zenodo y S3 simulado;
- el manifiesto acepte solo los cinco archivos, tamaños y hashes aprobados;
- Kedro construya desde crudos una cuadrícula única de 1.122 municipios por 163
  meses (`2011-06` a `2024-12`), equivalente a 182.886 claves;
- la certificación canónica N=3 produzca esquema, orden, tipos, claves, valores,
  nulos, digest semántico y SHA-256 serializado idénticos;
- la cuarentena previa y `guard_development` impidan que 2025 llegue a cualquier
  transformación o componente aprendido, incluidos cruces T+1/T+2 desde 2024;
- el despliegue existente continúe funcionando;
- el publicador produzca JSON aceptados por API y tablero;
- las pruebas de pipeline, API y tablero estén verdes;
- no existan secretos ni archivos pesados en Git;
- la revisión científica y la revisión de seguridad estén aprobadas;
- el único PR contenga una descripción verificable de cambios, pruebas y riesgos.

## 9. Referencia de diseño

La única hoja de directrices y diseño detallado del E2E es
[`PLAN_pipeline_e2e_experimentos_sat_dengue.md`](PLAN_pipeline_e2e_experimentos_sat_dengue.md).
La arquitectura implementada y sus fronteras versionadas también se documentan en
[`docs/architecture/pipeline-e2e.md`](docs/architecture/pipeline-e2e.md).

Este `plan.md` es la única fuente de verdad sobre tareas, numeración, estados,
dependencias y progreso. El plan de diseño no mantiene un estado operativo paralelo.

Antes de implementar la tarea 13, ese documento debe sincronizarse con DEC-015 y
DEC-016. La propia tarea 13 no puede cerrarse mientras conserve el supuesto de un
release derivado o público como entrada científica.

Si existe contradicción entre ambos documentos, se debe detener la implementación,
registrar la discrepancia en la sección 7 y resolverla antes de continuar.


### Reanudación de tarea 16: fábrica autorizada

El equipo autorizó explícitamente T16-FACTORY-XGB-S53-v1 para reproducibilidad
E2E de fábrica. La [especificación normativa V3](docs/decisions/task16-experiment-specification.md)
y `pipeline/conf/base/parameters_experiment.yml` fijan la receta, sin campeón,
uso operativo o tarea 17. Se conserva la evidencia anterior. Los nombres de
integrantes y fecha formal del acta no se comunicaron; el documento registra el
mecanismo de aprobación recibido y la fecha de registro, sin inventarlos.
Esta autorización resolvió el bloqueo anterior. Al reanudar se mantuvo 16 EN CURSO
y 15/21 hasta comprobar los gates y N=3. Ese conteo pertenece a la numeración
anterior a DEC-024. Cierre de T16: COMPLETA e intacta. Estado vigente: 21/27, T1–T21 COMPLETAS, T22–T27 PENDIENTES y ninguna tarea activa ni bloqueada.
