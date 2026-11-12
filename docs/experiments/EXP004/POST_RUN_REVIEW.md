# EXP004 — revisión científica posterior de la fábrica y alcance pendiente

Fecha: 12 de noviembre de 2026. Skill: `sat-dengue-scientific-review`, modo
`post-run`. **BLOCKED para el cierre del alcance completo**: faltan el diagnóstico
de retroanálisis ejecutado y la decisión científica humana. La fábrica tiene
inventario íntegro y es revisable descriptivamente. El retroanálisis queda
**NOT_VERIFIED**; no se emite una recomendación de aprobación del paquete completo.
Esta revisión no cambia estados del registro, no autoriza recuperación y no
selecciona un resultado científico o campeón.

## Evidencia contrastada

Contrato 1.0.0 APROBADO, manual, reglas temporales y de evaluación emparejada,
revisión científica histórica, protocolo/configuración R2 con hashes aprobados,
preinscripción y [aprobación humana](APPROVAL.md).
[Inventario](../../evidence/experiments/EXP004/04a0554e6fa7470394b185b5dab36d7a/inventory.json),
recibo, linaje, configuración efectiva y 99 fragmentos científicos del mismo
paquete. [Auditoría de ejecución](EXECUTION_AUDIT.json),
[síntesis agregada](RESULTS_SUMMARY.json), [conclusiones pendientes](CONCLUSIONS.md),
[resultado en bitácora](../../bitacora/tanda-exp004-resultados.md) y
[fallo de retroanálisis](RETROANALYSIS_ATTEMPT_1.json).

El inventario verifica 105 archivos y firma de ejecución
`24165ef5dfc03fbef19b72eaef543d3282891427354c047e784d09e34d74d98d`;
protocolo y configuración siguen exactamente bajo los hashes aprobados.
Código productivo idéntico al revisado antes de ejecutar. El único ajuste técnico
posterior afecta una prueba histórica que asumía solo EXP001/EXP002; no afecta
modelos, datos, receta, evaluación o los recibos ya producidos.

## Hallazgos

| Severidad / estado | Evidencia e implicación |
|---|---|
| PASS — cambio único y cohortes | 140 variantes y 210 modelos; 105 pares por horizonte. Se verificaron 525 digests de claves, predictores y matrices de roles entre brazos; preflight verificó etiquetas productoras antes de fit, y evaluación emparejada comprobó LINK/onset tras predecir. No se igualan cohortes primaria y secundaria entre sí. |
| PASS — pesos y aislamiento | 210 resúmenes con media uno, peso crudo más reciente uno y pesos positivos; referencia solo de train, fit_only. El código congelado aplica sample_weight solo a LogisticRegression.fit. No hay filas de pesos persistidas, HPO, otra vida media o transferencia de estado. |
| PASS — temporalidad | Canónico reconstruido operational_full idéntico al certificado; cuarentena de 2025 antes de productores. Los 140 planes, ventanas, orígenes y disponibilidades de roles terminan antes de 2025. Todas las variantes informan evaluation_reads_after_both_predictions=true. |
| PASS — identidad y semillas | Fábrica única, COMPLETED, desde a075b0d con dirty=false. Exactamente semillas 7/13/31/53/101; todas conservadas. Las tres diferencias agregadas e intervalos son idénticos en las cinco, sin sumar I o elegir una. Seed base 53 del recibo no sustituye el bloque científico multisemilla. |
| PASS — hipótesis de pesos | T+1: +0,1686 pp, IC95 % [−0,8293; 1,1746], con 3/7 cortes positivos, dos deterioros y dos empates en cada semilla. No satisface cota inferior >0 ni mayoría 4/7 predeclarada. Ambas lecturas T+2 tienen intervalos que incluyen cero y no rescatan T+1. No se convierte esa constatación en NEGATIVE o INCONCLUSIVE automáticamente. |
| PASS — regla de 10 pp y seguridad | En cada semilla y brazo: 0/7 cortes T+1 pasan ganancia y cota; T+2 primaria tiene 1/7, pero falla carga; secundaria 2/7, pero falla persistencia y A/C en esos cortes. Todas las lecturas tienen 0/7 votos completos. Sin control negativo CUMPLE ni violación de cupo en las celdas conjuntas. No se aplicó el criterio histórico de 5 pp. |
| PASS — B secundaria | Persistencia es EVALUABLE y B obligatoria en todos los cortes secundarios conjuntos; ambos brazos solo la superan en 2021. Ese corte tiene precisión insuficiente frente al canal. Primaria conserva NO_EVALUABLE/DEGENERATE_PRIMARY_COHORT sin inventar una victoria. |
| MEDIUM — soporte territorial | Los siete cortes conjuntos son suficientes. Las celdas departamentales pequeñas permanecen excluidas del voto; Meta T+2 primaria queda NO_EVALUABLE en ambos brazos. El agregado conjunto no valida las celdas pequeñas. Fragmentos científicos preservan sus N/I y todos los desgloses. |
| MEDIUM — exploratorio y disponibilidad | Hipótesis y periodos ya explorados; demora y embargo son supuestos, no evidencia de disponibilidad histórica o ausencia de backfill. No cabe una respuesta confirmatoria afirmativa del proyecto. Falta N=3 E2E finalista, que no se solicita ni ejecuta. |
| MEDIUM / NOT_VERIFIED — retroanálisis | Fallo ambiental en raw_input antes de aprender: falta caché corregida en inbox; la caché de experiments sí verifica. No existen seis CSV, curva descriptiva o conjunto.csv, por lo que no se afirma igualdad de filas ni resultado de ese instrumento. Requiere la autorización concreta del diagnóstico de recuperación. |
| MEDIUM / NOT_VERIFIED — curva contractual | El inventario de fábrica contiene el punto predeclarado, métricas, intervalos y políticas, pero ninguna curva completa de TP frente a volumen de alertas del apartado 9. No se atribuye ese requisito a la fábrica ni a CSV inexistentes. El fallo de los criterios observados no autoriza añadir otra evaluación favorable, cambiar el punto o ampliar la receta después de resultados. |
| LOW — nomenclatura territorial | La vista genérica national recibe aquí solo Meta/Tolima. No es evaluación nacional ni evidencia independiente adicional. |
| LOW — nomenclatura de agregación | INCONCLUSO_POR_INESTABILIDAD es el estado canónico cuando las cinco consistencias no cumplen; en este caso son numéricamente idénticas. No es una afirmación de dispersión entre semillas ni la decisión científica INCONCLUSIVE del equipo. |
| LOW — independencia | Este agente preparó, ejecutó y revisó. Esta revisión no cumple independencia: se recomienda otro chat o revisor humano antes de aceptar conclusiones. |

## Afirmaciones y decisiones pendientes

Demostrado técnicamente: fábrica E2E completa, identidades verificables, comparación
emparejada bajo el punto predeclarado, los valores y los incumplimientos descritos.
No demostrado: mejora de la hipótesis bajo su criterio predeclarado,
confirmación independiente, resultado del retroanálisis, cobertura de curva
contractual de fábrica, utilidad sanitaria, campeón o autorización operativa.

El equipo debe resolver la recuperación pendiente y la revisión independiente,
y asignar explícitamente POSITIVE/NEGATIVE/INCONCLUSIVE antes de cerrar el
registro. Hasta entonces RUNNING/PENDING y scientific_conclusion NOT_APPROVED.
No se repite la fábrica, no se cambia la receta y no se publica nada.
