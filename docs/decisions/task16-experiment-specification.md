Estado: APROBADA PARA VALIDACIÓN DE FÁBRICA
Versión: T16-FACTORY-XGB-S53-v1
Ejecución autorizada: SÍ, exclusivamente para reproducibilidad de tarea 16

# Especificación normativa de validación de fábrica V3

Aprobada por: Equipo SAT DENGUE, aprobación explícita comunicada por el usuario en esta conversación; integrantes no identificados todavía.
Fecha: 2026-11-07, registro de la autorización en esta conversación (America/Bogota); fecha formal del acta no informada.
Tarea: 16. V3 es la autoridad normativa. V2 es únicamente procedencia histórica;
no sus calendarios, semillas, resultados, grillas o aprobaciones. Esta versión
sustituye la propuesta anterior, conservada en el historial Git.

## Alcance aprobado

Dos modelos independientes T+1/T+2, exclusivamente los 33 predictores canónicos
actuales, sin variables G ni presupuesto del canal. XGBoost 3.0.5 fijo, 80 árboles,
profundidad 2, eta 0.05 y regularización lambda=1/alpha=0; semilla **53**, CPU,
hist y un hilo. Sin HPO, early stopping, balanceo, refit, selección de semillas,
campeón ni autorización operativa. La zona se codifica con las cuatro categorías
fijas y columnas explícitas de la configuración; matriz interna float32 de 36
columnas. El esquema externo conserva las 33 entradas y su orden canónico.

El bloque JSON siguiente es la representación normativa completa de
`pipeline/conf/base/parameters_experiment.yml` bajo la clave `factory_experiment`.
Las pruebas exigen igualdad estructural exacta. Los parámetros nativos resueltos
incluyen aliases y ajustes internos de XGBoost 3.0.5: no se aceptan defaults
silenciosos que cambien resultados. `boost_from_average=1` estima el intercepto
inicial solo de train; la marca ESTIMATED_FROM_TRAIN_ONLY es exclusivamente la
regla de conformidad de configuración, no un valor enviado a XGBoost. El valor
aprendido real se conserva íntegro en la identidad del modelo y en N=3.

## Configuración efectiva completa

