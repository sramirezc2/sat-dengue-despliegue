# Hoja de ruta de implementación — Pipeline E2E SAT DENGUE

**Versión:** 1.0
**Fecha de creación:** 7 de noviembre de 2026
**Estado general:** Implementación de tarea 10 en curso
**Repositorio definitivo:** `sramirezc2/sat-dengue-despliegue`
**Rama única de implementación:** `feature/pipeline-e2e`
**Entrega:** un único Pull Request

## 1. Objetivo

Implementar en el repositorio definitivo un pipeline E2E reproducible que permita
adquirir, validar y preparar datos, entrenar candidatos, evaluarlos y publicar
resultados compatibles con la API y el tablero existentes.

La implementación debe conservar la separación:

```text
pipeline/ -> datos/resultados/ -> app/api/ -> app/dashboard/
```

`pipeline/` será un proyecto Kedro autocontenido. La adquisición de datos estará
desacoplada mediante adaptadores intercambiables. Inicialmente se utilizarán
Hugging Face y Zenodo, con una extensión compatible con AWS S3 para una migración
futura.

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
- Cada cambio de comportamiento debe tener pruebas proporcionales.
- Una tarea no se marca como completa si sus validaciones no están verdes.
- `datos/resultados/` es la única frontera de publicación hacia la API.
- La API no importa código de `pipeline/` y el pipeline no escribe dentro de
  `app/`.
- 2025 permanece excluido del desarrollo y se registra como evaluación utilizada.

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
| 5 | Implementar releases y adquisición desacoplada | `COMPLETA` | 4 | `DataSource`, `ResolvedBundle`, manifiestos, caché, hashes y adaptadores local, Hugging Face, Zenodo y S3 simulado. |
| 6 | Migrar el panel canónico desde V2 | `COMPLETA` | 5 | Productores migrados con procedencia y paridad exacta sobre muestra artificial de 167 filas (no reproducción real). |
| 7 | Implementar etiquetas y controles temporales | `COMPLETA` | 6 | Inicio T+1/T+2, elegibilidad solo en T, ausencias, roles y compuerta previa a etiquetas/consumidor; 47 pruebas nuevas. |
| 8 | Recuperar o reimplementar el arnés rolling-origin | `COMPLETA` | 7 | Arnés mensual expansivo, madurez estricta, digest y 19 pruebas nuevas; protocolo histórico de ocho ventanas `NOT_REPRODUCED`. |
| 9 | Implementar adaptadores de modelos | `COMPLETA` | 8 | Protocol, configuración/semilla, registro neutral, protección de entradas y probabilidades; 28 pruebas nuevas. Estimadores reales pendientes. |
| 10 | Implementar calibración, umbrales y líneas base | `EN CURSO` | 9 | Separación temporal correcta, umbrales congelados y líneas base con información simétrica. |
| 11 | Implementar métricas e incertidumbre | `PENDIENTE` | 10 | Métricas emparejadas, estratos, curvas de volumen e intervalos definidos. |
| 12 | Agregar trazabilidad de corridas | `PENDIENTE` | 11 | MLflow, Git SHA, release, hashes, proveedor, parámetros, entorno y `run_id`. |
| 13 | Migrar la publicación sin romper el despliegue | `PENDIENTE` | 12 | Lógica trasladada al pipeline; script temporal compatible; contrato API/tablero equivalente. |
| 14 | Cerrar portabilidad | `PENDIENTE` | 13 | Ejecución sintética verde en macOS, Windows, Linux y Colab. |
| 15 | Ejecutar reproducción sintética y real | `PENDIENTE` | 14 | Fixture y release público 2018–2024 ejecutados; 2025 no fue leído. |
| 16 | Realizar revisión científica independiente | `PENDIENTE` | 15 | Auditoría de etiquetas, fuga, folds, líneas base, métricas y correspondencia con la bitácora. |
| 17 | Documentar operación, límites y migraciones | `PENDIENTE` | 16 | Guía de un comando, Colab, troubleshooting, publicación y migración Hugging Face/Zenodo hacia AWS. |
| 18 | Ejecutar revisión de seguridad | `PENDIENTE` | 17 | Revisión de datos, licencias, tokens, secretos, dependencias y superficies de red. |
| 19 | Registrar capacidades reutilizables | `PENDIENTE` | 18 | Skills, agentes o herramientas útiles identificados y documentados. |
| 20 | Elaborar reporte ejecutivo | `PENDIENTE` | 19 | Resumen final de entregables, validaciones, limitaciones y decisiones pendientes. |

## 5. Secuencia de integración

Aunque toda la implementación terminará en un solo PR, los commits deben conservar
esta secuencia lógica:

