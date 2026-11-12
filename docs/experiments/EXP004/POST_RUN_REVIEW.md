# EXP004 — revisión científica posterior para el cierre NEGATIVE

Fecha: 12 de noviembre de 2026. Skill: `sat-dengue-scientific-review`, modo
`post-run`, actualizada para la decisión humana explícita de cierre.
Recomendación: **APPROVED_WITH_LIMITATIONS**, exclusivamente para la correspondencia
entre receta, evidencia existente y resultado humano **NEGATIVE** de EXP004.
No acredita cumplimiento integral del contrato ni aprueba un modelo o campeón.
La revisión la realiza el mismo agente que preparó y ejecutó el experimento:
**no es una revisión independiente**. La decisión corresponde al equipo SAT DENGUE,
comunicada por la persona usuaria; no se deriva automáticamente de esta revisión.

El bloqueo anterior por retroanálisis pendiente se resuelve con su recuperación
ya validada; la decisión científica humana ya fue recibida. La curva completa
de fábrica permanece **NOT_PRODUCED/DEFERRED** por decisión explícita del equipo,
sin impedir el cierre negativo de la hipótesis específica en el punto predeclarado.
La versión previa de esta revisión se conserva en Git en 6cfb487; no se reescribe
ningún recibo cerrado. Este cierre no ejecuta nueva ciencia ni reconstruye predicciones.

## Evidencia contrastada

Contrato 1.0.0 APROBADO, manual, reglas temporales y de evaluación emparejada,
revisión científica histórica, protocolo/configuración R2 con hashes aprobados,
preinscripción y [aprobación humana](APPROVAL.md).
[Inventario](../../evidence/experiments/EXP004/04a0554e6fa7470394b185b5dab36d7a/inventory.json),
recibo, linaje, configuración efectiva y 99 fragmentos científicos del mismo
paquete. [Auditoría de ejecución](EXECUTION_AUDIT.json),
[síntesis agregada](RESULTS_SUMMARY.json), [conclusiones NEGATIVE](CONCLUSIONS.md),
[resultado en bitácora](../../bitacora/tanda-exp004-resultados.md) y
[fallo de retroanálisis](RETROANALYSIS_ATTEMPT_1.json),
[autorización de recuperación](RECOVERY_AUTHORIZATION.md),
[segundo intento](RECOVERY_ATTEMPT_2.json), [resultado recuperado](RECOVERY_RESULT.md),
[validación de los seis CSV](RECOVERY_VALIDATION.json) y
[verificación de recuperación](RECOVERY_VERIFICATION.json).

Para este cierre se volvieron a verificar los hashes R2, los 105 archivos del
inventario único y los seis CSV ya existentes. Se contrastaron las tres lecturas
de fábrica y los dos resultados de retroanálisis con la decisión humana, en las
cinco semillas. Todos coinciden; no se recalculan modelos, predicciones,
desenlaces, curvas o intervalos. La decisión y el recibo de cierre están en
`CLOSURE.json`.

El inventario verifica 105 archivos y firma de ejecución
`24165ef5dfc03fbef19b72eaef543d3282891427354c047e784d09e34d74d98d`;
protocolo y configuración siguen exactamente bajo los hashes aprobados.
Código productivo idéntico al revisado antes de ejecutar. El único ajuste técnico
posterior a la ejecución afectó una prueba histórica que asumía solo EXP001/EXP002; no afecta
modelos, datos, receta, evaluación o los recibos ya producidos.

## Hallazgos

