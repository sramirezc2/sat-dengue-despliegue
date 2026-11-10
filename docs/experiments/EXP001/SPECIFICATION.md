# EXP001 — fixture técnico de aceptación T17

Tipo: `synthetic_fixture`. Hipótesis: EXP001-H0.
Autorización: el pedido T17 autoriza explícitamente dos fixtures pequeños.
No es un experimento científico real ni una comparación de rendimiento generalizable.

## Protocolo congelado

Cinco fuentes generadas por `experiment_management.synthetic.acceptance_bundle`.
Dos municipios ficticios, datos hasta 2024 y tres centinelas 2025 en cuarentena.
Reconstrucción canónica por contenido; cinco roles con soporte previo a fit.
Horizontes [1, 2], semilla 53, XGBoost CPU/hist v1, 4 rondas.
Configuración completa en `pipeline/conf/experiments/EXP001.yml`, vinculada por SHA-256
al registro. Se congelan calibración y umbral antes de leer evaluación.
Métricas AP/AUROC/Brier/sensibilidad/FAR/volumen y dos referencias sobre las mismas filas.

## Criterio y límites

Éxito técnico: recibo COMPLETED, inventario íntegro, decisiones congeladas y
coexistencia de evidencia exclusiva. FAR sintético máximo 1.0 es solo fixture.
No hay HPO, nuevas familias, G, presupuesto, campeón ni autorización operativa.
Los 33 predictores se certifican como entrada; el adaptador usa el subconjunto
modelado declarado, conservando los contratos de preparación existentes.
Las conclusiones deben enlazar los resultados agregados, incluso si son negativos.
