# Catálogo de skills de la fábrica

Las skills canónicas viven en `.agents/skills/` y pueden seleccionarse por su
descripción o invocarse explícitamente. Guían al agente, pero no conceden acceso a
secretos ni autorización para aprobar ciencia, publicar, hacer push o merge.

## Selección rápida

- Crear, repetir, ejecutar, concluir o comparar → `$sat-dengue-experiment`.
- Revisar validez científica → `$sat-dengue-scientific-review`.
- Verificar antes de entregar → `$sat-dengue-verification`.
- Diagnosticar un fallo → `$sat-dengue-recovery`.

## Catálogo

| Nombre | Propósito | Activadores | Entradas principales | Salida | Aprobación humana requerida | Skill relacionada | Ubicación |
|---|---|---|---|---|---|---|---|
| `sat-dengue-experiment` | Operar el ciclo de vida registrado sin reescribir historia. | Preparar, registrar, ejecutar, repetir, concluir, listar o comparar. | Modo, ID, hipótesis, receta, hashes, estado y evidencia según etapa. | Acción/estado, archivos, validaciones, evidencia y siguiente paso seguro. | Aprobar receta, decidir resultado, ejecutar cuando falte permiso, publicar, push o merge. | Revisión científica, verificación y recuperación. | [`SKILL.md`](../../.agents/skills/sat-dengue-experiment/SKILL.md) |
| `sat-dengue-scientific-review` | Auditar validez antes de aprobar o después de ejecutar. | Revisión pre-approval/post-run; fuga, comparabilidad o métricas. | Hipótesis, referencia, receta, periodos; en post-run, inventario, métricas y conclusiones. | `APPROVED`, `APPROVED_WITH_LIMITATIONS` o `BLOCKED`, con hallazgos. | Aprobación científica, aceptación de conclusiones y cualquier cambio de receta. | Experimentos y verificación. | [`SKILL.md`](../../.agents/skills/sat-dengue-scientific-review/SKILL.md) |
| `sat-dengue-verification` | Seleccionar y ejecutar gates proporcionales/acumulados. | Antes de terminar, cerrar, preparar commit o proponer push; validación solicitada. | Claim, diff/revisión, archivos cambiados y baseline protegido. | `PASS`, `FAIL` o `BLOCKED`, comandos, resultados, omisiones y siguiente acción. | Push, merge, publicación y correcciones fuera del alcance. | Las otras tres skills. | [`SKILL.md`](../../.agents/skills/sat-dengue-verification/SKILL.md) |
| `sat-dengue-recovery` | Diagnosticar fallos conservando evidencia. | Descarga/hash/acceso/lock/evidencia/MLflow/memoria/Colab/plataforma o terminal fallido. | ID, estado, etapa, recibos/inventarios, logs agregados y contexto del sistema. | Diagnóstico, riesgo, acción mínima, aprobación y criterio de recuperación. | Eliminar, desbloquear, repetir, cambiar estado o descargar datos privados. | Experimentos para repetir; verificación para comprobar. | [`SKILL.md`](../../.agents/skills/sat-dengue-recovery/SKILL.md) |

Para procedimientos y comandos de la fábrica, usar el [manual de experimentos](../experiments/manual_pipeline.md); este catálogo solo ayuda a escoger la capacidad correcta.
