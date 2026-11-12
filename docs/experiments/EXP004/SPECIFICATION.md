# EXP004 — Historia reciente frente a pesos uniformes

Estado de preparación: **PROPOSED**, revisión R2 previa a aprobación,
12 de noviembre de 2026 (propuesta inicial: 11 de noviembre).
La persona solicitó añadir `secondary_t2` antes de
congelar la receta; no se han ejecutado EXP004 ni su retroanálisis. La propuesta
anterior y su recibo se conservan en Git y PREPARATION_VALIDATION.json.
Autoridad científica: equipo SAT DENGUE. La receta requiere aprobación humana
explícita; esta preinscripción no concede aprobación ni autoriza entrenamiento.

## Hipótesis y antecedente

Dar más peso a la historia reciente mejora la anticipación de nuevos inicios de
exceso de dengue frente al mismo modelo entrenado con pesos uniformes.

Es la formalización de una hipótesis explorada informalmente, **no un
descubrimiento nuevo ni una evaluación confirmatoria independiente**. La tanda
10 ya probó dar más peso a años recientes sin mejora relevante; 2018–2024 ha
intervenido en el desarrollo. EXP001/EXP002 son fixtures de ingeniería y no
son referencias científicas. No se usa ni se modifica EXP003.

Referencia ejecutable vigente: `pipeline/conf/retroanalisis/noche/log_conclima.yml`.
Se copian literalmente sus predictores, disponibilidad, preparación y candidato:
33 predictores (nueve climáticos), zona one-hot fija (36 columnas), log1p de
conteos/umbrales declarados y estandarización aprendida en train sin pesos.
`LogisticRegression`, scikit-learn 1.7.2, L2, C=1, max_iter=5000, solver lbfgs
según el adaptador v1. Sin balance de clases, HPO, early stopping, refit, búsqueda
de vidas medias, transferencia de estado, aprendizaje en línea o elección de semilla.

## Dos brazos y único cambio

| Brazo | Peso de ajuste |
|---|---|
| `uniform_history` | 1 para todas las filas de train |
| `recent_history_36m` | Recencia exponencial con vida media fija de 36 meses |

```text
reference_target = max(periodo objetivo del train efectivo y disponible del fold)
age_months = meses calendario entre periodo objetivo de la fila y reference_target
raw_weight = 2 ** (-age_months / 36)
sample_weight = raw_weight / mean(raw_weight dentro del train del fold)
```

El peso **crudo** más reciente es 1; el peso normalizado aplicado puede superar
1. Todos son positivos. No se retiran observaciones antiguas. La referencia se
obtiene exclusivamente del train efectivo ya autorizado por madurez, nunca de
calibración, umbral, evaluación o del extremo del panel completo.

Solo `LogisticRegression.fit` recibe `sample_weight`. Transformación, escalado,
prevalencia, calibración, selección de representación/umbral y evaluación no se
ponderan. Los resúmenes y el digest conjunto claves/pesos quedan en el linaje y
recibo; no se guardan pesos por fila ni modelos en Git o MLflow.

Ambos brazos comparten release, canónico certificado, predictores y orden,
preparación, filas, claves, etiquetas, horizontes, cinco roles, cortes, semillas,
calibración, grillas, presupuesto y comparadores **dentro de cada lectura**.
Las lecturas primaria y secundaria tienen cohortes propias; no se exige igualdad
entre ellas ni se mezclan sus denominadores. La comparación usa únicamente
la población `common`; como ambos brazos tienen los mismos predictores no se
repiten ajustes redundantes de una población nativa idéntica. Antes del primer
fit se exigen X, claves y etiquetas productoras idénticos. Evaluation.y sigue
diferida; tras predecir se exigen claves y etiquetas de evaluación idénticas.

## Datos, población y tiempo

- Release operacional corregido `satd-raw-173d5856`, revisión HF inmutable
  `173d5856874b89d8aeb0566accc65ce7f6759820`, manifiesto de cinco fuentes fijado.
- Perfil `operational_full`, 2007-01–2024-12, 1.122 municipios, 242.352 claves.
  El pipeline reconstruye y valida contra el certificado N=3 versionado de T27;
  no repite ni modifica la certificación histórica.