```json
{
  "specification": "T16-FACTORY-XGB-S53-v1",
  "authority": "V3",
  "execution": "factory_reproducibility_only",
  "horizons": [
    1,
    2
  ],
  "seed": 53,
  "predictors": [
    "dengue_notifications_count",
    "dengue_grave_notifications_count",
    "total_notifications_count",
    "rain_mm_month_sum",
    "surface_runoff_mm_month_sum",
    "total_evaporation_mm_month_sum_ecmwf",
    "solar_radiation_mj_m2_month_sum",
    "temp_mean_c_month_mean",
    "dewpoint_mean_c_month_mean",
    "soil_water_l1_month_mean",
    "wind_u_ms_month_mean",
    "wind_v_ms_month_mean",
    "p25_canal_t",
    "p50_canal_t",
    "p75_canal_t",
    "zona_canal_t",
    "month_of_year",
    "dengue_notifications_count_lag1",
    "dengue_notifications_count_lag2",
    "dengue_notifications_count_lag3",
    "dengue_notifications_count_lag12",
    "dengue_grave_notifications_count_lag1",
    "dengue_grave_notifications_count_lag2",
    "dengue_grave_notifications_count_lag3",
    "dengue_grave_notifications_count_lag12",
    "total_notifications_count_lag1",
    "total_notifications_count_lag2",
    "total_notifications_count_lag3",
    "total_notifications_count_lag12",
    "p25_h5_t1",
    "p75_h5_t1",
    "p25_h5_t2",
    "p75_h5_t2"
  ],
  "predictor_availability": {
    "dengue_notifications_count": 0,
    "dengue_grave_notifications_count": 0,
    "total_notifications_count": 0,
    "rain_mm_month_sum": 0,
    "surface_runoff_mm_month_sum": 0,
    "total_evaporation_mm_month_sum_ecmwf": 0,
    "solar_radiation_mj_m2_month_sum": 0,
    "temp_mean_c_month_mean": 0,
    "dewpoint_mean_c_month_mean": 0,
    "soil_water_l1_month_mean": 0,
    "wind_u_ms_month_mean": 0,
    "wind_v_ms_month_mean": 0,
    "p25_canal_t": 0,
    "p50_canal_t": 0,
    "p75_canal_t": 0,
    "zona_canal_t": 0,
    "month_of_year": 0,
    "dengue_notifications_count_lag1": -1,
    "dengue_notifications_count_lag2": -2,
    "dengue_notifications_count_lag3": -3,
    "dengue_notifications_count_lag12": -12,
    "dengue_grave_notifications_count_lag1": -1,
    "dengue_grave_notifications_count_lag2": -2,
    "dengue_grave_notifications_count_lag3": -3,
    "dengue_grave_notifications_count_lag12": -12,
    "total_notifications_count_lag1": -1,
    "total_notifications_count_lag2": -2,
    "total_notifications_count_lag3": -3,
    "total_notifications_count_lag12": -12,
    "p25_h5_t1": 0,
    "p75_h5_t1": 0,
    "p25_h5_t2": 0,
    "p75_h5_t2": 0
  },
  "preparation": {
    "zone_encoding": "fixed_onehot",
    "zone_mapping": {
      "EXITO": 0,
      "SEGURIDAD": 1,
      "ALERTA": 2,
      "EXCESO": 3
    },
    "zone_columns": [
      "zona_canal_t__EXITO",
      "zona_canal_t__SEGURIDAD",
      "zona_canal_t__ALERTA",
      "zona_canal_t__EXCESO"
    ],
    "matrix_columns": [
      "dengue_notifications_count",
      "dengue_grave_notifications_count",
      "total_notifications_count",
      "rain_mm_month_sum",
      "surface_runoff_mm_month_sum",
      "total_evaporation_mm_month_sum_ecmwf",
      "solar_radiation_mj_m2_month_sum",
      "temp_mean_c_month_mean",
      "dewpoint_mean_c_month_mean",
      "soil_water_l1_month_mean",
      "wind_u_ms_month_mean",
      "wind_v_ms_month_mean",
      "p25_canal_t",
      "p50_canal_t",
      "p75_canal_t",
      "zona_canal_t__EXITO",
      "zona_canal_t__SEGURIDAD",
      "zona_canal_t__ALERTA",
      "zona_canal_t__EXCESO",
      "month_of_year",
      "dengue_notifications_count_lag1",
      "dengue_notifications_count_lag2",
      "dengue_notifications_count_lag3",
      "dengue_notifications_count_lag12",
      "dengue_grave_notifications_count_lag1",
      "dengue_grave_notifications_count_lag2",
      "dengue_grave_notifications_count_lag3",
      "dengue_grave_notifications_count_lag12",
      "total_notifications_count_lag1",
      "total_notifications_count_lag2",
      "total_notifications_count_lag3",
      "total_notifications_count_lag12",
      "p25_h5_t1",
      "p75_h5_t1",
      "p25_h5_t2",
      "p75_h5_t2"
    ],
    "matrix_dtype": "float32",
    "missing": "error",
    "scaling": "none",
    "imputation": "none",
    "variables_g": false,
    "channel_budget": false
  },
  "candidate": {
    "family": "xgboost_onset",
    "adapter_version": "v1",
    "library": "xgboost",
    "library_version": "3.0.5",
    "rounds": 80,
    "parameters": {
      "booster": "gbtree",
      "objective": "binary:logistic",
      "tree_method": "hist",
      "device": "cpu",
      "nthread": 1,
      "n_jobs": 1,
      "seed": 53,
      "random_state": 53,
      "seed_per_iteration": false,
      "validate_parameters": true,
      "verbosity": 0,
      "disable_default_eval_metric": 1,
      "eta": 0.05,
      "max_depth": 2,
      "min_child_weight": 5,
      "lambda": 1.0,
      "alpha": 0.0,
      "gamma": 0.0,
      "max_delta_step": 0.0,
      "subsample": 1.0,
      "colsample_bytree": 1.0,
      "colsample_bylevel": 1.0,
      "colsample_bynode": 1.0,
      "max_bin": 128,
      "max_leaves": 0,
      "grow_policy": "depthwise",
      "sampling_method": "uniform",
      "base_score": 0.5,
      "boost_from_average": 1,
      "num_parallel_tree": 1,
      "max_cached_hist_node": 65536,
      "debug_synchronize": false,
      "multi_strategy": "one_output_per_tree",
      "scale_pos_weight": 1.0,
      "process_type": "default",
      "cache_opt": true,
      "max_cat_threshold": 64,
      "max_cat_to_onehot": 4,
      "monotone_constraints": "()",
      "interaction_constraints": "",
      "refresh_leaf": true,
      "sketch_ratio": 2.0,
      "sparse_threshold": 0.2,
      "extmem_single_page": false,
      "fail_on_invalid_gpu_id": false
    },
    "expected_native_configuration": {
      "learner": {
        "generic_param": {
          "device": "cpu",
          "fail_on_invalid_gpu_id": "0",
          "n_jobs": "1",
          "nthread": "1",
          "random_state": "53",
          "seed": "53",
          "seed_per_iteration": "0",
          "validate_parameters": "1"
        },
        "gradient_booster": {
          "gbtree_model_param": {
            "num_parallel_tree": "1",
            "num_trees": "80"
          },
          "gbtree_train_param": {
            "process_type": "default",
            "tree_method": "hist",
            "updater": "grow_quantile_histmaker",
            "updater_seq": "grow_quantile_histmaker"
          },
          "name": "gbtree",
          "specified_updater": false,
          "tree_train_param": {
            "alpha": "0",
            "cache_opt": "1",
            "colsample_bylevel": "1",
            "colsample_bynode": "1",
            "colsample_bytree": "1",
            "eta": "0.0500000007",
            "gamma": "0",
            "grow_policy": "depthwise",
            "interaction_constraints": "",
            "lambda": "1",
            "learning_rate": "0.0500000007",
            "max_bin": "128",
            "max_cat_threshold": "64",
            "max_cat_to_onehot": "4",
            "max_delta_step": "0",
            "max_depth": "2",
            "max_leaves": "0",
            "min_child_weight": "5",
            "min_split_loss": "0",
            "monotone_constraints": "()",
            "refresh_leaf": "1",
            "reg_alpha": "0",
            "reg_lambda": "1",
            "sampling_method": "uniform",
            "sketch_ratio": "2",
            "sparse_threshold": "0.20000000000000001",
            "subsample": "1"
          },
          "updater": [
            {
              "hist_train_param": {
                "debug_synchronize": "0",
                "extmem_single_page": "0",
                "max_cached_hist_node": "65536"
              },
              "name": "grow_quantile_histmaker"
            }
          ]
        },
        "learner_model_param": {
          "base_score": "ESTIMATED_FROM_TRAIN_ONLY",
          "boost_from_average": "1",
          "num_class": "0",
          "num_feature": "36",
          "num_target": "1"
        },
        "learner_train_param": {
          "booster": "gbtree",
          "disable_default_eval_metric": "1",
          "multi_strategy": "one_output_per_tree",
          "objective": "binary:logistic"
        },
        "metrics": [],
        "objective": {
          "name": "binary:logistic",
          "reg_loss_param": {
            "scale_pos_weight": "1"
          }
        }
      },
      "version": [
        3,
        0,
        5
      ]
    },
    "early_stopping": false,
    "hyperparameter_search": false,
    "class_balancing": false,
    "refit": false,
    "seed_selection": false
  },
  "calibration": {
    "representations": [
      "original",
      "sigmoid"
    ],
    "method": "logistic_on_raw_probability",
    "parameters": {
      "solver": "lbfgs",
      "penalty": "l2",
      "C": 1.0,
      "fit_intercept": true,
      "max_iter": 1000,
      "tol": 0.0001,
      "random_state": 53,
      "class_weight": null,
      "dual": false,
      "intercept_scaling": 1,
      "multi_class": "deprecated",
      "n_jobs": 1,
      "l1_ratio": null,
      "warm_start": false,
      "verbose": 0
    },
    "brier_tolerance": 1e-12,
    "tie": "original",
    "convergence": "fail"
  },
  "label_delay_months": 1,
  "embargo_months": 1,
  "reserved_start": "2025-01",
  "roles_by_horizon": {
    "1": {
      "train": {
        "start": "2018-01",
        "end": "2020-12",
        "support": {
          "n0": 10000,
          "n1": 1000,
          "municipalities": 900,
          "months": 36
        }
      },
      "calibration_fit": {
        "start": "2021-05",
        "end": "2021-10",
        "support": {
          "n0": 3000,
          "n1": 300,
          "municipalities": 900,
          "months": 6
        }
      },
      "calibration_selection": {
        "start": "2022-03",
        "end": "2022-08",
        "support": {
          "n0": 3000,
          "n1": 300,
          "municipalities": 900,
          "months": 6
        }
      },
      "threshold_selection": {
        "start": "2023-01",
        "end": "2023-06",
        "support": {
          "n0": 3000,
          "n1": 300,
          "municipalities": 900,
          "months": 6
        }
      },
      "evaluation": {
        "start": "2024-01",
        "end": "2024-11",
        "support": {
          "n0": 3000,
          "n1": 500,
          "municipalities": 900,
          "months": 11
        }
      }
    },
    "2": {
      "train": {
        "start": "2018-01",
        "end": "2020-12",
        "support": {
          "n0": 10000,
          "n1": 1000,
          "municipalities": 900,
          "months": 36
        }
      },
      "calibration_fit": {
        "start": "2021-05",
        "end": "2021-10",
        "support": {
          "n0": 3000,
          "n1": 300,
          "municipalities": 900,
          "months": 6
        }
      },
      "calibration_selection": {
        "start": "2022-03",
        "end": "2022-08",
        "support": {
          "n0": 3000,
          "n1": 300,
          "municipalities": 900,
          "months": 6
        }
      },
      "threshold_selection": {
        "start": "2023-01",
        "end": "2023-06",
        "support": {
          "n0": 3000,
          "n1": 300,
          "municipalities": 900,
          "months": 6
        }
      },
      "evaluation": {
        "start": "2024-01",
        "end": "2024-11",
        "support": {
          "n0": 3000,
          "n1": 500,
          "municipalities": 900,
          "months": 11
        }
      }
    }
  },
  "threshold": {
    "grid": [
      0.0,
      0.005,
      0.01,
      0.015,
      0.02,
      0.025,
      0.03,
      0.035,
      0.04,
      0.045,
      0.05,
      0.055,
      0.06,
      0.065,
      0.07,
      0.075,
      0.08,
      0.085,
      0.09,
      0.095,
      0.1,
      0.105,
      0.11,
      0.115,
      0.12,
      0.125,
      0.13,
      0.135,
      0.14,
      0.145,
      0.15,
      0.155,
      0.16,
      0.165,
      0.17,
      0.175,
      0.18,
      0.185,
      0.19,
      0.195,
      0.2,
      0.205,
      0.21,
      0.215,
      0.22,
      0.225,
      0.23,
      0.235,
      0.24,
      0.245,
      0.25,
      0.255,
      0.26,
      0.265,
      0.27,
      0.275,
      0.28,
      0.285,
      0.29,
      0.295,
      0.3,
      0.305,
      0.31,
      0.315,
      0.32,
      0.325,
      0.33,
      0.335,
      0.34,
      0.345,
      0.35,
      0.355,
      0.36,
      0.365,
      0.37,
      0.375,
      0.38,
      0.385,
      0.39,
      0.395,
      0.4,
      0.405,
      0.41,
      0.415,
      0.42,
      0.425,
      0.43,
      0.435,
      0.44,
      0.445,
      0.45,
      0.455,
      0.46,
      0.465,
      0.47,
      0.475,
      0.48,
      0.485,
      0.49,
      0.495,
      0.5,
      0.505,
      0.51,
      0.515,
      0.52,
      0.525,
      0.53,
      0.535,
      0.54,
      0.545,
      0.55,
      0.555,
      0.56,
      0.565,
      0.57,
      0.575,
      0.58,
      0.585,
      0.59,
      0.595,
      0.6,
      0.605,
      0.61,
      0.615,
      0.62,
      0.625,
      0.63,
      0.635,
      0.64,
      0.645,
      0.65,
      0.655,
      0.66,
      0.665,
      0.67,
      0.675,
      0.68,
      0.685,
      0.69,
      0.695,
      0.7,
      0.705,
      0.71,
      0.715,
      0.72,
      0.725,
      0.73,
      0.735,
      0.74,
      0.745,
      0.75,
      0.755,
      0.76,
      0.765,
      0.77,
      0.775,
      0.78,
      0.785,
      0.79,
      0.795,
      0.8,
      0.805,
      0.81,
      0.815,
      0.82,
      0.825,
      0.83,
      0.835,
      0.84,
      0.845,
      0.85,
      0.855,
      0.86,
      0.865,
      0.87,
      0.875,
      0.88,
      0.885,
      0.89,
      0.895,
      0.9,
      0.905,
      0.91,
      0.915,
      0.92,
      0.925,
      0.93,
      0.935,
      0.94,
      0.945,
      0.95,
      0.955,
      0.96,
      0.965,
      0.97,
      0.975,
      0.98,
      0.985,
      0.99,
      0.995,
      1.0
    ],
    "max_false_alarm_ratio_by_horizon": {
      "1": 0.8,
      "2": 0.8
    },
    "comparison": "probability_greater_or_equal_threshold",
    "denominator": "emitted_evaluable_alerts_TP_plus_FP",
    "zero_alerts": "infeasible",
    "objective": "maximum_onset_sensitivity",
    "tiebreak": [
      "fewer_false_alerts",
      "lower_false_alarm_ratio",
      "higher_threshold"
    ]
  },
  "baselines": [
    "train_prevalence",
    "non_excess_persists_no_new_onset"
  ],
  "metrics": [
    "average_precision",
    "auroc",
    "brier",
    "onset_sensitivity",
    "false_alarm_ratio",
    "alert_volume",
    "alert_fraction"
  ],
  "uncertainty": "not_estimated_factory_validation",
  "governance": {
    "purpose": "factory_validation_not_scientific_approval",
    "G5": "NOT_APPROVED",
    "champion_status": "NOT_SELECTED",
    "operational_authorization": false,
    "task17_started": false,
    "reserved_evidence": "consumed_retrospective_evidence"
  },
  "reproducibility": {
    "repetitions": 3,
    "execution": "clean_isolated_sequential_processes",
    "comparison": "exact_canonical_json_and_sha256",
    "allow_fourth_run": false,
    "on_failure": "stop_without_parameter_changes"
  },
  "acquisition": {
    "manifest": "conf/releases/approved-raw.json",
    "cache": "data/01_raw/inbox",
    "authentication": "environment_only",
    "require_private": true
  },
  "runtime": {
    "workspace": "data/factory-validation",
    "evidence": "docs/evidence/task16/factory-experiment",
    "tracking": "isolated_local_aggregate_receipts"
  },
  "execution_threads": {
    "OMP_NUM_THREADS": 1,
    "OPENBLAS_NUM_THREADS": 1,
    "MKL_NUM_THREADS": 1,
    "NUMEXPR_NUM_THREADS": 1
  }
}
```

