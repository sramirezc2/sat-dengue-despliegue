# Manual de la fábrica de experimentos

Esta guía sirve para personas y agentes. Todos los comandos se ejecutan desde la raíz del repositorio. La fábrica sigue una receta aprobada, ejecuta adquisición → construcción canónica → entrenamiento → evaluación y guarda un recibo exclusivo de cada corrida. El [contrato científico](contrato.md) define qué resultados pueden interpretarse; sigue pendiente de aprobación del equipo.

## Elija la ayuda adecuada

| Necesidad | Skill |
|---|---|
| Crear, registrar, ejecutar, repetir, concluir o comparar | `$sat-dengue-experiment` |
| Revisar la receta antes de aprobarla o los resultados después | `$sat-dengue-scientific-review` |
| Comprobar los cambios antes de entregarlos | `$sat-dengue-verification` |
| Diagnosticar una corrida fallida o bloqueada | `$sat-dengue-recovery` |

Pida al agente la acción y el identificador, por ejemplo: «Usa `$sat-dengue-experiment` para preparar EXP003». Las skills guían el trabajo; **no aprueban recetas ni conclusiones por el equipo**. Sus instrucciones están en el [catálogo](../agents/skills-catalog.md).

## 1. Prepare un experimento nuevo

Use un ID libre, por ejemplo `EXP003`. No reutilice `EXP001` ni `EXP002`: son pruebas técnicas con datos artificiales. Cree:

- `docs/experiments/EXP003/SPECIFICATION.md`: pregunta, hipótesis, experimento de referencia, cambio propuesto y criterio de evaluación, escritos **antes** de entrenar.
- `pipeline/conf/experiments/EXP003.yml`: receta ejecutable con datos y certificado fijados, predictores, modelo, periodos, horizontes, brazos, cortes y semillas. Use otra receta solo como ejemplo de estructura. La [guía de evaluación](scientific-evaluation.md) explica sus campos; no copie valores sintéticos como decisiones científicas.
- `docs/experiments/EXP003/registration.yml`: ID único, estado `PROPOSED`, rutas y hashes SHA-256 de los dos archivos anteriores. Su forma está en [Registrar y aprobar](README.md#registrar-y-aprobar).

Para calcular los hashes de forma portable, use `uv run --project pipeline python -c "import hashlib,sys; print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())" RUTA_DEL_ARCHIVO` una vez por archivo. Si cambia un archivo, recalcule su hash. No cambie una receta después de observar resultados.

Registre y compruebe:

```sh
uv sync --locked --project pipeline
uv run --directory pipeline python -m sat_dengue_pipeline.experiment_management register --entry docs/experiments/EXP003/registration.yml
uv run --directory pipeline python -m sat_dengue_pipeline.experiment_management validate
```

Use `$sat-dengue-scientific-review` para revisar hipótesis, periodos, disponibilidad de datos, comparadores y criterio de éxito. Otra persona del equipo debe aprobar la receta mediante PR y autorizar el cambio de estado. Entonces ejecute:

```sh
uv run --directory pipeline python -m sat_dengue_pipeline.experiment_management transition EXP003 APPROVED
```

Registre esa aprobación en Git. El programa rechaza un experimento no aprobado o cuyos hashes ya no coinciden.

## 2. Ejecute el recorrido completo

Cada integrante configura su acceso a los datos privados siguiendo la [guía de autenticación por sistema](../operations/pipeline-operations.md#autenticación-segura). Nunca comparta el token con un agente ni lo guarde en Git. Con el acceso listo, el recorrido E2E usa **un comando**:

```sh
uv run --directory pipeline kedro run --pipeline experiment_run --params experiment_id=EXP003
```

La fábrica verifica los datos, construye el canónico certificado, prepara los cinco periodos de trabajo, entrena y evalúa sin pasos manuales intermedios. Excluye 2025 del aprendizaje. Cada ejecución crea su propia evidencia en `docs/evidence/experiments/EXP003/<execution_id>/` y registra métricas en MLflow local. No edite esos archivos.

## 3. Revise la evaluación y cierre

Lea `receipt.json`, `inventory.json` y los resultados enlazados desde el recibo. El [contrato](contrato.md) explica A/B/C, el canal, persistencia, soportes y veredictos; la [guía de evaluación](scientific-evaluation.md) explica los brazos con y sin clima, cortes y cinco semillas. La fábrica muestra T+1 y T+2 por separado, las diferencias por año y territorio, y conserva todas las semillas: **no elija la mejor**. Los veredictos actuales son bajo contrato propuesto, no aprobación académica ni elección de campeón. Los resultados de 2025, ya conocidos en V2, no son confirmación independiente.

Pida una revisión posterior con `$sat-dengue-scientific-review`. Escriba `docs/experiments/EXP003/CONCLUSIONS.md` con la hipótesis, resultados, comparación, límites, aprendizaje y enlace al inventario. El equipo decide `POSITIVE`, `NEGATIVE` o `INCONCLUSIVE`; después cierre y valide:

```sh
uv run --directory pipeline python -m sat_dengue_pipeline.experiment_management transition EXP003 COMPLETED --result INCONCLUSIVE
uv run --directory pipeline python -m sat_dengue_pipeline.experiment_management validate
```

Sustituya `INCONCLUSIVE` solo por la decisión aprobada. Para consultar y comparar resultados registrados:

```sh
uv run --directory pipeline python -m sat_dengue_pipeline.experiment_management list
uv run --directory pipeline python -m sat_dengue_pipeline.experiment_management compare --candidate xgboost_onset
```

Compare científicamente solo experimentos con población, periodos, evento y datos compatibles. La comparación automática no selecciona un campeón.

## Repetir o recuperar

Para repetir `EXP003`, prepare **EXP004** con un ID y aprobación nuevos. Declare si busca repetir exactamente la receta o estudiar un cambio concreto; conserve `EXP003` y toda su evidencia. Si la corrida falla o queda bloqueada, use `$sat-dengue-recovery` antes de reintentar. No borre recibos, desbloquee a ciegas ni vuelva a usar un ID ejecutado.

**Ejemplo.** El equipo quiere comprobar si añadir clima ayuda. Prepara `EXP003` con dos brazos predeclarados, uno epidemiológico y otro con clima, sobre las mismas observaciones comparables. Un revisor comprueba la receta y el equipo la aprueba. Se ejecuta el comando E2E; la fábrica guarda ambos brazos, los cinco resultados por semilla y la evaluación por horizonte. Otra persona revisa la evidencia y documenta si el clima aportó algo, si el resultado fue inconcluso y qué límites tiene. Una repetición se registra como `EXP004`, sin alterar `EXP003`.
