# Prioridades retrospectivas de 2025

Estado: A–E APROBADAS por el equipo SAT DENGUE, comunicadas explícitamente por
el usuario en esta conversación. Registro: 2026-11-13. No se inventan integrantes
ni un acta externa. Base autorizada: `a9c2c1abac386053b2e78f072bdb44e0141f4045`.
Rama exclusiva: `feature/dashboard-2025-risk-ranking`.

## Decisiones cerradas

- **A.** Única receta: `pipeline/conf/retroanalisis/noche/log_conclima.yml` de la
  base autorizada; SHA-256
  `7d67f0595cfdd990e331682ae581d4f49d1f74f83a107f4d9474540412443ec8`.
  Procedencia del archivo: `41a625e6ca7b77e6e47a793d4ed3c0bcc5d15656`.
  `logistic_onset/v1`, scikit-learn 1.7.2, semilla 53, C=1, max_iter=5000;
  33 predictores/36 columnas internas, one-hot fijo, log1p declarado y escalado
  solo en train, sin imputación ni G. No modificar la receta ni elegir otra.
  Se autoriza materializar un artefacto final nuevo, no un experimento.
- **B.** Objetivos de aprendizaje 2012-01–2024-09, disponibilidad máxima 2024-10,
  estrictamente anterior al primer origen 2024-11 (demora declarada: un mes).
  T+2 usa orígenes 2024-11–2025-10 y objetivos 2025-01–2025-12. No objetivos 2026.
- **C.** Entrenamiento local Meta/Tolima, sin entrenamiento nacional. Elegibilidad:
  estado conocido sin exceso en T y predictores requeridos completos. No consultar
  T+1 para decidir T+2. Ausencias e ineligibilidad explícitas, sin reducir el
  universo territorial. La receta es autoridad de preparación: no agregar filtros
  de bloques exploratorios no declarados. Las etiquetas de entrenamiento son
  exclusivamente anteriores al corte y maduras; inferencia no construye etiquetas.
- **D.** Universo 76 (29 Meta, 47 Tolima). Un ranking global entre elegibles;
  `risk_rank=null` para ineligibles. Exactamente ocho por mes/horizonte, sin reparto
  departamental. Score descendente y DIVIPOLA ascendente; filtros sin renumeración
  ni reposición. Menos de ocho elegibles detiene la publicación completa.
- **E.** Configuración seleccionada para informe, reproducción histórica de
  prioridades 2025 aprobada, operación sanitaria NO autorizada y champion
  NOT_SELECTED. T+2 principal del producto; no reclasifica la prioridad científica
  T+1 del contrato propuesto ni aprueba globalmente ese contrato.

## Alcance y límites

Es inferencia retrospectiva con fuentes consolidadas: fechas de evento y clima
hasta T no demuestran disponibilidad de las versiones originales en tiempo real.
No es holdout intacto, confirmación independiente ni reproducción exacta del
retroanálisis mensual. El ajuste único es una adaptación aprobada para publicación.
La primera entrega publica T+2; T+1 solo podrá mostrarse con su propio artefacto
autorizado, nunca mediante resultados históricos de otro modelo.

Se conservan intactos receta, registro experimental, evidencias y los 22 JSON.
Digest del mapa ordenado ruta→SHA-256 (JSON compacto con claves ordenadas):
`4d3ddd3890a6a622b658fc2b1ef0159d0da6bc855cacc2c5b62854290623e16e`.
Los nuevos paquetes viven bajo `datos/resultados/risk-ranking/<edition>/`;
artefactos y recibos operacionales bajo `pipeline/data/risk-2025/`, fuera de Git.

La autorización sustituye para este alcance la rama histórica de AGENTS.md.
Sin push, PR, merge ni cambios remotos. Mientras EXP006 siga activo: únicamente
implementación, fixtures y pruebas focalizadas; descargas, materialización real,
N=3, suites completas, builds y E2E intensivos requieren confirmación posterior.

Operación y contrato ejecutable: [guía de prioridades](../operations/risk-2025.md).