## Objetivos, disponibilidad y soporte

Cada horizonte usa sus propias claves, matrices, modelo, prevalencia,
calibrador y umbral. Los cinco intervalos objetivo son inclusivos:

| Rol | Objetivos | N0 mínimo | N1 mínimo | Municipios mínimo | Meses exactos |
|---|---|---:|---:|---:|---:|
| train | 2018-01 a 2020-12 | 10000 | 1000 | 900 | 36 |
| calibration_fit | 2021-05 a 2021-10 | 3000 | 300 | 900 | 6 |
| calibration_selection | 2022-03 a 2022-08 | 3000 | 300 | 900 | 6 |
| threshold_selection | 2023-01 a 2023-06 | 3000 | 300 | 900 | 6 |
| evaluation | 2024-01 a 2024-11 | 3000 | 500 | 900 | 11 |

Disponibilidad A(S)=S+1 mes como supuesto retrospectivo, embargo B=1 mes y
límite reservado 2025-01. Se conserva `TemporalPolicy`, `guard_development`,
`validate_data` y `preflight_roles`: S=T+h y A también deben preceder a 2025.
Cada transición exige max(disponibilidad de dependencias)+B < primer origen
consumidor. Sus límites A+B son 2021-02, 2021-12, 2022-10 y 2023-08; preceden
respectivamente a los primeros orígenes T+1 2021-04/2022-02/2022-12/2023-12 y
T+2 2021-03/2022-01/2022-11/2023-11. Diciembre de 2024 como objetivo se excluye
porque A sería enero de 2025. Un origen anterior a 2025 nunca habilita un
objetivo o disponibilidad reservados. Las observaciones crudas >=2025 quedan
en cuarentena antes de normalizar o agregar; también se excluyen las de 2026.

