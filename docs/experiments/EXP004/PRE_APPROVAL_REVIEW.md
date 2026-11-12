# EXP004 — revisión científica previa a aprobación

Modo: `pre-approval`, revisión R2 solicitada por la persona, 12 de noviembre de 2026.
La propuesta anterior omitió la lectura secundaria T+2 y esta revisión no lo
señaló. Se corrige antes de aprobar o ejecutar, sin haber observado resultados.
Recomendación: **APPROVED_WITH_LIMITATIONS**, sujeta al gate técnico documentado
en PREPARATION_VALIDATION_R2.json y a la aprobación humana explícita de la receta.
No es una transición del registro ni autorización de entrenamiento.

## Evidencia revisada

AGENTS.md, plan.md, arquitectura E2E, las cuatro skills de la fábrica, manual,
contrato aprobado 1.0.0, bitácora completa y tanda 10, decisiones temporales y
evaluación emparejada, revisión científica anterior y guía operacional.

[Especificación cerrada](SPECIFICATION.md), [registro inicial](registration.yml),
[receta de fábrica](../../../pipeline/conf/experiments/EXP004.yml),
[preinscripción por tanda](../../bitacora/tanda-exp004-recencia.md), dos recetas
de retroanálisis y entorno `conf/exp004`, con identidades SHA-256 enumeradas en
la especificación. El registro oficial valida EXP004 como PROPOSED.

Las regresiones de [pesos y receta](../../../pipeline/tests/test_training_weighting.py)
ejercitan las tres lecturas con el lifecycle artificial y verifican B en el
recibo. Se revisan además las [reglas de B](../../../pipeline/tests/test_scientific_evaluation.py)
con persistencia informativa o sin alertas y la [agregación separada](../../../pipeline/tests/test_seed_aggregation.py).
La implementación existente ya admite `secondary_t2`; esta R2 no cambia código
productivo, criterios, hiperparámetros, datos ni periodos.

Protocolo SHA-256:
`ee40e74fa0dbf7bdd150340c9103961ef9fe0300c87743faab1c3337aa6ab2fd`.
Configuración SHA-256:
`ed55aedb9259ae253863fd97cf255d48b56cba2a15854e4746e666df32e7132f`.

## Hallazgos y alcance

| Severidad / estado | Evidencia y acción |
|---|---|
| PASS: único cambio aislado | Misma logística climática C=1/max_iter=5000, predictores/preparación y calendario. Recencia fija 36m con media uno, exclusivamente en fit. Los tests contrastan X, claves y etiquetas y equivalencia uniforme con el comportamiento previo. |
| PASS: temporalidad | Referencia de edad tomada solo de train maduro. Se reutilizan TemporalPolicy, fold_inputs y preflight_roles; evaluación diferida y bloqueo explícito de todos los periodos de 2025. No se usa T+1 para emitir T+2. |
| PASS: diseño cerrado | Siete cortes 2018–2024, cinco semillas 7/13/31/53/101 y población común idéntica entre brazos dentro de cada lectura. `primary` T+1/T+2 y `secondary_t2` solo T+2: 140 variantes y 210 ajustes. Datos/release/certificado fijados; sin HPO, otra vida media, refit o selección de semilla. |
| PASS: dos preguntas separadas | Hipótesis recent−uniform con intervalo emparejado y criterio fijado antes de evaluar. Cada brazo frente al canal mantiene 10 pp puntuales y en cota inferior, carga, A/C primaria y A/B/C secundaria, soporte, controles y consistencia contractual. Ambas lecturas T+2 se reportan separadas y ninguna rescata T+1. |
| PASS: B secundaria explícita | `secondary_t2` incluye ambos estados conocidos en T; mantiene el evento T+1 → T+2 y no usa T+1 como compuerta. B y utilidad frente a persistencia C1 son obligatorias; ausencia de alertas produce NO_EVALUABLE/NO_PERSISTENCE_ALERTS, no éxito. Cohortes, votos y resúmenes separados de primaria, con soporte común por par de brazos. |
| PASS: contrato y gobernanza separados | Contrato APPROVED; registro PROPOSED, scientific_result PENDING, scientific_conclusion NOT_APPROVED y champion_status NOT_SELECTED. Pruebas de recibos y hashes históricos. |
| MEDIUM: evidencia exploratoria | La hipótesis y 2018–2024 se exploraron previamente. La preinscripción lo declara. No presentar como descubrimiento nuevo o confirmación independiente; no cerrar afirmativamente el proyecto con EXP004. |
| MEDIUM: disponibilidad retrospectiva | Demora de un mes y embargo no prueban disponibilidad operativa real o ausencia de backfill. Mantener esa limitación en conclusiones. |
| MEDIUM: soporte aún no observado | Los mínimos productivos y 30 inicios/celda son reglas previas. Hasta la corrida real no se conoce el soporte efectivo. Un fallo no autoriza relajar la receta, descartar el intento o repetir a ciegas. |
| LOW: instrumentos distintos | El retroanálisis usa ranking mensual y presupuesto realizado del canal, con bootstrap municipal descriptivo; la fábrica usa cinco roles y presupuesto proxy fijo, con 2.000 bloques mensuales. Comparar brazos dentro de cada instrumento; no mezclar sus cifras ni atribuir un veredicto contractual a los CSV. |
| LOW: reproducibilidad de modelos | N=3 del canónico no equivale a N=3 E2E del finalista. EXP004 es un intento registrado con cinco semillas, sin aprobación de campeón. |
| LOW: independencia | Esta revisión fue realizada por el mismo agente que preparó la implementación. Se recomienda otra persona o chat para la revisión científica independiente, especialmente la posterior y la decisión final. |

La lectura secundaria faltante de la propuesta anterior queda incorporada y
predeclarada en esta R2. No se identificó fuga temporal ni un cambio científico
adicional entre brazos
en el alcance inspeccionado. Las pruebas usan fuentes exclusivamente artificiales;
no prueban efecto científico, soporte real, confirmación o capacidad sanitaria.

## Decisión humana requerida

Aprobar explícitamente el protocolo y configuración identificados arriba y los
archivos vinculados por sus hashes antes de pasar EXP004 de PROPOSED a APPROVED.
La instrucción del usuario reserva esta aprobación a la persona y no autoriza
PR, push o merge; el mecanismo de esta operación es aprobación explícita en la
conversación y registro posterior de esa autorización en Git, sin modificar la
receta congelada. El equipo decidirá POSITIVE/NEGATIVE/INCONCLUSIVE tras la
corrida y la revisión posterior, antes de cerrar el registro.
