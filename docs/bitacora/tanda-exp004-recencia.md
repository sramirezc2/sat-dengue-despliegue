# Tanda EXP004 — preinscripción de recencia a 36 meses

Fecha inicial: 11 de noviembre de 2026. Estado: **PROPOSED**.
Revisión R2: 12 de noviembre de 2026.
En revisión humana de la propuesta se solicitó añadir la lectura secundaria T+2
antes de aprobar y congelar. No se han ejecutado EXP004 ni el retroanálisis;
esta enmienda precede a cualquier resultado. La versión anterior queda en Git.
Esta preinscripción se conserva sin cambios después de observar resultados.
Los resultados y decisiones se añadirán en `tanda-exp004-resultados.md`.

**Hipótesis.** Dar más peso a la historia reciente mejora la anticipación de
nuevos inicios frente al mismo modelo con pesos uniformes. Se formaliza una
hipótesis explorada informalmente en la tanda 10; no se presenta como descubrimiento
nuevo o confirmación independiente.

**Qué se correrá.** EXP004 registrado por la interfaz de la fábrica, una sola
vez tras aprobación humana. Dos logísticas climáticas idénticas a la referencia
versionada `conf/retroanalisis/noche/log_conclima.yml`: `uniform_history` y
`recent_history_36m`. Único cambio: peso crudo `2 ** (-age_months / 36)` donde la
edad se mide por objetivo respecto al último objetivo efectivo de train del fold;
media de pesos normalizada a 1. Solo se pondera el ajuste del modelo. No se
eliminan años antiguos ni se prueban otras vidas medias o hiperparámetros.

**Población y periodos.** Meta y Tolima, release corregido `satd-raw-173d5856`,
canónico `operational_full` certificado. Siete cortes de fábrica por año objetivo
2018–2024; train desde 2012-03, con cinco roles separados. Evaluación de enero
a noviembre en cada corte. `primary` incluye T+1 y T+2 sin exceso observado en T;
`secondary_t2` incluye ambos estados conocidos en T para modelo y comparadores,
sin usar T+1 como compuerta. Conserva el evento no exceso en T+1 → exceso en T+2,
leído solo después de predecir. T+1 primario, T+2 primario y T+2 secundario se
reportan por separado, sin mezclar cohortes o votos ni rescatar T+1.
Semillas 7, 13, 31, 53 y 101, todas conservadas. Exclusión completa de 2025.

**Qué decide la hipótesis.** Diferencia emparejada de sensibilidad recent−uniform
con IC95 % por mes objetivo (2.000 réplicas, semilla 42), por lectura, corte y agregado de
los siete cortes, sin sumar semillas. Evidencia a favor en T+1 requiere diferencia
positiva y cota inferior >0 en las cinco semillas, soporte suficiente y mayoría
estricta de cortes utilizables con diferencia positiva (al menos tres cortes).
Los intervalos que incluyan cero, empates, signos contrarios y falta de soporte
se reportan; la decisión científica final corresponde al equipo.

**Qué decide el proyecto.** Independientemente de la pregunta anterior, cada
brazo se compara con el canal condicionado bajo contrato 1.0.0 APROBADO:
ganancia ≥10 pp y cota inferior ≥10 pp, carga y cota superior ≤5 falsas por 100
municipio-mes, A/C primaria (B degenerada explícita) y **A/B/C obligatorias en
secundaria T+2**, presupuesto proxy del 10 %,
soportes, controles negativos y demás condiciones. Los 5 pp históricos no
sustituyen esa regla. En secundaria, B exige más inicios que persistencia
C1 = exceso observado en T sobre el mismo soporte. Si persistencia no alerta,
B es NO_EVALUABLE con NO_PERSISTENCE_ALERTS y no acredita éxito. La lectura
secundaria no sustituye a la primaria ni se elige la favorable después de medir.
La evidencia consumida no se vuelve confirmatoria.

**Control adicional.** Un retroanálisis mensual 2018–2024 con las dos recetas y
cinco semillas en una sola corrida, configuración `conf/exp004`, salida exclusiva
`pipeline/data/retroanalisis/EXP004/run1/`. Se conservarán seis CSV y se verificará
igualdad de claves y etiquetas mediante digests por horizonte/semilla/fold en
`conjunto.csv`; una diferencia o un fold omitido detiene la corrida. Este
instrumento descriptivo conserva su cohorte vigente y no reemplaza la lectura
secundaria ni el veredicto contractual de la fábrica.

**Protocolo completo.** [SPECIFICATION.md](../experiments/EXP004/SPECIFICATION.md).
Sin aprobación humana de receta no se entrena. Sin decisión científica humana
no se cierra el registro, ni se decide campeón o autorización operativa.
