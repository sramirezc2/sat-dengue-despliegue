# Hoja de ruta de implementación — Pipeline E2E SAT DENGUE

**Versión:** 1.0
**Fecha de creación:** 7 de noviembre de 2026
**Estado general:** Implementación iniciada
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
| 2 | Activar gobernanza y CI por componentes | `PENDIENTE` | 1 | Ruleset, CODEOWNERS, plantilla de PR y checks para pipeline, API, tablero y publicación. |
| 3 | Congelar y proteger la línea base del despliegue | `PENDIENTE` | 2 | Compose arranca desde clon limpio; salud y consulta válida funcionan; brechas existentes quedan corregidas o documentadas. |
| 4 | Crear el subproyecto `pipeline/` con Python, Kedro y uv | `PENDIENTE` | 3 | Estructura autocontenida, lock, CLI y E2E sintético mínimo sin afectar `app/`. |
| 5 | Implementar releases y adquisición desacoplada | `PENDIENTE` | 4 | `DataSource`, `ResolvedBundle`, manifiestos, caché, hashes y adaptadores local, Hugging Face, Zenodo y S3 simulado. |
| 6 | Migrar el panel canónico desde V2 | `PENDIENTE` | 5 | Productores migrados con procedencia y equivalencia sobre una muestra aprobada. |
| 7 | Implementar etiquetas y controles temporales | `PENDIENTE` | 6 | Etiquetas de inicio, elegibilidad, horizontes, ausencias y prueba centinela que rechaza 2025. |
| 8 | Recuperar o reimplementar el arnés rolling-origin | `PENDIENTE` | 7 | Ventana expansiva 2018–2024 reproducible; diferencias registradas como `NOT_REPRODUCED`. |
| 9 | Implementar adaptadores de modelos | `PENDIENTE` | 8 | Interfaz común para los enfoques del equipo sin duplicar evaluación. |
| 10 | Implementar calibración, umbrales y líneas base | `PENDIENTE` | 9 | Separación temporal correcta, umbrales congelados y líneas base con información simétrica. |
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
| Tareas completas | 1/20 |
| Tarea activa | Ninguna |
| Tareas bloqueadas | 0 |
| Última tarea completada | 1 — Formalizar arquitectura y fronteras |
| Última actualización | 7 de noviembre de 2026 |

### Registro de ejecución

| Fecha | Tarea | Estado nuevo | Commit | Validaciones | Observaciones |
|---|---:|---|---|---|---|
| 2026-11-07 | 1 | COMPLETA | `e794bce` (arquitectura); commit `docs(plan): add implementation roadmap` (cierre, sustituye a `fd9eae7`) | Rutas y enlaces revisados; diff documental sin errores de espacios; plan versionado. | Arquitectura y hoja de ruta compartidas. |

## 7. Decisiones y desviaciones

Toda desviación debe registrarse antes de continuar.

| ID | Fecha | Decisión o desviación | Motivo | Impacto | Aprobación |
|---|---|---|---|---|---|
| DEC-001 | 2026-11-07 | Implementar todo en una sola rama y un único PR. | Regla del proyecto. | Exige commits pequeños y validaciones acumulativas. | Aprobada |
| DEC-002 | 2026-11-07 | Usar inicialmente Hugging Face y Zenodo con adquisición desacoplada. | Acceso público, reproducibilidad y migración futura. | Requiere manifiestos y adaptadores comunes. | Aprobada |
| DEC-003 | 2026-11-07 | Crear el E2E bajo `pipeline/` sin reorganizar el despliegue existente. | Mantener el repositorio ordenado y reducir riesgo. | Dependencias y pruebas separadas. | Aprobada |
| DEC-004 | 2026-11-07 | Prohibir celdas Markdown hasta autorización formal. | Regla del proyecto. | Los notebooks no incorporarán narrativa Markdown inicialmente. | Aprobada |

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
