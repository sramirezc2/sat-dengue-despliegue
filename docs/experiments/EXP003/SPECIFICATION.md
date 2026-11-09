# EXP003 — Regresión logística sin clima frente al canal condicionado (contrato v0.1.0)

Tipo: `scientific`. Hipótesis: EXP003-H1. Estado: `PROPOSED`. Nivel de afirmación esperado: exploratorio (§3 del contrato); 2024 ya se usó en análisis previos y no es una cohorte confirmatoria. Requiere revisión científica y aprobación de otra persona del equipo antes de ejecutarse.

## Pregunta (§2)
En los municipios de Meta y Tolima, ¿una regresión logística L2 sin variables climáticas, con información disponible al cierre de T, anticipa en T+1 y T+2 más inicios de exceso de dengue que el canal endémico condicionado, con el mismo presupuesto de alertas y sin aumentar la carga de falsas alertas más allá de la tolerancia?

## Único cambio principal
Respecto a la receta XGBoost de referencia, cambia la familia del candidato a `logistic_onset` v1 (C = 1, max_iter = 5000) y se quitan las 9 variables de clima. La preparación aplica log1p a conteos y umbrales y estandariza con estadísticas aprendidas solo en `train`.

## Población, datos y roles (§4, §5)
- Población: 76 municipios de Meta (50) y Tolima (73), con `population.department_codes`.
- Manifiesto privado aprobado `satd-raw-a1a7f237`. Horizontes T+1 (primario) y T+2 (secundario). Demora de etiqueta de 1 mes.
- Cinco roles fijos de la fábrica. En T+1: `train` 2018-01 a 2020-12, `calibration_fit` 2021-05 a 2021-10, `calibration_selection` 2022-03 a 2022-08, `threshold_selection` 2023-01 a 2023-06 y `evaluation` 2024-01 a 2024-11.
- 2025 no participa.

## Comparadores (§8)
- **Primario: canal condicionado.** Alerta si los casos de T superan f × P75 del mes objetivo, solo sin exceso en T. f se elige en `threshold_selection` (máximo F1 de inicio sobre la grilla 0 a 1,5 en pasos de 0,05; en empate, f mayor) y queda congelado.
- **Referencias:** canal estándar (f = 1), persistencia y prevalencia de entrenamiento.
- **Controles negativos:** ranking aleatorio al mismo presupuesto, alertar todo y canal inflado con tantas alertas aleatorias como las del canal.

## Punto de operación (§9)
Presupuesto predeclarado: en cada mes de origen el candidato emite tantas alertas como el canal condicionado, un número conocido en T. También se reportan el umbral congelado de la fábrica y sus métricas.

## Métricas y regla de éxito (§10-§12)
- Sensibilidad de inicio S = TP / I y carga B = 100 × (A − TP) / N, más las complementarias.
- Intervalo del 95 % con 2.000 réplicas, semilla 42, bloques por mes objetivo y emparejado.
- **CUMPLE** si ΔS ≥ 10 pp en la estimación puntual y en la cota inferior, ΔB ≤ 5 en la puntual y en la cota superior, se supera a persistencia y ningún control negativo cumple. En los demás casos el veredicto es `NO_CUMPLE_POR_EFECTO`, `PRECISION_INSUFICIENTE`, `NO_EVALUABLE` o `INVALIDO`, por horizonte.
- Se reportan también la heterogeneidad por departamento y AP, AUROC y Brier sobre inicios.

## Determinismo (§13)
El candidato es determinista (`LogisticRegression` lbfgs sin muestreo). Se acredita con dos ejecuciones aisladas que deben dar la misma huella del modelo y las mismas métricas.

## Evidencia previa y límites
En el retroanálisis de la tanda 10 (ventana expansiva, fuera del contrato), la logística detectó 301 inicios frente a 280 del canal en T+1 y 217 frente a 179 en T+2. Eso equivale a unos 4 pp en T+1, así que se espera `NO_CUMPLE_POR_EFECTO` en T+1 con la regla de 10 pp. La ventaja se concentra en brotes pequeños o de un solo mes. Un resultado favorable no selecciona campeón ni autoriza uso operativo.
