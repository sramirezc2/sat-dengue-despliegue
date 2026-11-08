# Manual de uso de la fábrica de experimentos

## Propósito

La fábrica permite registrar, aprobar, ejecutar, concluir y comparar entrenamientos sin sobrescribir su historia. Cada experimento queda unido a una hipótesis, una receta, una versión de los datos, una versión del código y un paquete de evidencia verificable.

Este manual aplica tanto a personas como a agentes de IA. Todas las acciones se realizan desde la raíz del repositorio y sobre una rama de trabajo. Ningún experimento autoriza por sí mismo un modelo campeón ni su uso operativo.

## Reglas esenciales

1. Use un identificador nuevo y consecutivo, por ejemplo `EXP003`. Un identificador ejecutado nunca se reutiliza.
2. Defina la hipótesis y la receta antes de entrenar. No cambie la receta después de observar los resultados.
3. Para repetir un entrenamiento, cree otro experimento con un identificador nuevo, aunque la receta sea idéntica. Así se conservan ambas ejecuciones.
4. No edite directamente una entrada cerrada del registro ni los archivos de evidencia.
5. No use `EXP001` ni `EXP002` como resultados científicos: son ejemplos técnicos con datos artificiales.
6. Los datos reales deben provenir del manifiesto privado aprobado. No entregue al pipeline una tabla canónica construida manualmente.
7. El periodo 2025 está excluido del aprendizaje. No modifique `reserved_start: 2025-01` ni los controles temporales.
8. No guarde tokens, datos crudos, matrices, modelos o predicciones en Git. `HF_TOKEN` debe existir únicamente como secreto del entorno.
9. La especificación, configuración y aprobación deben pasar por revisión mediante Pull Request antes de ejecutar un experimento científico.

## Archivos de cada experimento

Para `EXP003` deben existir:

```text
docs/experiments/EXP003/SPECIFICATION.md
pipeline/conf/experiments/EXP003.yml
docs/experiments/EXP003/registration.yml   # archivo auxiliar para registrar
docs/experiments/EXP003/CONCLUSIONS.md     # se crea después de ejecutar
```

El registro central está en:

```text
docs/experiments/registry.yml
```

La evidencia de cada ejecución se crea automáticamente en:

```text
docs/evidence/experiments/<experiment_id>/<execution_id>/
```

No cambie manualmente esa evidencia. Contiene recibo, configuración efectiva, linaje, métricas, validaciones e inventario con hashes.

## Preparar el entorno

```sh
uv sync --locked --project pipeline
uv run --directory pipeline python -m sat_dengue_pipeline.experiment_management validate
```

Para datos privados, configure el token sin escribirlo en el repositorio ni en el prompt de un agente:

```sh
read -s "HF_TOKEN?Token de Hugging Face: "
export HF_TOKEN
```

## Crear un experimento nuevo

### 1. Escribir la especificación

Cree `docs/experiments/EXP003/SPECIFICATION.md`. Debe declarar, antes de entrenar:

- identificador de la hipótesis;
- pregunta que se desea responder;
- cambio respecto al experimento de referencia;
- población, horizontes y periodos temporales;
- predictores, preparación, candidato, semilla e hiperparámetros;
- calibración, umbrales, métricas y líneas base;
- criterio para considerar el resultado positivo, negativo o inconcluso;
- limitaciones y comparación prevista.

La especificación explica por qué se ejecuta el experimento. La configuración define exactamente cómo se ejecuta.

### 2. Crear la configuración cerrada

Cree `pipeline/conf/experiments/EXP003.yml`. Use una configuración existente únicamente como referencia estructural y cambie de forma consciente los valores autorizados.

Para un experimento científico con datos reales, la sección de datos debe tener esta forma:

```yaml
data:
  mode: raw
  manifest: pipeline/conf/releases/<manifiesto-aprobado>.json
  manifest_sha256: <sha256-del-manifiesto>
  require_private: true
```

La configuración debe conservar los contratos implementados: predictores canónicos en su orden, familia `xgboost_onset` versión `v1`, preparación soportada, cinco roles temporales, métricas y líneas base oficiales. Cualquier opción no implementada será rechazada antes de adquirir datos o entrenar.

### 3. Calcular los hashes

Calcule el SHA-256 de los bytes de la especificación y de la configuración:

