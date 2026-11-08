# T18 — auditoría científica del pipeline V3

**Conclusión: APPROVED_WITH_LIMITATIONS.** No se identificó un fallo científico
bloqueante en los contratos implementados. Esta conclusión aprueba la revisión
metodológica de la fábrica; no acredita superioridad predictiva, un campeón,
uso operativo ni reproducción de las tandas históricas.

Commit auditado: `00c540445fbe18f6e9aff05960afb6eac6a97d84`.
Rama `feature/pipeline-e2e`, PR #1 abierto hacia `main`, árbol inicialmente limpio.
T17 completa, 17/22; manual versionado. Solo `plan.md` mantiene estados operativos.

## Alcance y método

Se leyeron las autoridades documentales solicitadas y se contrastaron con código,
pruebas y recibos versionados. La revisión no se limita a ratificar informes de
cierre: verificó inventarios, firmas y aritmética de agregados y comparó AP/AUROC/
Brier en **1.134 casos artificiales enumerados** con las funciones independientes
de scikit-learn instaladas desde el lock. Se ejecutó la suite completa: **536
pruebas**, seis avisos de OmegaConf, sin fallos ni omisiones, en macOS local.
Lock/sync y Ruff verdes. No se ejecutaron nuevos experimentos científicos,
entrenamientos reales, adquisición privada ni reproducción real N=3; no se solicitó
ni utilizó una credencial HF. Los ajustes sintéticos de las pruebas existentes son
contratos de software, no evidencia científica nueva.

Se verificaron por separado la igualdad de las tres identidades T16, sus digests,
la aritmética de métricas reconstruibles desde agregados y la conservación de los
49 archivos protegidos. Los dos paquetes de EXP001/EXP002 pasaron inventarios,
firmas, configuración efectiva frente al YAML y clasificación NOT_APPLICABLE.

La independencia es metodológica respecto de los informes de cierre: no equivale
a una revisión humana externa y ciega. Esa aprobación independiente y los checks
finales siguen siendo requisitos externos antes del merge.

## Matriz de contraste

PASS significa control inspeccionado y probado; PARTIAL significa cobertura
limitada explícita; NOT_VERIFIED no se convierte en cumplimiento.

