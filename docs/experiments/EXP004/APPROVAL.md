# EXP004 R2 — aprobación humana de receta y ejecución

Fecha: 12 de noviembre de 2026. Autoridad: persona usuaria, en esta conversación.

La persona aprobó explícitamente la receta R2 con estas identidades SHA-256:

| Archivo | SHA-256 |
|---|---|
| `SPECIFICATION.md` | `ee40e74fa0dbf7bdd150340c9103961ef9fe0300c87743faab1c3337aa6ab2fd` |
| `pipeline/conf/experiments/EXP004.yml` | `ed55aedb9259ae253863fd97cf255d48b56cba2a15854e4746e666df32e7132f` |

Autorización recibida:

> Autorizo cambiar EXP004 de `PROPOSED` a `APPROVED` y ejecutar una sola vez la fábrica E2E y el retroanálisis predeclarado usando `HF_TOKEN` exclusivamente desde el entorno.

Restricciones expresas de la persona:

> No autorizo modificar la receta después de observar resultados, seleccionar semillas, usar 2025, declarar campeón, hacer push, abrir PR ni merge.

La aprobación corresponde a la receta revisada, incluida `secondary_t2`, sus
archivos vinculados, cinco semillas y comandos predeclarados. No autoriza
reintentos automáticos, cambios de parámetros, conclusiones científicas,
campeón, publicación o uso operativo. Un fallo conserva su evidencia y requiere
el diagnóstico de recuperación antes de proponer otra acción.

Antes de registrar la aprobación se verificaron los dos hashes, registro
PROPOSED/PENDING, árbol Git limpio y ausencia de directorios de ejecución real
de EXP004. Solo se comprobó la presencia de `HF_TOKEN` en el entorno; su valor
no se imprimió ni persistió. La revisión previa y el recibo de preparación R2
permanecen históricos e intactos. El cambio de estado se realiza mediante el
CLI oficial; este documento no modifica el protocolo ni la configuración.

La decisión científica POSITIVE/NEGATIVE/INCONCLUSIVE sigue pendiente del equipo
tras la evidencia y revisión posterior. `champion_status` permanece
`NOT_SELECTED`, sin autorización operativa.