```sh
shasum -a 256 docs/experiments/EXP003/SPECIFICATION.md
shasum -a 256 pipeline/conf/experiments/EXP003.yml
```

En Linux también puede usarse `sha256sum`. Copie los dos valores en `registration.yml`. Si después cambia cualquiera de esos archivos, debe recalcular el hash antes de registrar; una receta ya ejecutada no se modifica.

### 4. Crear la solicitud de registro

`docs/experiments/EXP003/registration.yml` debe contener:

```yaml
experiment_id: EXP003
experiment_slug: exp003-descripcion-breve
hypothesis_id: EXP003-H1
title: Título claro del experimento
experiment_type: scientific
status: PROPOSED
protocol: docs/experiments/EXP003/SPECIFICATION.md
protocol_sha256: <sha256-de-la-especificacion>
configuration: pipeline/conf/experiments/EXP003.yml
configuration_sha256: <sha256-de-la-configuracion>
pipeline: experiment_run
conclusions: docs/experiments/EXP003/CONCLUSIONS.md
scientific_result: PENDING
champion_status: NOT_SELECTED
```

Registre y valide:

```sh
uv run --directory pipeline python -m sat_dengue_pipeline.experiment_management register --entry docs/experiments/EXP003/registration.yml
uv run --directory pipeline python -m sat_dengue_pipeline.experiment_management validate
```

El registro debe quedar en Git. No edite `registry.yml` a mano para saltarse la validación.

### 5. Revisar y aprobar

Otra persona debe revisar la hipótesis, los periodos, los datos, los predictores, la receta y los criterios. Después de aprobar los cambios mediante Pull Request, ejecute:

```sh
uv run --directory pipeline python -m sat_dengue_pipeline.experiment_management transition EXP003 APPROVED
```

Registre también esa transición en Git. El pipeline solo acepta experimentos con estado `APPROVED` y una receta cuyos hashes coincidan.

## Ejecutar el entrenamiento

```sh
uv run --directory pipeline kedro run --pipeline experiment_run --params experiment_id=EXP003
```

Durante la ejecución, la fábrica:

1. verifica identidad, aprobación y hashes;
2. obtiene el release fijado y comprueba su integridad;
3. reconstruye la tabla canónica desde los datos crudos;
4. aplica la frontera temporal y los soportes mínimos;
5. entrena, calibra y selecciona el umbral sin usar la evaluación para ajustar;
6. calcula métricas y líneas base;
7. registra agregados en MLflow local;
8. publica evidencia exclusiva y verificable.

Una ejecución correcta deja el experimento en `RUNNING`: significa que el cálculo terminó y espera interpretación humana. No vuelva a lanzar el mismo identificador.

Si la ejecución falla, conserve la evidencia y la causa registrada. No borre el directorio ni retire un bloqueo abandonado sin investigar. La repetición debe usar una identidad nueva.

## Revisar y cerrar el experimento

Consulte el registro y la evidencia:

```sh
uv run --directory pipeline python -m sat_dengue_pipeline.experiment_management list
uv run --directory pipeline python -m sat_dengue_pipeline.experiment_management compare --candidate xgboost_onset
```

Puede limitar la comparación:

```sh
uv run --directory pipeline python -m sat_dengue_pipeline.experiment_management compare --horizon 1 --status COMPLETED
```

La comparación muestra métricas y procedencia; no ordena candidatos ni selecciona un campeón. Antes de comparar resultados científicamente, confirme que población, periodos, protocolo y datos sean comparables.

Cree `docs/experiments/EXP003/CONCLUSIONS.md` y enlace el `inventory.json` de la ejecución. Debe contener estas ocho secciones con contenido real:

```text
## Hipótesis
## Resultado
## Métricas principales
## Comparación
## Limitaciones
## Decisión científica
## Qué se aprendió
## Próximo paso
```

El equipo debe clasificar el resultado como `POSITIVE`, `NEGATIVE` o `INCONCLUSIVE`. La fábrica valida la integridad, pero no decide el significado científico de las métricas.

Después cierre y valide:

```sh
uv run --directory pipeline python -m sat_dengue_pipeline.experiment_management transition EXP003 COMPLETED --result INCONCLUSIVE
uv run --directory pipeline python -m sat_dengue_pipeline.experiment_management validate
```

