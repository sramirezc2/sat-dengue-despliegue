# Experimentos registrados de V3

T17 añade gobernanza a los contratos científicos existentes. El registro
`registry.yml` y los archivos versionados permiten recuperar la historia sin el
store MLflow. T16 sigue siendo validación de ingeniería cerrada y vive fuera del
registro científico; no se reinterpreta ni se vuelve a ejecutar.

## Registrar y aprobar

1. Crear `docs/experiments/EXP003/SPECIFICATION.md` con hipótesis, receta,
   límites, criterio y comparación predeclarados. Crear
   `pipeline/conf/experiments/EXP003.yml` usando una configuración del directorio
   como ejemplo de estructura, sin atribuir sus valores sintéticos a la ciencia.
2. Crear `docs/experiments/EXP003/registration.yml` con los mismos campos cerrados
   que una entrada de `registry.yml`, ID/slug/hipótesis únicos, `status: PROPOSED`,
   `scientific_result: PENDING`, `champion_status: NOT_SELECTED`, rutas relativas
   y SHA-256 **de los bytes** del protocolo y configuración. Para una receta real,
   `experiment_type: scientific` y `data.mode: raw`, manifiesto cerrado y su SHA-256,
   `require_private: true`. No hay ejecución real autorizada por los fixtures.
3. Desde la raíz registrar y validar:

   ```sh
   uv run --directory pipeline python -m sat_dengue_pipeline.experiment_management register --entry docs/experiments/EXP003/registration.yml
   uv run --directory pipeline python -m sat_dengue_pipeline.experiment_management validate
   ```

4. La revisión humana de protocolo/configuración precede a la aprobación explícita:

   ```sh
   uv run --directory pipeline python -m sat_dengue_pipeline.experiment_management transition EXP003 APPROVED
   ```

   Registrar esta aprobación en Git. Para ciencia real la especificación debe
   pasar por el único PR antes de ejecutar, según D9 del diseño; esta tarea no
   concede esa autorización. Ni MLflow ni el ejecutor aprueban ciencia.

Solo se permiten `PROPOSED → APPROVED → RUNNING → COMPLETED|BLOCKED`. Una aprobación
habilita un intento en ese checkout. El ejecutor marca `RUNNING` al reservar una
carpeta exclusiva; no restaura automáticamente `APPROVED` al terminar. Reintentos
o recetas revisadas necesitan una nueva identidad y aprobación, conservando los
recibos previos. Distintos checkouts de una aprobación generan execution_id
nuevos y la misma firma si coinciden todas las entradas de identidad.

## Ejecutar

Sintaxis verificada con Kedro 1.7.0 instalado:

```sh
uv sync --locked --project pipeline
uv run --directory pipeline kedro run --pipeline experiment_run --params experiment_id=EXP003
```

EXP001 y EXP002 son únicamente los fixtures autorizados de aceptación técnica.
Sus ejecuciones versionadas ya cerradas no se vuelven a lanzar sobre el registro
actual. La suite genera copias temporales de ambas aprobaciones y las ejecuta
completas sin fuentes privadas ni red:

```sh
uv run --directory pipeline pytest tests/test_experiment_management.py
```

El ejecutor valida hashes y aprobación antes de adquirir fuentes, reconstruye
siempre y verifica bytes/digest/esquema/tipos del canónico antes de usarlo. No
acepta una tabla externa ni implementa caché canónica nueva. Reutiliza
`factory.engine` para guards, cinco roles, soportes previos a todo ajuste,
calibración, umbral, predicciones previas a etiquetas de evaluación, métricas y
referencias emparejadas. 2025 se mantiene globalmente excluido mediante las mismas
autoridades `TemporalPolicy` y `guard_development`.

La única familia es `xgboost_onset/v1`, CPU/hist/un hilo, sin imports en YAML,
HPO, refit o campeón. Los 33 predictores de entrada se certifican completos por
los contratos existentes; la matriz interna usa el subconjunto canónico declarado.
Esto conserva el filtro conservador de filas completas para los 33 predictores,
aunque una receta modele menos variables. La preparación admite solo codificación
fija, sin imputación/escalado/G/presupuesto; modos no implementados fallan cerrados.
Los parámetros y configuración nativa esperada de XGBoost son explícitos.

## Evidencia y estados

Cada intento reservado produce:

```text
docs/evidence/experiments/<experiment_id>/<execution_id>/
  receipt.json          terminal, UTC, semilla, candidato, MLflow, firma
  configuration.json    receta y propósito efectivos
  lineage.json          entradas de la firma, release y huellas canónicas
  metrics.json          métricas, calibrador y umbral congelados por horizonte
  validation.json       soportes, auditorías temporales y hashes de artefactos/modelos
  inventory.json        SHA-256 de los cinco archivos; marcador final de cierre
```