- Entrenamiento y evaluación solo en Meta/Tolima (50/73, 76 municipios).
- Lecturas obligatorias de esta receta: `primary` para T+1 y T+2, y
  `secondary_t2` solo para T+2. En primaria se exige estado observado sin exceso
  en T; en secundaria se incluyen ambos estados conocidos en T, con y sin
  exceso, para modelo y comparadores. Cada lectura mantiene su soporte común
  propio. El evento H5 no cambia: inicio T+2 = no exceso en T+1 y exceso en T+2.
  T+1 se consulta solo para el desenlace posterior al freeze y las predicciones;
  nunca selecciona filas, cupo, alertas ni ajuste en T. No se combina T+2 con T+1.
- Ningún origen, objetivo, etiqueta, disponibilidad o transformación de 2025
  participa en aprendizaje, selección, ajuste o evaluación de EXP004.
- Demora de etiqueta: un mes; embargo adicional: un mes en la fábrica. Son
  supuestos retrospectivos, no mediciones de disponibilidad operativa.
- Semillas predeclaradas: **7, 13, 31, 53, 101**, las cinco identidades usadas
  por la evaluación científica de la fábrica (`test_scientific_e2e.py` y
  `test_seed_aggregation.py`). Se ejecutan todas, sin escoger una.

## Cinco roles de la fábrica

Siete cortes independientes por año objetivo Y, **Y=2018,…,2024**. Los intervalos
son por objetivo e inclusivos; ambas lecturas y ambos horizontes usan el mismo
calendario, aplicado sobre la cohorte propia de cada lectura:

| Rol | Ventana objetivo |
|---|---|
| train | 2012-03 a diciembre de Y−4 |
| calibration_fit | mayo a octubre de Y−3 |
| calibration_selection | marzo a agosto de Y−2 |
| threshold_selection | enero a junio de Y−1 |
| evaluation | enero a noviembre de Y |

Los objetivos de evaluación no se solapan. Noviembre es el último mes cuya
etiqueta con demora de un mes puede conocerse dentro de 2024; se conserva la
misma ventana de once meses en todos los cortes. No se incorporan meses después
de observar resultados. La historia anterior a 2012-03 sirve solo para H5/lags.

Train exige al menos 30 ejemplos de cada clase y 20 municipios. Los otros roles
exigen al menos un ejemplo de cada clase y 20 municipios; la receta declara el
número exacto de meses de cada ventana. Son gates de ingeniería, **no sustituyen
los 30 inicios por celda del contrato científico**. Una celda con menos de 30
inicios se reporta sin voto ni conclusión. Un gate productor fallido detiene la
corrida; no se relajan soportes ni se modifica esta receta para continuar.

La calibración vigente de la fábrica es sigmoide sobre probabilidad original,
ajustada solo en calibration_fit; se conserva original si Brier no mejora más
de 1e-12 en calibration_selection. Umbral con grilla 0–1 en pasos de 0,005,
FAR de inicio máxima 0,8 en threshold_selection; empate por menos falsas,
menor FAR y mayor umbral. Se copia la política vigente de la fábrica. No hay refit.

## Comparadores, presupuesto y evaluación del proyecto

Contrato **1.0.0 APROBADO**, con hash fijado en la receta. Presupuesto
predeclarado **10 %** por mes objetivo y departamento, `floor(0.10 × N_emisión)`,
empates por código municipal. Es el presupuesto proxy de referencia de la
bitácora, no capacidad sanitaria medida. El tope común no obliga a rellenar
alertas que no superan el umbral; se informa el volumen realmente emitido.

Canal condicionado: casos de dengue conocidos en T frente a una fracción del
P75 H5 del objetivo; fracciones **0,00–1,50 en pasos de 0,05**. Se selecciona por
F1 en threshold_selection, desempate por menos alertas y mayor fracción.
La prioridad del cupo es exceso absoluto `casos(T) − fracción × P75`, sin
excluir ni priorizar P75=0. No se consulta evaluación para fijar fracción o cupo.

