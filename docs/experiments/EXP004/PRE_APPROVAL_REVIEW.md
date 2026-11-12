# EXP004 — revisión científica previa a aprobación

Modo: `pre-approval`, 11 de noviembre de 2026.
Recomendación: **APPROVED_WITH_LIMITATIONS**, sujeta al gate técnico documentado
en PREPARATION_VALIDATION.json y a la aprobación humana explícita de la receta.
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

Protocolo SHA-256:
`785bd9e16e36cc219719c13d514e4d41e2c9a1e3c3955a0cc96e99843e16599d`.
Configuración SHA-256:
`87860f2f66965fa20cba8647cfa7b120aecaac26df3773b077f0e9f4547c008f`.

## Hallazgos y alcance

| Severidad / estado | Evidencia y acción |
|---|---|
| PASS: único cambio aislado | Misma logística climática C=1/max_iter=5000, predictores/preparación y calendario. Recencia fija 36m con media uno, exclusivamente en fit. Los tests contrastan X, claves y etiquetas y equivalencia uniforme con el comportamiento previo. |
| PASS: temporalidad | Referencia de edad tomada solo de train maduro. Se reutilizan TemporalPolicy, fold_inputs y preflight_roles; evaluación diferida y bloqueo explícito de todos los periodos de 2025. No se usa T+1 para emitir T+2. |
| PASS: diseño cerrado | Siete cortes 2018–2024, cinco semillas 7/13/31/53/101 y población común idéntica. Datos/release/certificado fijados; sin HPO, otra vida media, refit o selección de semilla. |
| PASS: dos preguntas separadas | Hipótesis recent−uniform con intervalo emparejado y criterio fijado antes de evaluar. Cada brazo frente al canal mantiene 10 pp puntuales y en cota inferior, carga, A/C, soporte, controles y consistencia contractual. T+2 no rescata T+1. |
| PASS: contrato y gobernanza separados | Contrato APPROVED; registro PROPOSED, scientific_result PENDING, scientific_conclusion NOT_APPROVED y champion_status NOT_SELECTED. Pruebas de recibos y hashes históricos. |
| MEDIUM: evidencia exploratoria | La hipótesis y 2018–2024 se exploraron previamente. La preinscripción lo declara. No presentar como descubrimiento nuevo o confirmación independiente; no cerrar afirmativamente el proyecto con EXP004. |
| MEDIUM: disponibilidad retrospectiva | Demora de un mes y embargo no prueban disponibilidad operativa real o ausencia de backfill. Mantener esa limitación en conclusiones. |
| MEDIUM: soporte aún no observado | Los mínimos productivos y 30 inicios/celda son reglas previas. Hasta la corrida real no se conoce el soporte efectivo. Un fallo no autoriza relajar la receta, descartar el intento o repetir a ciegas. |
| LOW: instrumentos distintos | El retroanálisis usa ranking mensual y presupuesto realizado del canal, con bootstrap municipal descriptivo; la fábrica usa cinco roles y presupuesto proxy fijo, con 2.000 bloques mensuales. Comparar brazos dentro de cada instrumento; no mezclar sus cifras ni atribuir un veredicto contractual a los CSV. |
| LOW: reproducibilidad de modelos | N=3 del canónico no equivale a N=3 E2E del finalista. EXP004 es un intento registrado con cinco semillas, sin aprobación de campeón. |
| LOW: independencia | Esta revisión fue realizada por el mismo agente que preparó la implementación. Se recomienda otra persona o chat para la revisión científica independiente, especialmente la posterior y la decisión final. |

No se identificó fuga temporal ni un cambio científico adicional entre brazos
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