La firma no incluye reloj ni execution_id: incluye ID de experimento, protocolo,
configuración, manifiesto, código/Git/dirty, lock y versiones científicas. Antes de
adquirir un release fallido, su digest puede ser null en fixtures; no se inventa
una identidad de datos adquiridos. No se guardan filas, X/y, predicciones, modelos,
rutas privadas ni mensajes libres de proveedores en evidencia. Solo se conservan
huellas de modelos, por lo que no se necesita un backend de persistencia de modelos.

Los estados terminales de ejecución son `COMPLETED`, `BLOCKED`, `FAILED`, `KILLED`.
Una excepción se propaga con código no cero y causa pública por etapa/tipo; se
conservan agregados parciales con su estado de fallo. El **experimento** queda
`RUNNING` tras éxito de cómputo hasta revisión y conclusiones humanas; el estado
experimental `COMPLETED` requiere conclusiones válidas y resultado explícito.
Un intento fallido deja el experimento `BLOCKED`.

La carpeta se reserva con mkdir exclusivo y cada archivo se abre con `xb`; no se
sobrescribe una ejecución. Un inventario ausente o alterado impide compararla como
éxito. Si falla la escritura de evidencia, MLflow y registro quedan fallidos y se
intenta conservar un recibo local `pipeline/data/experiments/<execution_id>/evidence-failure.json`.
No se reparan automáticamente paquetes incompletos ni se ocultan. Un fallo total
del filesystem puede impedir cualquier recibo; se propaga el error. Un lock
abandonado requiere investigar la interrupción antes de retirarlo manualmente.
`pipeline/data/` y `pipeline/.tracking/` ya están ignorados por Git.

MLflow usa el backend SQLite y SDK local existentes en
`pipeline/.tracking/experiments/`, un padre por ejecución y dos hijos solo cuando
hay comparación entre horizontes. Una receta de un horizonte usa el padre solo.
Tags cerrados enlazan evidencia Git, hipótesis, protocolo/configuración, datos,
código y terminal; se registran exclusivamente métricas agregadas. No se requiere
servidor, backend remoto ni API fluida. La ausencia del grupo opcional tracking
falla explícitamente; no se simula un registro exitoso.

## Concluir y comparar

`CONCLUSIONS.md` debe identificar experimento y resultado (`POSITIVE`, `NEGATIVE`,
`INCONCLUSIVE`; `NOT_APPLICABLE` para fixtures), enlazar un inventario completo y
tener contenido en ocho secciones: Hipótesis, Resultado, Métricas principales,
Comparación, Limitaciones, Decisión científica, Qué se aprendió y Próximo paso.
La validación comprueba estructura, identidad e integridad; el juicio científico
corresponde a la revisión humana. No se deduce positividad de una métrica.

```sh
uv run --directory pipeline python -m sat_dengue_pipeline.experiment_management transition EXP003 COMPLETED --result INCONCLUSIVE
uv run --directory pipeline python -m sat_dengue_pipeline.experiment_management list
uv run --directory pipeline python -m sat_dengue_pipeline.experiment_management compare --horizon 2 --candidate xgboost_onset
```

La salida JSON determinista incluye métricas del candidato y referencias,
terminales, resultado científico, hashes de protocolo/configuración/dataset/código
y enlaces a evidencia. `--status` filtra estado experimental o terminal. No ordena
por rendimiento ni elige campeón; recetas, cohortes o protocolos distintos no
constituyen por sí mismos una comparación científica emparejada. Las conclusiones
científicas futuras enlazarán su evidencia en la bitácora; los fixtures no aportan
resultados científicos a ella.

## Procedencia y diferencias frente a V2

Se revisaron, sin escribir en V2, el registro y las conclusiones de EXP02 del
commit `916a69f3bb73f2ffbb0ec038b8bef887ee91adf1`. Se recuperan registro central,
protocolo congelado, identidad, aprendizaje obligatorio y tracking padre/hijos.
No se copian runners por experimento, replay, matrices históricas, complejidad de
aprobaciones de ocho identidades ni 63 hijos sin comparación requerida. Los
contratos científicos V3 y su exclusión de 2025 siguen siendo la autoridad.

La preservación de T16 y los 22 JSON se verifica sin ejecutar ciencia:

```sh
uv run --directory pipeline python tools/check_experiment_preservation.py
```