Se conservan C0 histórico sin cupo, persistencia C1, prevalencia y los controles
negativos: ranking aleatorio al mismo presupuesto, alertar todo y canal inflado.
Persistencia primaria es degenerada: B queda NO_EVALUABLE, causa
DEGENERATE_PRIMARY_COHORT, sin atribuir victoria. A/C siguen siendo obligatorias.
En `secondary_t2`, persistencia C1 = exceso observado en T puede ser informativa:
B y la comparación de utilidad con persistencia son **obligatorias**. Se exige
TP_modelo > TP_persistencia sobre las mismas claves. Si no hay alertas de
persistencia en el soporte evaluado, B queda NO_EVALUABLE con causa
NO_PERSISTENCE_ALERTS; esa comparación vacía no acredita éxito ni se elimina
para favorecer el voto. B, su causa, obligatoriedad y base de decisión se
conservan en celdas, cortes, semillas y recibo.

Para contribuir a un resultado afirmativo del proyecto, **cada brazo** debe
satisfacer ganancia de sensibilidad frente al canal condicionado **≥10 pp** y
cota inferior **≥10 pp**; carga adicional de falsas de inicio y cota superior
**≤5 por 100 municipio-mes**, A/C en primaria y A/B/C en secundaria T+2,
soporte, presupuesto, controles negativos y
demás condiciones contractuales. C histórica mantiene margen de FAR de exceso
≤0,05. Se conserva la mayoría estricta de cortes utilizables (mínimo tres) y
unanimidad de las cinco semillas. No se cuentan semillas como nuevos cortes.
Se generan resúmenes separados para T+1 primario, T+2 primario y T+2 secundario,
por brazo y territorio. No se mezclan sus cohortes, votos, intervalos o
veredictos ni se elige a posteriori la lectura más favorable. Se derivan 140
variantes y 210 ajustes: 140 primarios (dos horizontes) y 70 secundarios T+2.
La evidencia exploratoria de EXP004 no cierra afirmativamente la pregunta de
grado; faltan cohorte confirmatoria independiente y N=3 E2E de un finalista.

## Hipótesis de EXP004 e interpretación predeclarada

La pregunta de pesos se responde **frente al mismo modelo uniforme**, separada
del contrato frente al canal. Estimando primario: sensibilidad de inicio de
`recent_history_36m` menos `uniform_history`, en pp, al punto predeclarado, sobre
las mismas claves/etiquetas. Se reportan N, I, TP, alertas, falsas, diferencia
emparejada y su IC95 % por horizonte, **lectura**, semilla, corte, año y territorio.

Se reporta además el agregado de los siete cortes predeclarados con bootstrap
emparejado por mes objetivo, **2.000 réplicas, semilla 42**, sin sumar semillas
como observaciones independientes. Ese agregado no añade votos al proyecto.
La fábrica conserva también AP, AUROC, Brier, FAR y carga con sus denominadores.

Evidencia a favor de la hipótesis primaria requiere diferencia T+1 positiva y
cota inferior >0 en las cinco semillas, soporte suficiente, al menos tres cortes
utilizables y diferencia positiva en mayoría estricta de esos cortes. Se
reportan signos contrarios, empates, intervalos que incluyan cero y celdas no
evaluables; no se ocultan. No se exige la ganancia histórica de 5 pp ni se usa
como regla contractual. La evaluación del proyecto sigue exigiendo 10 pp y su
cota inferior. Ambas lecturas T+2 se informan por separado y **ninguna rescata
T+1 ni sustituye un incumplimiento de la otra lectura**.

El equipo asigna POSITIVE, NEGATIVE o INCONCLUSIVE al revisar la evidencia.
El software y este documento no aprueban conclusiones, campeón o uso operativo.
No se ajustarán vida media, reglas o receta después de observar EXP004.

## Retroanálisis adicional y comandos cerrados

Una sola corrida del pipeline `retroanalisis`, dos recetas de EXP004 y las cinco
semillas. Panel, folds, filas y etiquetas efectivos idénticos por horizonte y
semilla. La vida media y función de pesos son exactamente las de la fábrica.
Cadencia mensual expansiva desde origen 2018-01; objetivos de train desde
2012-03, último objetivo solicitado 2024-12, demora un mes y disponibilidad
estrictamente anterior al origen. El último objetivo efectivo será 2024-11;
no se usan etiquetas disponibles en 2025. Se comprueba el canónico consumido
contra el mismo certificado antes de preparar o entrenar.