| Severidad / estado | Evidencia e implicación |
|---|---|
| PASS — cambio único y cohortes | 140 variantes y 210 modelos; 105 pares por horizonte. Se verificaron 525 digests de claves, predictores y matrices de roles entre brazos; preflight verificó etiquetas productoras antes de fit, y evaluación emparejada comprobó LINK/onset tras predecir. No se igualan cohortes primaria y secundaria entre sí. |
| PASS — pesos y aislamiento | 210 resúmenes con media uno, peso crudo más reciente uno y pesos positivos; referencia solo de train, fit_only. El código congelado aplica sample_weight solo a LogisticRegression.fit. No hay filas de pesos persistidas, HPO, otra vida media o transferencia de estado. |
| PASS — temporalidad | Canónico reconstruido operational_full idéntico al certificado; cuarentena de 2025 antes de productores. Los 140 planes, ventanas, orígenes y disponibilidades de roles terminan antes de 2025. Todas las variantes informan evaluation_reads_after_both_predictions=true. |
| PASS — identidad y semillas | Fábrica única, COMPLETED, desde a075b0d con dirty=false. Exactamente semillas 7/13/31/53/101; todas conservadas. Las tres diferencias agregadas e intervalos son idénticos en las cinco, sin sumar I o elegir una. Seed base 53 del recibo no sustituye el bloque científico multisemilla. |
| PASS — hipótesis y decisión humana | T+1: 130 frente a 131 TP, +0,1686 pp, IC95 % [−0,8293; 1,1746], con 3/7 cortes positivos, dos deterioros y dos empates en cada semilla. No satisface cota inferior >0 ni mayoría 4/7 predeclarada. T+2 primaria: 81/84 TP, +0,6961 pp [−0,6609; 2,1284]; secundaria: 97/101 TP, +0,6745 pp [−0,5320; 1,9516]. Ninguna rescata T+1. NEGATIVE fue decidido explícitamente por el equipo; no se infiere igualdad exacta o efecto nulo de intervalos que incluyen cero. |
| PASS — regla de 10 pp y seguridad | En cada semilla y brazo: 0/7 cortes T+1 pasan ganancia y cota; T+2 primaria tiene 1/7, pero falla carga; secundaria 2/7, pero falla persistencia y A/C en esos cortes. Todas las lecturas tienen 0/7 votos completos. Sin control negativo CUMPLE ni violación de cupo en las celdas conjuntas. No se aplicó el criterio histórico de 5 pp. |
| PASS — B secundaria | Persistencia es EVALUABLE y B obligatoria en todos los cortes secundarios conjuntos; ambos brazos solo la superan en 2021. Ese corte tiene precisión insuficiente frente al canal. Primaria conserva NO_EVALUABLE/DEGENERATE_PRIMARY_COHORT sin inventar una victoria. |
| MEDIUM — soporte territorial | Los siete cortes conjuntos son suficientes. Las celdas departamentales pequeñas permanecen excluidas del voto; Meta T+2 primaria queda NO_EVALUABLE en ambos brazos. El agregado conjunto no valida las celdas pequeñas. Fragmentos científicos preservan sus N/I y todos los desgloses. |
| MEDIUM — exploratorio y disponibilidad | Hipótesis y periodos ya explorados; demora y embargo son supuestos, no evidencia de disponibilidad histórica o ausencia de backfill. No cabe una respuesta confirmatoria afirmativa del proyecto. Falta N=3 E2E finalista, que no se solicita ni ejecuta. |
| PASS — retroanálisis recuperado | Primer fallo conservado, previo al ajuste; única invocación adicional autorizada completada. Seis CSV verifican sus hashes. 815 pares de folds, 1.630 registros de ajuste, 81.240 predicciones, cero omisiones e igualdad de claves/etiquetas en la lectura primaria por horizonte, semilla y fold. T+1 uniforme/reciente: 359/361 TP; T+2: 253/251, idénticos en las cinco semillas. El cambio +2/−2 no muestra mejora estable. No se mezcla su instrumento descriptivo con la fábrica ni se le atribuye secondary_t2. |
| MEDIUM / NOT_PRODUCED/DEFERRED — curva contractual | La curva completa de alertas de fábrica del apartado 9 sigue sin producirse y el equipo decidió diferirla. curva.csv del retroanálisis no la sustituye. EXP004 no acredita cumplimiento integral del contrato, no puede seleccionar champion ni sustentar un resultado afirmativo del proyecto. La limitación no impide NEGATIVE sobre la hipótesis de 36 meses en el punto predeclarado; no se amplía la receta ni se genera evidencia para repararla. |
| LOW — nomenclatura territorial | La vista genérica national recibe aquí solo Meta/Tolima. No es evaluación nacional ni evidencia independiente adicional. |
| LOW — nomenclatura de agregación | INCONCLUSO_POR_INESTABILIDAD es el estado canónico cuando las cinco consistencias no cumplen; en este caso son numéricamente idénticas. No es una afirmación de dispersión entre semillas ni la decisión científica INCONCLUSIVE del equipo. |
| LOW — independencia | Este agente preparó, ejecutó y revisó. Esta revisión no cumple independencia: se recomienda otro chat o revisor humano antes de aceptar conclusiones. |

## Correspondencia de la decisión y límites pendientes

Demostrado técnicamente: fábrica E2E completa, identidades verificables, comparación
emparejada bajo el punto predeclarado, los valores y los incumplimientos descritos.
La decisión **NEGATIVE** es coherente con el incumplimiento predeclarado de T+1,
los intervalos que incluyen cero y el resultado adicional sin mejora estable.
Rechaza únicamente la ponderación exponencial de 36 meses evaluada en EXP004;
no demuestra que toda estrategia de actualización temporal sea inútil. No es
una respuesta confirmatoria negativa sobre toda la pregunta del proyecto.

No demostrado: mejora sólida bajo el criterio predeclarado, confirmación
independiente, curva contractual completa de fábrica, cumplimiento integral,
eficacia sanitaria, campeón o autorización operativa. No se cambia ningún
veredicto automático preservado para equipararlo al resultado científico humano.

La autorización humana permite la transición oficial RUNNING/PENDING a
COMPLETED/NEGATIVE con las conclusiones actualizadas. Esta recomendación no
confiere independencia a la revisión ni selecciona un modelo. Los recibos
históricos conservan scientific_conclusion NOT_APPROVED; el cierre humano
posterior se documenta aparte. La curva queda diferida y cualquier trabajo
futuro sobre ella, otras hipótesis o confirmación requiere autorización propia.
No se repite la fábrica o el retroanálisis, no se modifica plan.md ni se publica.