```text
arquitectura y gobernanza
        -> línea base del despliegue
        -> esqueleto de pipeline
        -> adquisición y contratos
        -> preparación científica
        -> entrenamiento y evaluación
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
| Tareas completas | 9/20 |
| Tarea activa | 10 — Calibración, umbrales y líneas base |
| Tareas bloqueadas | 0 |
| Última tarea completada | 9 — Adaptadores de modelos |
| Última actualización | 7 de noviembre de 2026 |

### Registro de ejecución

| Fecha | Tarea | Estado nuevo | Commit | Validaciones | Observaciones |
|---|---:|---|---|---|---|
| 2026-11-07 | 1 | COMPLETA | `e794bce` (arquitectura); `60692c3` (hoja de ruta y cierre, sustituye a `fd9eae7`) | Rutas y enlaces revisados; diff documental sin errores de espacios; plan versionado. | Arquitectura y hoja de ruta compartidas. |
| 2026-11-07 | 2 | COMPLETA | `f67d1c6` | API: 22 pruebas; tablero: lint sin errores (6 advertencias), 33 pruebas y build; publicación: 22 JSON en API y prueba Zod verde; YAML, shell, filtros y diff validados localmente. | Implementación y validación local completas. GitHub Actions no fue ejecutado ni validado remotamente. CI remota, ruleset, aprobación independiente y checks requeridos siguen pendientes y son obligatorios antes del merge (DEC-006). |
| 2026-11-07 | 3 | COMPLETA | `5ec813e` | API: 28 pruebas; tablero: instalación con lockfile congelado, lint sin errores (6 advertencias), 33 pruebas y build; Docker Compose construido sin caché desde checkout temporal, 3 servicios activos, 22 resultados, Meta y Tolima disponibles, consultas y smoke test verdes; volumen verificado tras recrear contenedores; diff sin errores. | El estado inicial arrancaba con volumen vacío, 0 resultados y consultas 404. La imagen ahora siembra el volumen; S3 descarga siempre a temporal, comprueba tamaño y contrato, y reemplaza atómicamente. SHA-256 queda diferido a la tarea 13 porque aún no existe un hash remoto confiable. Recursos Docker temporales eliminados. |
| 2026-11-07 | 4 | COMPLETA | `20897e9` | `uv lock --check --project pipeline`, `uv sync --locked --project pipeline`, `uv run --directory pipeline ruff check .`, `uv run --directory pipeline pytest` (7 pruebas) y `uv run --directory pipeline kedro run --pipelines synthetic`: verdes, también desde clon temporal limpio del commit con entorno nuevo. Métricas sintéticas: 1 fila, MAE 5, MSE 25. Regresión: API 28 pruebas; tablero lint sin errores (6 advertencias), 33 pruebas y build node_server; YAML, shell, filtros, enlaces y diff válidos. | `Pipeline quality` implementado y validado localmente; no se ejecutó remotamente por DEC-006. Python 3.12, Kedro 1.7.0, pytest 9.2.0, Ruff 0.17.4 y uv 0.11.19. Adaptación CLI registrada en DEC-007. CLI actualizada en `1dad0ec`; solo persisten avisos internos de OmegaConf. Sin publicación, datos reales, secretos ni artefactos pesados generados fuera del entorno ignorado; árbol del clon limpio. |
| 2026-11-07 | 5 | COMPLETA | `1dad0ec` (CLI Kedro vigente); `a308c78` (adquisición) | `uv lock --check --project pipeline`, `uv sync --locked --project pipeline`, Ruff, pytest (71 pruebas: 64 nuevas) y `kedro run --pipelines synthetic` verdes, también desde clon temporal limpio de `a308c78` con entorno nuevo. API: 28 pruebas; tablero: lint sin errores (6 advertencias), 33 pruebas y build node_server. YAML, filtros, shell, diff y exclusión de `pipeline/data/` verificados. | Contratos inmutables, fábrica única y caché común por release/digest; cada hit verifica tamaño y SHA-256; transferencias temporales y reemplazo atómico por archivo. Local, HF y Zenodo probados con archivos/dobles locales; S3 con cliente falso y claves bajo prefijo de revisión, sin AWS. Integración del resolver como nodo Kedro con configuración temporal, sin pipeline de adquisición pendiente de datos reales. Solo se agregó huggingface_hub 2.4.0 y sus dependencias transitivas; Zenodo usa HTTP de biblioteca estándar. Guard global de pytest bloquea red, DNS, imports inversos y acceso a publicaciones. No hubo descargas científicas reales ni credenciales. Identificadores, hashes e inventario del primer release público siguen pendientes; reproducción real en tarea 15. CI remota y ruleset pendientes por DEC-006. |

| 2026-11-07 | 6 | COMPLETA | `3ff23a560388c24b6eabe3a1427f6376c867da87` (implementación); `d5355e9` (cierre e inicio de 7) | Lock/sync, Ruff, 92 pruebas y E2E sintético verdes; verificación optativa de referencia V2 exacta; API 28; tablero lint sin errores (6 advertencias), 33 pruebas y build; diff sin errores. | V2 `j-mauro-r/SAT-Dengue-V2@916a69f3bb73f2ffbb0ec038b8bef887ee91adf1`, blobs y SHA-256 documentados en `docs/decisions/v2-scientific-migration.md`. 167 filas artificiales 2018–2024, Meta/Tolima; igualdad de tabla, tipos, nulos, roles, X y cobertura. NumPy 2.5.4 y pandas 3.0.6 fijados. Pruebas normales bloquean V2/red/app/publicaciones; no CSV de 426 MB ni datos científicos reales/2025. No se escribió en V2; cambios externos de ese árbol registrados en DEC-008. La evidencia es sintética; release real pendiente en tarea 15. |
| 2026-11-07 | 7 | COMPLETA | `8ed8293391620a955f8756c92b8a0b64a74eb0e9` | Lock/sync, Ruff, 139 pruebas (47 nuevas), E2E y siete centinelas explícitos verdes; clon temporal con entorno nuevo, árbol idéntico al commit de implementación, instalación, Ruff, 139 pruebas, centinelas y E2E verdes. API 28; tablero lint sin errores (6 advertencias), 33 pruebas y build; cuatro YAML, filtros y 19 bloques shell válidos; diff/imports/patrones de secretos/tamaños revisados. | Mismo commit histórico V2; referencia adicional de siete estados artificiales hasta junio de 2024 con paridad exacta en ambos horizontes. Inicio = anterior 0 y objetivo 1; ausencia preservada, elegibilidad solo en T. Rechazo por objetivo antes de leer etiquetas o invocar consumidor; no se leyó ni utilizó ninguna observación/etiqueta científica de 2025 en el pipeline. Centinelas solo con claves/marcadores artificiales. X/y separados, disponibilidad explícita, selecciones fijas sin rolling-origin ni reserva rígida de 2024. Ninguna escritura en V2; estado externo final documentado en DEC-008. Las regresiones de producto consultan JSON publicados históricos (DEC-009). Sin CSV de 426 MB, modelos, datos reales nuevos, notebooks, push o PR. Reproducción real pendiente en tarea 15; CI remota y ruleset pendientes (DEC-006); CLI conserva DEC-007. Tarea 8 no iniciada. |

| 2026-11-07 | 8 | COMPLETA | `672c8aaf1d863d6562686b67d560af7625876999` | Estado inicial exacto `f5c8768`, árbol limpio y 139 pruebas verdes; gate de tarea: lock/sync, Ruff, 158 pruebas (19 nuevas), suite específica y E2E sintético verdes; diff sin errores. | Fuente histórica fijada `916a69f3bb73f2ffbb0ec038b8bef887ee91adf1`, archivos/hashes/reglas en `docs/decisions/temporal-experiments.md`. Desarrollo artificial 2018–2024: 2018 calentamiento, folds mensuales desde 2019, T+1/T+2 separados, etiquetas disponibles estrictamente antes del consumo. Protocolo de ocho ventanas/cohortes/preparadores históricos `NOT_REPRODUCED`; sin paridad ni reproducción real. Sin nuevas dependencias, datos reales/2025, modelos científicos, notebooks, acceso a publicaciones o escrituras V2. Tarea 15, CI remota y ruleset pendientes. |

| 2026-11-07 | 9 | COMPLETA | `1b16058e3975b0003ade9fd4e7ccff61a542f8e7` | Lock/sync, Ruff, 186 pruebas (28 nuevas), 47 pruebas específicas de tareas 8–9 y E2E sintético verdes; diff sin errores. | Contrato neutral con identidad/configuración JSON/semilla, instancia nueva por fold, esquema/orden/tipos congelados, inferencia solo X, probabilidades y enlaces validados. Backend mutante rechazado y entrada original protegida. Misma ejecución rolling-origin para dos familias dobles. Procedencia/hashes históricos en `docs/decisions/temporal-experiments.md`. Sin dependencias nuevas ni estimadores reales; XGBoost/LightGBM/GAM, preparación y replay históricos pendientes/NOT_REPRODUCED. No modelos entrenados versionados, escrituras V2, publicaciones ni datos reales/2025. |

## 7. Decisiones y desviaciones

Toda desviación debe registrarse antes de continuar.

| ID | Fecha | Decisión o desviación | Motivo | Impacto | Aprobación |
|---|---|---|---|---|---|
| DEC-001 | 2026-11-07 | Implementar todo en una sola rama y un único PR. | Regla del proyecto. | Exige commits pequeños y validaciones acumulativas. | Aprobada |
| DEC-002 | 2026-11-07 | Usar inicialmente Hugging Face y Zenodo con adquisición desacoplada. | Acceso público, reproducibilidad y migración futura. | Requiere manifiestos y adaptadores comunes. | Aprobada |
| DEC-003 | 2026-11-07 | Crear el E2E bajo `pipeline/` sin reorganizar el despliegue existente. | Mantener el repositorio ordenado y reducir riesgo. | Dependencias y pruebas separadas. | Aprobada |
| DEC-004 | 2026-11-07 | Prohibir celdas Markdown hasta autorización formal. | Regla del proyecto. | Los notebooks no incorporarán narrativa Markdown inicialmente. | Aprobada |
| DEC-005 | 2026-11-07 | El workflow pipeline-ci se incorporará en la tarea 4 junto con el proyecto Kedro, de modo que nazca ejecutable y validado, no como un placeholder. | Evitar sobreingeniería y checks rotos sobre archivos inexistentes. | Evidencia de tarea 4 ampliada; tarea 2 cubre componentes existentes. | Aprobada por el prompt 2 |
| DEC-006 | 2026-11-07 | La validación remota de GitHub Actions y la activación del ruleset se aplazan hasta que se publique el único PR. Las validaciones locales de la tarea 2 fueron aprobadas. | No abrir un PR auxiliar ni afirmar una validación remota que no ocurrió. | CI remota, ruleset, aprobación independiente y checks requeridos siguen siendo condiciones obligatorias antes del merge. | Aprobada por el prompt 3 |
| DEC-007 | 2026-11-07 | Ejecutar los comandos de herramientas desde la raíz con `uv run --directory pipeline ...`; mantener `--project pipeline` en lock y sync. | En uv 0.11.19, `--project` selecciona el entorno sin cambiar cwd: Kedro no descubre el subproyecto y responde No such command run. `--directory` funciona y limita Ruff y pytest al subproyecto. | Un único comando documentado para el E2E: `uv run --directory pipeline kedro run --pipelines synthetic`; sin wrapper ni configuración Kedro en la raíz. | Adaptación reproducible permitida por el prompt 4 |
| DEC-008 | 2026-11-07 | Migrar desde blobs inmutables de V2 `916a69f3bb73f2ffbb0ec038b8bef887ee91adf1`, sin escribir en V2. | El árbol V2 ya estaba sucio y su inventario cambió externamente durante la tarea 6. | Se preservaron esos cambios; no se afirma identidad del árbol ajeno. Al control posterior estaba limpio, HEAD externo `e5fc87ae79efa87e8526643626ecb494d1dcbb76`, origin/main aún en el commit autorizado. Esta implementación no creó ese commit ni cambió referencias V2. Huellas y paridad verificadas; no se usó el CSV local de 426 MB. | Fuente fijada y solo lectura autorizadas por el prompt de tareas 6–7; concurrencia registrada |
| DEC-009 | 2026-11-07 | Distinguir exclusión científica de 2025 y regresiones del producto publicado. | Las suites existentes de API/tablero, cuya ejecución completa es obligatoria, leen JSON históricos publicados de 2025 para validar contratos y servicio. | No se afirma ausencia global de lecturas de esos artefactos. El pipeline y sus tests bloquean publicaciones y no leen/utilizan observaciones o etiquetas científicas de 2025; esos JSON no participan en preparación, selección o ajuste. | Alcance de regresiones exigido por el prompt y separación científica de la arquitectura; distinción registrada |

## 8. Condición de finalización

El trabajo solo puede considerarse terminado cuando:

- las 20 tareas estén `COMPLETA`;
- el clon limpio ejecute el E2E sintético con un comando;
- el release público se adquiera sin credenciales;
- el pipeline funcione con proveedor local, Hugging Face, Zenodo y S3 simulado;
- el desarrollo rechace cualquier dato de 2025;
- el despliegue existente continúe funcionando;
- el publicador produzca JSON aceptados por API y tablero;
- las pruebas de pipeline, API y tablero estén verdes;
- no existan secretos ni archivos pesados en Git;
- la revisión científica y la revisión de seguridad estén aprobadas;
- el único PR contenga una descripción verificable de cambios, pruebas y riesgos.

## 9. Referencia de diseño

La fuente arquitectónica versionada y disponible para todos los integrantes es
[docs/architecture/pipeline-e2e.md](docs/architecture/pipeline-e2e.md).

Si existe contradicción entre ambos documentos, se debe detener la implementación,
registrar la discrepancia en la sección 7 y resolverla antes de continuar.