Primero se validan claves, meses, municipios y todos los soportes de los cuatro
roles productores de **ambos** horizontes; ningún modelo se ajusta antes. Para
evaluation, antes del ajuste solo se comprueban claves, meses y municipios,
sin leer valores de y. Solo después de freeze y predicciones se leen esas
etiquetas, se verifican N0/N1 y se calculan métricas. Un fallo invalida el
resultado y detiene la receta sin reajustar ni reintentar.

## Calibración, métricas y gobierno

Se reutiliza la sigmoide sobre probabilidad original, lbfgs/L2/C=1/intercepto,
1000 iteraciones/tol=1e-4/semilla 53. Se elige sigmoide únicamente si Brier mejora
en más de 1e-12; empate conserva original. Cada horizonte selecciona entre los
201 umbrales k/200, k=0..200, con FAR máxima 0.80. FAR=FP/(TP+FP); sin alertas
es indefinida y no factible. Máxima sensibilidad; desempates por menos FP,
menor FAR y mayor umbral. La política no contiene presupuesto del canal.

Se reportan métricas puntuales agregadas por horizonte mediante las definiciones
V3 existentes, con prevalencia solo de train y persistencia de no nuevo inicio.
No se añade bootstrap o búsqueda de utilidad para la validación de fábrica.
Un rendimiento deficiente o FAR posterior superior a 0.80 se reporta sin cambios:
no determina el cierre técnico si el procedimiento fue válido y reproducible.
2025 permanece `consumed_retrospective_evidence`: no interviene en ningún ajuste,
selección, calibración, umbral o política FAR y no es un holdout ciego.

