# T17 — administración de experimentos de V3

Fecha: 2026-11-07. Alcance autorizado por DEC-024 y reanudado tras DEC-026.
T17 queda completa técnicamente; no se inicia T18 ni se autoriza ciencia real.

## Diseño final

El [registro central](../experiments/registry.yml) contiene esquema versión 1 y
entradas cerradas con ID, slug, hipótesis, título, tipo, estado, protocolo y
SHA-256, configuración y SHA-256, pipeline, conclusiones, resultado científico y
champion_status. No hay imports en YAML. Rutas confinadas, symlinks, duplicados,
campos desconocidos, hashes alterados y recetas históricas reutilizadas fallan
cerrados. La configuración tiene JSON Schema cerrado independiente de T16.

`experiment_run` reutiliza `factory.engine` para preparación, guard V3, soportes
previos al primer ajuste, calibración/umbral, predicción previa a evaluación,
métricas y referencias. Los cambios compartidos se limitan a admitir uno o ambos
horizontes y proyectar el subconjunto canónico dentro del adaptador existente.
`factory_validation` conserva su validador exacto y el rechazo de sobrescritura.

Los estados experimentales son PROPOSED→APPROVED→RUNNING→COMPLETED|BLOCKED.
Cada intento tiene UUID, firma, terminal independiente, UTC, receta, semilla,
horizontes, métricas, decisiones, linaje y seis archivos agregados con inventario.
La firma incluye protocolo/configuración, datos, Git/dirty, código, lock y versiones.
La escritura exclusiva no reemplaza ejecuciones. El ejecutor no concluye ciencia:
tras éxito mantiene RUNNING hasta conclusiones humanas válidas; errores dejan
BLOCKED y un terminal FAILED/BLOCKED/KILLED que se propaga al llamador.

La comparación/listado lee únicamente registro y evidencia agregada. MLflow
extiende el backend local existente: un padre por ejecución y niños por horizonte
solo cuando hay comparación. El store no es fuente única de historia.
No se persisten modelos: solo hashes, sin necesidad de almacenamiento remoto.

## Aceptación y aprendizaje técnico

- EXP001: T+1/T+2, semilla 53, 33 predictores, cuatro rondas; ejecución
  `40800d46732940d1914f8fc2430bfb8e`, padre MLflow `c8d165f18173417b93d1abd37dc02bd0`
  y dos hijos.
- EXP002: T+2, semilla 71, dos predictores modelados, seis rondas; ejecución
  `b27dd78427ca486984c67b2b9b64d97f`, padre `d9c6e3a0654b403d99c25bf1c2d7f3f0`
  sin hijos redundantes.

Ambas son fixtures sintéticos con resultado NOT_APPLICABLE, conclusiones y
paquetes separados, no resultados científicos de dengue. La comparación T+2
produce 42 filas deterministas de candidato y referencias. Que coincidan algunas
métricas no borra las identidades diferentes. No se ajustó ninguna receta tras
observar esas métricas. La bitácora solo enlaza la capacidad de infraestructura.

Los recibos CLI se ejecutaron desde `6910efa`, EXP001 con dirty=false y EXP002 con
dirty=true por el estado/evidencia aún sin commit de EXP001. El guard posterior
`7c4004a` verifica los bytes efectivamente cargados y vuelve a comprobar protocolo;
la suite completa prueba de nuevo ambos E2E en copias temporales. Los recibos
anteriores no se repiten ni se editan para atribuirles otro código.

## Validaciones

[Recibo agregado](../evidence/task17/validation.json) y comandos en
[la guía de experimentos](../experiments/README.md).

| Gate local | Resultado |
|---|---|
| `uv lock --check` y `uv sync --locked` | Verdes; lock sin cambios |
| Ruff | Verde |
| Pipeline completo | 536 pruebas; 45 nuevas de T17; seis avisos OmegaConf existentes |
| Registro/estados/evidencia/tracking | Incluidos: coexistencia, firmas, rechazo de aprobación/receta alterada, rutas y symlinks, fallos/KILLED, cierre sin conclusiones, corrupción, bloqueo exclusivo y fallos de escritura/tracking |
| Kedro sintético previo | synthetic, canonical_build, canonical_reproducibility y deployment_publication verdes |
| Kedro `experiment_run` | EXP001 y EXP002 COMPLETED; inventarios, conclusiones y MLflow real verificados |
| API | 28 pruebas; un aviso de deprecación existente |
| Tablero | Instalación congelada, 33 pruebas, lint sin errores/seis advertencias y build node_server verdes |
| Contratos Pydantic/Zod | 24 documentos aceptados por ambos |
| Preservación | 49 SHA-256 iguales: 22 JSON, 16 recibos previos y resto de evidencia/configuración/documentos T16 |
| Adaptador T16 | Modelo JSON completo y probabilidades artificiales exactamente iguales frente a daf6ed5 |
| Higiene | Diff sin errores, escaneo local de patrones de secretos sin hallazgos, sin archivos nuevos pesados ni notebooks |

La identidad N=3 continúa siendo
`899ba8b2c48b69dbf2e9094a6efedfa838cbfe4c800bed25fa1823503d06d52f`
en los tres recibos históricos. No se descargaron fuentes privadas ni se repitió
la reproducción real de T16. [Snapshot protegido](../evidence/task17/preservation-baseline.json)
y [regresión artificial](../evidence/task17/t16-adapter-regression.json).

## Diferencias frente a V2 y límites pendientes

Se recuperan sus principios de registro, receta congelada, identidad verificable,
estados, evidencia, conclusiones incluso sin mejora y comparación. No se copian
runners por experimento, replay, microdatos, matrices, modelos ni jerarquías de
tracking que no aporten comparación. La procedencia local V2 y el commit revisado
están en la guía; no se escribió en V2.

La preparación conserva entrada completa de 33 predictores aunque la matriz
modelada sea menor; es un filtro conservador explícito, no una nueva política de
imputación. Solo existe xgboost_onset/v1. No hay HPO, G, presupuesto del canal,
campeón, selección automática ni autorización operativa. La comparación JSON no
convierte recetas/cohortes distintas en un análisis emparejado científico.

Una aprobación permite un intento por checkout; revisión de receta o reintentos
requieren nueva identidad y aprobación. Un paquete incompleto falla cerrado; un
error total del filesystem puede impedir un recibo, y un lock abandonado exige
investigar la interrupción antes de retirarlo. La validación estructural de
conclusiones no sustituye revisión científica independiente.

No se hicieron push, merge, force push ni PR adicional. La CI remota de esta
revisión no publicada, el ruleset y la aprobación independiente siguen pendientes
como condiciones antes del merge. La tarea 18 permanece PENDIENTE.
