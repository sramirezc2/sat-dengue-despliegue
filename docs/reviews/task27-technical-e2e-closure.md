# T27 — cierre documental de la aceptación E2E real

**Aceptación técnica y cierre documental: PASS. T27: BLOQUEADA, 26/27.**
Revisión del 9 de noviembre de 2026 sobre `e8fae62`, rama
`feature/pipeline-e2e`, inicialmente limpia. La autoridad de estado es
[plan.md](../../plan.md). Este cierre verifica evidencia conservada; no ejecuta
adquisición, construcción canónica, entrenamiento ni certificación N=3.

La corrida `ACCEPTV3REAL01`, ejecución `b0a09b94fa9e45ccafed0f4d568ef82f`,
usó código `24ac37d84b2343ea725318b09bd563b0268c88a7` en checkout temporal.
El [recibo de aceptación](../evidence/task27/technical-e2e-24ac37d-24q4bmiu.json)
conserva resultados, receta y terminales; solo se añaden unidades de recuento,
horas de ejecución y referencia a este cierre. El
[recibo de conciliación](../evidence/task27/technical-e2e-documentary-closure.json)
registra los hashes de las fuentes auditadas, controles y límites. El original
anterior a la aclaración permanece en Git y en el archivo local ignorado.

## Recuento conciliado

La frase «42 registros métricos» contaba filas devueltas por `compare`, una por
**horizonte × método × nombre de métrica**, incluyendo valores nulos. Son dos
horizontes, tres métodos (`candidate`, `persistence`, `train_prevalence`) y siete
nombres de métrica. No cuenta 42 métricas distintas ni 42 valores numéricos.

| Método | Filas agregadas, ambos horizontes | Valores numéricos | Valores nulos |
|---|---:|---:|---:|
| Candidato | 14 | 14 | 0 |
| Persistencia | 14 | 10 | 4 |
| Prevalencia de entrenamiento | 14 | 6 | 8 |
| Total | **42** | **30** | **12** |

Los nulos conservan sus motivos: `NOT_PROBABILISTIC` (2 Brier de persistencia),
`NO_ALERTS` (2 FAR de persistencia) y `NO_DECISION_POLICY` (8 métricas de decisión
de prevalencia). Los ceros numéricos sí se registran en MLflow.

| Run MLflow | Función | Filas en `metrics` | Filas en `latest_metrics` |
|---|---|---:|---:|
| `5353ed24d39044c18e2398ffd71f4fed` | Padre, ambos horizontes | 30 | 30 |
| `868e0cf797994343866542d1380c41d5` | Hijo T+1 | 15 | 15 |
| `b46a4ef9fa914ee3b50f71bfaf72b58f` | Hijo T+2 | 15 | 15 |
| Total | | **60** | **60** |

Son **60 registros numéricos de MLflow para 30 valores agregados**: el padre
repite los valores de sus hijos. No son 60 resultados independientes. Ambas
tablas son vistas del mismo tracking y sus totales no se suman entre sí.
Cada run tiene una sola observación por clave. Hay 45 cadenas de clave distintas
entre runs: 30 con prefijo de horizonte en el padre y 15 sin ese prefijo,
compartidas por los hijos. Solo hay siete nombres de métrica.

Se consultaron los dos SQLite con `mode=ro` y `PRAGMA quick_check` = `ok`;
las tablas `metrics`, `latest_metrics`, `runs` y `tags` coinciden por filas.
La copia archivada se creó con `sqlite3.Connection.backup`: sus bytes difieren
del store original; esa diferencia no afecta los registros consultados. Ambos
archivos permanecieron intactos durante esta revisión. Todos los valores
registrados coinciden exactamente con los agregados conservados, y las tres
corridas están FINISHED con tag COMPLETED y parentesco/horizonte correctos.

La consulta de recuento usada para cada tabla, restringida a los tres IDs, es:

```sql
SELECT run_uuid, COUNT(*), COUNT(DISTINCT key)
FROM metrics
WHERE run_uuid IN (
  '5353ed24d39044c18e2398ffd71f4fed',
  '868e0cf797994343866542d1380c41d5',
  'b46a4ef9fa914ee3b50f71bfaf72b58f'
)
GROUP BY run_uuid;
```

La misma consulta sobre `latest_metrics` produce 30/15/15. Las 42 filas de
`compare` se cotejaron contra el CLI archivado y `metrics.json`. Por eso se
conserva `metric_rows_queryable: 42`, ahora con unidad explícita en el recibo.

## Ejecución temporal, identidad y etapas

El recibo generado por la ejecución registra inicio
`2026-11-10T02:22:21.813922+00:00` y fin
`2026-11-10T02:29:08.216919+00:00`: 9 de noviembre, 21:22:21–21:29:08 en Bogotá.
`at_utc: 2026-11-10T02:30:38.862437+00:00` identifica la creación del informe.
Los 409,58 s corresponden al comando completo medido externamente; los 406,5 s
son los reportados por Kedro. El pico de 13.046.136.832 bytes es RSS del proceso,
no memoria total de la máquina ni un mínimo universal.

La adquisición de cinco crudos y la construcción nueva fueron parte de aquella
corrida exitosa. Ahora se verifican sus recibos, linaje y artefacto conservados,
sin repetir esas etapas ni acceder a credenciales o servicios remotos.