El retroanálisis conserva su instrumento vigente: ranking sin calibración ni
umbral probabilístico, canal ajustado/condicionado elegido con el año previo,
mismo volumen realizado por mes y bootstrap municipal descriptivo de 1.000
réplicas. Ambos brazos comparten esas reglas. Es un diagnóstico adicional;
**no sustituye la evaluación científica de la fábrica, no se mezcla con ella ni
se le atribuye un veredicto contractual desde esos CSV**. La lectura secundaria
contractual T+2 y B se evalúan en la fábrica; este retroanálisis conserva su
cohorte vigente y no se presenta como implementación de esa lectura secundaria.

Comandos desde la raíz, solo después de aprobación humana de EXP004:

```sh
uv run --locked --directory pipeline kedro run --pipeline experiment_run --params experiment_id=EXP004
uv run --locked --directory pipeline kedro run --pipeline retroanalisis --env exp004
```

La configuración versionada `pipeline/conf/exp004/parameters_exp004.yml` fija
explícitamente release corregido, perfil canónico, certificado, dos recetas,
cinco semillas, periodos y salida exclusiva `pipeline/data/retroanalisis/EXP004/run1/`.
No se modifican parámetros globales. Se conservan `resumen.csv`, `por_anio.csv`,
`curva.csv`, `omitidos.csv`, `conjunto.csv` y `predicciones.csv`, fuera de Git.
`conjunto.csv` conserva digests de claves/etiquetas train y evaluación y resumen
de pesos por horizonte/semilla/fold. Se relee y falla si difiere cualquier brazo;
un fold omitido también detiene la comparación cerrada. Una carpeta existente
no se sobrescribe. No se relanza un fallo sin diagnóstico y autorización concretos.

## Evidencia, aprobación y preservación

La fábrica guarda evidencia exclusiva en `docs/evidence/experiments/EXP004/`,
trabajo bajo `pipeline/data/experiments/<execution_id>/` y MLflow local existente.
Un único intento aprobado; éxito técnico deja registro RUNNING/PENDING para la
decisión científica humana. No publica ni selecciona campeón.

Se preservan EXP001/EXP002, certificados, bitácora previa, recibos, recetas
históricas y resultados publicados. La preinscripción por tanda solo se ha revisado por solicitud humana antes de
aprobación o resultados. Tras aprobarla es inmutable; los resultados se añadirán
en otro archivo y se enlazarán sin editarla.
Se preparará CONCLUSIONS.md tras las corridas, con decisión humana pendiente.

## Identidades congeladas

| Archivo | SHA-256 |
|---|---|
| `docs/experiments/contrato.md` | `f701ae4a6731d6a40dd0b7e03a3a50f6f07e9b8154d25091b984f91834e6b97b` |
| `pipeline/conf/retroanalisis/noche/log_conclima.yml` | `7d67f0595cfdd990e331682ae581d4f49d1f74f83a107f4d9474540412443ec8` |
| `pipeline/conf/releases/operational-raw-173d5856.json` | `846c72ecd2e641373d55b40e7a8e2b790ea02239b44cff08e412990bcdb404fe` |
| `docs/evidence/task27/canonical-full-93ac27fd-certification.json` | `5c1d2adc0a7967be9ee5e3398b5541cf74963ed6f6b4ee94e6f4a4838a77a966` |
| `pipeline/conf/experiments/EXP004.yml` | `ed55aedb9259ae253863fd97cf255d48b56cba2a15854e4746e666df32e7132f` |
| `pipeline/conf/retroanalisis/EXP004_uniform_history.yml` | `2708be7132badb66ba169df12c96b7af7fa16a957d22d47ddff405e4b789c0c8` |
| `pipeline/conf/retroanalisis/EXP004_recent_history_36m.yml` | `9fe505a6dd721a0177856b3b29eb5fd6531466e527ab4183b77273623d5d348a` |
| `pipeline/conf/exp004/parameters_exp004.yml` | `68272b9c09747cf16a19bcf0b2e8a76a857c8e882ce70e6ccf97e4cf4d4008c2` |
| `docs/bitacora/tanda-exp004-recencia.md` | `0a6a3d9b82121fc8d8742fe7c09ea54c2992a888d65a16594e8808c39977fe95` |