| ID | Área y estado | Evidencia concreta y alcance |
|---|---|---|
| S01 | Fuentes — PASS | `raw/contract.py:INVENTORY,raw_contract_validation`, `acquisition/raw_manifest.py:validate_raw_manifest`; `test_raw_canonical.py::test_inventory_rejects_before_projection`, `test_forbidden_input_names`, `test_mutable_revisions_rejected_before_acquisition`. Inventario exacto de cinco archivos, tamaños/SHA-256 y revisión fijada; se rechazan Excel, derivados y clima recortado. |
| S02 | Privacidad remota actual — NOT_VERIFIED | `acquisition/sources.py:HuggingFaceSource.verify_private`, `test_private_release.py::test_environment_auth_is_explicit_and_not_kept_in_source`; recibos históricos T16 de privacidad/acquisición. El código exige private=true y SHA exacto. No se consultó la visibilidad ni las cuentas actuales, por la prohibición de credenciales/adquisición. |
| S03 | Neutralidad de proveedor — PASS | `acquisition/contracts.py:DataSource,ResolvedBundle`; `sources.py:create_source`; `raw/build.py:build`. `test_raw_reproducibility.py::test_scientific_modules_have_no_provider_imports`. Proveedores confinados a adquisición; S3 solo simulado y Zenodo privado no habilitado. |
| S04 | Territorio/eventos — PASS | `raw/producers.py:geography_normalization,epidemiology_normalization`; `test_residence_ini_sin_and_no_consecutive_dedup`, `test_rejection_reasons_reconcile`, `test_geography_unique_dimension_and_provenance`. Residencia e INI_SIN, eventos 210/220 separados, sin fallback ni deduplicación por CONSECUTIVE. Son notificaciones, no personas ni casos confirmados. |
| S05 | Clima/joins/conservación — PASS | `raw/producers.py:climate_daily_normalization,climate_monthly_aggregation`, `raw/panel.py:canonical_panel,canonical_validation`; pruebas de días incompletos, duplicados, cardinalidad y conservación. Cuatro sumas/cinco medias; nulos preservados; cuadrícula fija y ceros solo dentro de cobertura epidemiológica. |
| S06 | Esquema y N=3 — PASS | `raw/serialization.py:verify_artifact,load_canonical`, `raw/reproducibility.py:canonical_reproducibility,certify_then_consume`; `test_serialization_round_trip_preserves_schema_types_values_and_nulls`, `test_injected_divergence_stops_before_training`. Recibos `task16/certify-real.json` y `task16/factory-experiment/run-{1,2,3}.json`: identidades/digests concordantes. Se verificó evidencia existente; no se repitieron los crudos. |
| S07 | Cuarentena/causalidad — PASS | `raw/build.py:build,retained_frame`, `raw/temporal.py:raw_temporal_projection,raw_temporal_quarantine`, `domain/canonical.py:build_table`; `test_projection_quarantine_precedes_values_and_reconciles`, `test_retained_rows_survive_chunk_boundaries_without_reserved_values`. Solo claves antes de cuarentena; lags e historia H5 anteriores al origen. |
| S08 | Autoridad temporal/etiquetas — PASS | `domain/temporal.py:TemporalPolicy,guard_development`, `domain/onset.py:build_labels,operational_eligibility`; tests de semántica, mes ausente, T+1/T+2 y centinelas 2025 antes de lectores/consumidores. Elegibilidad solo en T; T+2 no se condiciona con T+1 observado. |
| S09 | Demora/embargo — PARTIAL | `experiments/roles.py:TemporalPlan,preflight_roles`, `rolling.py:validate_data,fold_inputs`; `test_roles_are_disjoint_ordered_and_embargo_is_not_training`. La anterioridad estricta se comprueba; demora de un mes en T16 es un supuesto aprobado, no una medición de disponibilidad operativa. |
| S10 | Rolling-origin — PARTIAL | `rolling.py:build_folds,run_rolling`; `test_expanding_calendar_and_mature_disjoint_inputs`, `test_reordering_and_future_changes_do_not_affect_prior_folds`. Arnés mensual disponible/probado; `factory.engine` usa cinco roles fijos. No son el rolling anual de G ni los ocho cortes históricos V2. |
| S11 | Preparación/soporte — PARTIAL | `factory/engine.py:prepare,preflight`, `models/xgboost.py:matrix`; pruebas de soporte previo a todo fit y esquema. Se certifican los 33 predictores aunque la matriz use un subconjunto; el filtro de complete-case es conservador y limita cobertura. La cohorte T+2 requiere no exceso en T, una restricción declarada que no representa todos los inicios posibles. |
| S12 | Freeze/calibración/umbrales — PASS | `experiments/procedure.py:fit_procedure,predict_frozen`, `decisions.py:choose_representation,select_threshold`; `test_each_fit_and_selection_receives_only_its_own_labels`, `test_evaluation_labels_and_future_values_cannot_change_frozen_decisions`, `test_factory.py::test_evaluation_labels_created_only_after_both_predictions`. Sin HPO/refit; selección por Brier y grilla/FAR antes de evaluación. |
| S13 | Métricas/soporte emparejado — PASS | `evaluation/metrics.py:metric_records`, `paired.py:_joined,evaluate`; pruebas manuales de empates/denominadores y ausencias comunes; contraste adicional de 1.134 casos con sklearn. FP/(TP+FP), sensibilidad/inicios conocidos; FAR sin alertas indefinido. Se verificaron proporciones/soportes T16; AP real no se recalcula sin scores por fila. |
| S14 | Líneas base científicas — PARTIAL | `procedure.py:predict_frozen`, `factory/engine.py:evaluate`; `test_prevalence_train_only_and_persistence_share_all_keys`. Prevalencia train-only y persistencia degenerada sin nuevo inicio, ambas sobre las mismas filas. No incluye canal estándar/ajustado/condicionado de la bitácora; no acredita utilidad frente al canal. |
| S15 | Incertidumbre — PARTIAL | `evaluation/paired.py` y `test_actual_resamples_keep_all_months_together`, `test_paired_bootstrap_valid_and_undefined_replicates_counted`. Bootstrap municipal descriptivo, sin cobertura calibrada ni réplica del bootstrap histórico por ventanas. No se conecta a la salida de fábrica ni se estimó incertidumbre real T16. |
| S16 | Gobernanza/historia — PASS | `experiment_management/registry.py`, `configuration.py`, `evidence.py`, `runner.py`, `tracking.py`, `compare.py`; 45 pruebas T17. Hashes de bytes cargados, allowlists, aprobación previa, reserva exclusiva, terminales, inventarios, conclusiones estructuradas y comparación sin microdatos/MLflow. El significado científico de conclusiones requiere revisión humana. |
| S17 | Bitácora y límites de reproducción — NOT_VERIFIED | Las tandas 1–9 se conservan como historia del autor: esta auditoría no recupera sus scripts/matrices ni reproduce sus métricas. `temporal-experiments.md` y `paired-evaluation.md` declaran adaptaciones/NOT_REPRODUCED. El apéndice T17 solo registra infraestructura y no agrega métricas de fixtures a la ciencia. |
| S18 | T16/2025/gobierno — PASS | `tools/check_experiment_preservation.py`; 49 hashes iguales, 22 JSON y 16 recibos previos intactos; identidad N=3 común preservada. T16 es validación de ingeniería, no selección. 2025 sigue siendo evidencia retrospectiva consumida, no holdout independiente. |
| S19 | Portabilidad actual — PARTIAL | PR #1/HEAD 00c5404: Pipeline quality, Ubuntu y macOS verdes; Windows falla 31 pruebas por hashes de Markdown tras conversión de finales de línea. El guard rechaza correctamente esos bytes; no se encontró corrupción en los originales Git. Pendiente corrección de transporte/checks antes del merge; no se atribuye portabilidad completa al HEAD. |