| Identidad | Valor verificado |
|---|---|
| SHA-256 de bytes del canónico consumido | `b4562ba50def7a98dceede0b7e95feed0e799b4652939d8037f1604bef37a23d` |
| Digest semántico del canónico | `de49b11bad43c35983a098ead2faa149d4e744da4172432aecdaadd828c73158` |
| SHA-256 del certificado N=3 | `5c1d2adc0a7967be9ee5e3398b5541cf74963ed6f6b4ee94e6f4a4838a77a966` |
| SHA-256 de bytes del manifiesto | `846c72ecd2e641373d55b40e7a8e2b790ea02239b44cff08e412990bcdb404fe` |
| Digest normalizado del manifiesto | `1b2a28a4c90d3225272c2103b27d3cef1bfb69f3a6aeb9470e4177fd3798ed01` |

La relectura del archivo canónico verifica bytes, semántica y 242.352 filas,
1.122 municipios, 2007-01–2024-12. Auditoría completa, perfil, lockfile y ambos
hashes coinciden con el [certificado versionado](../evidence/task27/canonical-full-93ac27fd-certification.json).
El constructor certificado es `9e06a519d20de5b86cf3f07f0420175cf5644fff`;
el código de aceptación es `24ac37d`. No se exige igualdad de commits ni se
presenta esta corrida única como una repetición N=3. Los nulos del canónico
certificado se conservan.

Los cinco roles por horizonte se definen por objetivo:

| Rol | Periodo objetivo, T+1 y T+2 |
|---|---|
| Entrenamiento | 2018-01–2020-12 |
| Ajuste de calibración | 2021-05–2021-10 |
| Selección de calibración | 2022-03–2022-08 |
| Selección de umbral | 2023-01–2023-06 |
| Evaluación | 2024-01–2024-11 |

Los diez soportes coinciden con configuración y validación, con ambas clases y
conteos reconciliados. Cada transición respeta disponibilidad más embargo antes
del primer origen consumidor. La disponibilidad máxima de evaluación es 2024-12;
sus primeros orígenes son 2023-12 (T+1) y 2023-11 (T+2). Hay cero observaciones
desde 2025 en el canónico; la cuarentena reconcilia entrada, retenidos, reservados
y fechas inválidas antes de productores.

El código y la evidencia registran soporte previo a cualquier fit, un ajuste
independiente por horizonte, calibración/umbral, ambas predicciones congeladas
y después lectura de etiquetas de evaluación. Los agregados no son una traza
horaria por etapa ni prueban disponibilidad histórica en tiempo real.
El terminal COMPLETED, inventario de cinco artefactos más inventario final,
firma de linaje y hashes de las seis copias archivadas pasan verificación.
Esto respalda las etapas PASS del recibo hasta evaluación, registro de evidencia
y cierre de MLflow. No hubo publicación hacia `datos/resultados/`.

## Alcance científico y pendientes

**Revisión documental post-run: APPROVED_WITH_LIMITATIONS**, restringida a
aceptación técnica. No sustituye la aprobación independiente final.
La autorización humana permitió una receta y aprobación temporales para ejercer
`experiment_run`. El enum `experiment_type: scientific`, exigido por el esquema
para raw, no es aprobación científica del equipo.

Se conservan XGBoost/v1, semilla 53, cuatro rondas, 33 predictores, mínimos de
fixture y FAR máxima 1.0. Sensibilidad 1.0, umbral 0.0 y fracción de alertas 1.0
dependen de esa receta permisiva; no acreditan utilidad científica, superioridad
frente a T16, presupuesto de alertas, campeón ni autorización operativa.
No se recalculan resultados predictivos ni se completan comparadores o
incertidumbre ausentes. 2025 sigue siendo evidencia previamente utilizada,
fuera del desarrollo y sin carácter de holdout intacto.

El recibo de ejecución sigue COMPLETED; el registro temporal permanece
RUNNING/PENDING y el oficial solo contiene EXP001/EXP002. No se crean conclusiones
científicas ni transiciones de registro. El preflight separado bloqueado por
credencial ausente permanece intacto; no invalida ni constituye un reintento
de esta ejecución. Los diagnósticos ambientales previos también se conservan.

Para cerrar T27 faltan publicación normal autorizada y actualización de la
descripción del único PR #1, siete checks obligatorios del HEAD final, aprobación
independiente y auditoría final de merge de esa revisión. Este commit es local;
no se hace push, merge ni cambio de ruleset.

## Validación proporcional

PASS: JSON versionado; inventario/firma; correspondencia exacta de valores con
MLflow; control de preservación normal y `-O` (49 archivos, 22 JSON, 16 recibos
históricos e identidad N=3 T16); snapshot extendido de 92 archivos; registro
oficial VALID; enlaces locales de los Markdown modificados y referencias de los
JSON de cierre; `git diff --check` local, staged y contra `origin/main`.
EXP001/EXP002 y el certificado completo N=3 permanecen idénticos a la base.

```sh
uv run --locked --directory pipeline python tools/check_experiment_preservation.py
uv run --locked --directory pipeline python -O tools/check_experiment_preservation.py
uv run --locked --directory pipeline python -m sat_dengue_pipeline.experiment_management validate
git diff --check
git diff --cached --check
git diff --check origin/main...HEAD
```

No se repiten suites de API/tablero, suites completas delegadas a GitHub ni CI
remota: cierre documental sin cambios de comportamiento, según T27/DEC-030.
La evidencia histórica conserva avisos de OmegaConf, deprecación de `--pipeline`
y diferencia de `VIRTUAL_ENV`; no son defectos nuevos ni resultados científicos.
Los archivos grandes, SQLite, receta temporal y evidencia completa siguen solo
en el archivo local ignorado indicado por el recibo de aceptación.