Versione la configuración, el protocolo, el registro, las conclusiones y la evidencia agregada mediante Pull Request. No versionar datos crudos, cachés, matrices ni secretos.

## Repetir un entrenamiento

Una repetición es un experimento nuevo. Por ejemplo, para repetir `EXP003`:

1. cree `EXP004`;
2. copie la especificación y configuración de `EXP003`;
3. declare en la nueva especificación que el propósito es medir reproducibilidad y que `EXP003` es la referencia;
4. conserve la receta sin cambios si busca una repetición exacta;
5. use una semilla diferente únicamente si la hipótesis estudia sensibilidad a la semilla;
6. calcule hashes nuevos, registre, revise y apruebe `EXP004`;
7. ejecute `EXP004` y compare sus métricas, identidad de datos, código y evidencia con `EXP003`;
8. documente coincidencias y diferencias en las conclusiones de `EXP004`.

No copie la evidencia de `EXP003`, no cambie su estado y no reutilice su identificador. La separación permite aprender de ambas ejecuciones sin perder información.

## Validación mínima antes de entregar cambios

```sh
uv lock --check --project pipeline
uv run --directory pipeline ruff check .
uv run --directory pipeline pytest
uv run --directory pipeline python -m sat_dengue_pipeline.experiment_management validate
git diff --check
```

## Ejemplo de uso correcto

El equipo quiere saber si aumentar la profundidad máxima de XGBoost mejora la detección de inicios en T+1 sin exceder la FAR predeclarada.

1. Registra `EXP010` como experimento de referencia con `max_depth: 2`, semilla 53, el release privado fijado y los periodos aprobados. Antes de entrenar declara el criterio de éxito y congela los archivos mediante SHA-256.
2. Una persona distinta revisa la receta, confirma que 2025 no participa en aprendizaje y aprueba `EXP010`. La fábrica lo ejecuta, conserva su evidencia y el equipo escribe conclusiones, aunque el resultado no sea favorable.
3. Registra `EXP011` con la misma población, datos, semilla, periodos y procedimiento; cambia únicamente `max_depth` a 3. La especificación declara que `EXP010` es la comparación prevista. Después de revisión y aprobación, ejecuta `EXP011`.
4. El equipo usa `compare` para revisar ambos resultados y verifica que las diferencias relevantes se limitan al cambio predeclarado. Documenta métricas, FAR, limitaciones y aprendizaje en `EXP011/CONCLUSIONS.md`.
5. Si desea comprobar que `EXP011` puede repetirse, crea `EXP012` con la misma receta de `EXP011`. No sobrescribe `EXP011`. Compara hashes de datos y código, métricas y evidencia, y registra cualquier diferencia.

Este procedimiento conserva las decisiones previas, hace auditables los cambios y evita elegir una receta después de mirar la evaluación.

## Uso de las skills de la fábrica

Una skill es una guía reutilizable que ayuda a un agente compatible con Agent
Skills a escoger el procedimiento y los límites correctos. Puede activarse
automáticamente por su descripción o invocarse explícitamente. La skill guía al
agente; no reemplaza la aprobación humana.

- `$sat-dengue-experiment` prepara, registra, ejecuta, repite, concluye o compara
  experimentos usando este manual y la fábrica existente.
- `$sat-dengue-scientific-review` revisa una receta antes de aprobarla o las
  conclusiones después de ejecutar, sin entrenar ni modificar la receta.
- `$sat-dengue-verification` selecciona y ejecuta los gates requeridos antes de
  declarar cambios terminados, preparar un commit o proponer un push.
- `$sat-dengue-recovery` diagnostica descargas, locks, evidencia o ejecuciones
  fallidas e identifica la recuperación mínima que debe autorizarse.

Invocaciones explícitas:

```text
Usa $sat-dengue-experiment para preparar EXP003.
Usa $sat-dengue-scientific-review para revisar EXP003 antes de aprobarlo.
Usa $sat-dengue-verification para validar los cambios.
Usa $sat-dengue-recovery para diagnosticar la ejecución bloqueada.
```

Para una revisión científica independiente conviene usar otro chat o revisor
distinto del que preparó o ejecutó el experimento. Ninguna skill autoriza por sí
sola un push, merge, acceso a secretos, aprobación científica, publicación o
selección de campeón. El [catálogo de skills](../agents/skills-catalog.md) resume
cuándo elegir cada una y enlaza su fuente canónica.