## Certificación E2E y evidencia

`factory_validation` adquiere solo las cinco fuentes fijadas por manifiesto;
Excel continúa excluido. Después de adquisición, ciencia recibe únicamente
`ResolvedBundle` neutral. Tres procesos limpios, aislados y secuenciales
reconstruyen desde esos crudos sin compartir derivados, modelos, matrices,
decisiones, resultados o tracking. Se certifica el conjunto E2E antes de liberar
un resultado de fábrica; no se reutiliza el canónico previo como entrenamiento.
La certificación canónica histórica sigue intacta y no sustituye esta N=3.

La identidad exacta comprende canónico, claves por rol/horizonte, matrices y
orden de entradas, JSON completo de modelo y configuración efectiva, probabilidades
originales y calibradas, representación, umbral, decisiones, métricas, hashes,
configuración y linaje. El JSON canónico incluye árboles y todo estado predictivo;
no usa pickle, archivos binarios ni exclusiones de estado. Fechas de ejecución,
PID y directorios son metadatos operativos separados, nunca parte de identidad.
No se persisten rutas privadas, filas, modelos ni credenciales en evidencia Git.

Los recibos previos en `docs/evidence/task16/` son inmutables. Nuevos agregados
se escriben exclusivamente, sin sobrescritura, en `factory-experiment/`. Si un
soporte/gate falla o hay divergencia, se detiene sin cuarta corrida ni otra receta.
Las corridas restantes quedan explícitamente no ejecutadas, no simuladas.
La tarea 16 solo se cierra tras todos los gates; tarea 17 permanece PENDIENTE.

Comando: `uv run --directory pipeline kedro run --pipelines factory_validation`.
No hay autorización de publicación, push, merge, force push u otro PR.