Las funciones citadas pertenecen a `pipeline/src/sat_dengue_pipeline/` y las
pruebas a `pipeline/tests/`. La evidencia está bajo `docs/evidence/`.

## Hallazgos por severidad

No se identificaron hallazgos científicos CRITICAL o HIGH ni una fuga temporal.

- **MEDIUM SC-01 — comparación científica incompleta.** Las referencias actuales
  de fábrica no sustituyen el canal condicionado ni demuestran la mejora G.
  Mitigación: limitar las conclusiones a ingeniería; una afirmación futura de
  utilidad necesita protocolo y líneas base científicas aprobadas sobre cohortes
  comparables. Responsable: equipo científico; seguimiento antes de una corrida
  que pretenda demostrar superioridad.
- **MEDIUM SC-02 — disponibilidad y selección de cohorte.** Demora aprobada,
  complete-case de 33 variables y elegibilidad al origen son restricciones
  técnicas. No prueban disponibilidad prospectiva, cobertura poblacional o
  transportabilidad. Responsable: equipo científico; medición de latencias y
  población antes de cualquier interpretación operativa.
- **LOW SC-03 — incertidumbre y verificabilidad real.** Hay pruebas del método
  descriptivo, pero no intervalos reales T16 ni scores versionados para recalcular
  AP/AUROC reales. Conservar privacidad; no publicar microdatos para remediarlo.
  Responsable: revisores científicos; verificación controlada en otro alcance.
- **LOW SC-04 — referencias históricas.** Documentos congelados T16 conservan
  numeración y estado de aquella fase. Se leen junto con DEC-024 y `plan.md`;
  no se reescriben para simular estados actuales. Responsable: documentación;
  navegación operativa debe apuntar a la autoridad vigente.
- **MEDIUM TECH-01 — checkout Windows.** Integridad por bytes falla al convertir
  Markdown; es una limitación técnica real y gate de merge, no un resultado
  científico negativo. Responsable: mantenedor; corrección local sin cambiar
  recetas/hashes y nueva CI nativa antes del merge.

## Correspondencia con la bitácora

La bitácora distingue exceso de inicio y explica las correcciones de métricas y
líneas base de sus tandas. V3 implementa inicio exacto, FAR contra inicio y
restricción informacional correcta de T+2. No reproduce G, presupuesto del canal,
los 76 municipios/cortes ni su rolling anual: esas cifras no se atribuyen al
canónico nacional ni a T16. La persistencia degenerada se conserva como referencia
mínima documentada, sin afirmar que vencerla pruebe utilidad. La comparación
condicionada y la evidencia científica histórica quedan fuera de lo demostrado
por esta fábrica. El NOT_APPROVED/NOT_SELECTED histórico no cambia.

## Conclusión y decisiones pendientes

APPROVED_WITH_LIMITATIONS para la auditoría de lo efectivamente implementado y
su evidencia técnica. No se encontró una contradicción científica sustancial,
fuga o evidencia histórica corrupta que obligue a detener T18. PARTIAL y
NOT_VERIFIED permanecen expresamente abiertos con el alcance descrito. La
visibilidad remota actual, la replicación de las tandas, latencias y validación
prospectiva no se verificaron ni se autorizan aquí. No se aprueba una política de
alertas, un modelo o un merge. Puede iniciarse T19 tras registrar este cierre.
