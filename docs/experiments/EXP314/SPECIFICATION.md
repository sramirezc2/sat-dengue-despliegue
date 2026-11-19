# EXP314 · Logística con clima T+2 para Meta y Tolima

El equipo aprobó un ajuste de `logistic_onset/v1`, exclusivamente para T+2, con la receta versionada [`log_conclima.yml`](../../../pipeline/conf/retroanalisis/noche/log_conclima.yml). Conserva las nueve variables climáticas, la semilla 53, la regularización y el orden de los predictores. La población son los municipios de Meta y Tolima. La fuente es el release privado `satd-raw-173d5856` con el certificado `operational_full` fijado en la configuración.

La hipótesis técnica es que el ajuste, una vez exportado, reproduce las probabilidades brutas de Kedro en la misma matriz de evaluación con tolerancia absoluta de `1e-12`. La fábrica conserva sus diagnósticos frente a la prevalencia de entrenamiento y la persistencia sin inicio en la misma cohorte. Un mes de demora de etiquetas y uno de embargo separan las ventanas por mes objetivo.

| Rol | Meses objetivo |
| --- | --- |
| Ajuste | 2018-01 a 2020-12 |
| Ajuste de calibración | 2021-05 a 2021-10 |
| Selección de calibración | 2022-03 a 2022-08 |
| Selección de umbral | 2023-01 a 2023-07 |
| Evaluación | 2024-01 a 2024-11 |

El control previo verificó las ventanas y el soporte de los productores sin ajustar el estimador ni abrir las etiquetas de evaluación. El aprendizaje termina antes de 2025. El resultado de este protocolo es un artefacto de inferencia sobre predictores preparados y evidencia diagnóstica de la fábrica. Establecer utilidad operativa requeriría verificar también la disponibilidad del clima al cierre de cada mes.
