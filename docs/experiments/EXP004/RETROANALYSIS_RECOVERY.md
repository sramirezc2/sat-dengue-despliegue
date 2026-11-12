# EXP004 — diagnóstico del primer intento de retroanálisis

Fecha: 12 de noviembre de 2026. Skill aplicada: `sat-dengue-recovery`.
Estado del componente: **BLOCKED**, recuperación pendiente de autorización humana.
No se cambia el estado del registro: la fábrica sí terminó y conserva RUNNING/PENDING
hasta la decisión científica humana.

## Hechos y evidencia preservada

El comando congelado terminó con código 1 en `raw_input`, antes de ejecutar
nodos con éxito, construir el canónico o entrenar. No creó `run1/`, el workspace
canónico de retroanálisis ni CSV. La configuración de logging solo usa consola;
este pipeline no emitió un recibo propio del fallo. El
[registro del intento](RETROANALYSIS_ATTEMPT_1.json) identifica explícitamente
su origen como registro operacional del error observado, sin fingir un recibo
generado por Kedro. No se borró ni corrigió evidencia.

La causa está confirmada por `canonical/nodes.py:build_input`: consulta
`data/01_raw/inbox/<release>/<manifest_digest>`. La fábrica usa
`data/01_raw/experiments/<release>/<manifest_digest>`. En inbox solo está el
release histórico, y falta el corregido. En experiments están los cinco archivos
del release corregido; se volvieron a verificar tamaños y SHA-256, solo lectura,
con el manifiesto aprobado. No hay indicio de cambio de datos o parámetros.
La preparación previa validó release, perfil y certificado, pero no detectó la
ausencia de esa caché en inbox antes de invocar el retroanálisis. Ese control
operacional debió realizarse antes del primer intento.

## Recuperación mínima propuesta, no ejecutada

1. Copiar exclusivamente los cinco archivos verificados del release corregido
   desde la caché de experiments al destino ausente de inbox, mediante temporales
   y verificación de tamaño/SHA-256 del resolver existente. Rechazar symlinks,
   entradas adicionales y un destino ya existente. Conservar el origen y un
   recibo agregado nuevo de la materialización. No descargar ni cambiar archivos
   históricos, receta, release, certificado o parámetros.
2. Solo si esa verificación pasa y existe autorización explícita adicional,
   invocar una vez más el mismo comando:

   ```sh
   uv run --locked --directory pipeline kedro run --pipeline retroanalisis --env exp004
   ```

La propuesta conserva el primer fallo y usa el destino `run1/` aún inexistente.
No repite la fábrica ni ningún aprendizaje anterior del retroanálisis: el primer
intento falló antes del ajuste. Por esa causa ambiental previa al aprendizaje,
no se propone una nueva identidad científica; una repetición de entrenamiento
ya realizado sí exigiría otra identidad y aprobación. La invocación adicional
no está cubierta por la autorización original de un solo intento.

## Comprobación y límites

Antes del segundo comando: verificar de nuevo los hashes R2, cinco archivos,
inventario cerrado y ausencia de salida. Después: conservar seis CSV, verificar
`conjunto.csv` por horizonte/semilla/fold y ausencia de 2025, registrar sus hashes
y revisar resultados. Ante otro fallo se detiene y conserva lo producido.

La copia añade aproximadamente 2,6 GB de caché local ignorada; no escribe en Git
datos o modelos ni modifica el origen. No hay borrado o rollback automático.
El estado `BLOCKED` de este diagnóstico no atribuye fallo a la fábrica terminada
ni permite cerrar el experimento con una conclusión inventada.
