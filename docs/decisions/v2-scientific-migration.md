# Migración de reglas históricas de V2

V3 es la fuente de verdad futura. La fuente histórica, de solo lectura, es
`j-mauro-r/SAT-Dengue-V2`, referencia `origin/main`, commit
`916a69f3bb73f2ffbb0ec038b8bef887ee91adf1`. Los blobs se consultaron con
`git show COMMIT:ruta`, independientemente del árbol de trabajo de V2.

## Fuentes y huellas

SHA-256 de los bytes del commit, también versionados en
[`canonical_receipt.json`](../../pipeline/tests/fixtures/canonical_receipt.json):

| Archivo en V2 | SHA-256 |
|---|---|
| `src/sat_dengue/canonical/table.py` | `b452868bccccf5eda5601203d252aaea05d6344eca9a0776e299ce47f8f6e7c1` |
| `src/sat_dengue/data/consolidation.py` | `3e750fd1a95de947afb417021b77c3753f3be2b538a4a5ef6f7fe33894ca9cad` |
| `src/sat_dengue/experiments/onset.py` | `48a186010eba73b61acf4f56766cbe8b9c48ce1e6118d6c9b6985eb038d57285` |
| `src/sat_dengue/training_preparation/contract.py` | `388df770a511aa61239ec65ee904a0a39b8d0db81cb61e2b94bc8c60c17ac08e` |
| `src/sat_dengue/training_preparation/validation.py` | `623b88797eed4352d70640c07a91bd81d44972438209f164afad5d0142901963` |
| `tests/unit/test_canonical_model_table.py` | `83eb0f45a073ffd0c08731cf2210fba9f801c73dca97c5d2f4ced9f5008d6aed` |
| `tests/unit/test_training_preparation.py` | `19b09fd002485a8c652d23346911dd2208e5e7c06ad0ea9d2996cdffc9d465e7` |
| `tests/unit/test_training_temporal.py` | `9b24470378b9cba4525581212c7aa326b16ca4a14bc10c5c042adcdcfb070c8d` |
| `pyproject.toml` (versiones numéricas) | `64243055f4a06e97b2f372232f86a1d4af6da668b2e99ce105960dd34e08bdd1` |

## Tarea 6: reglas adoptadas

- De `consolidation.py`: `add_months`, `percentile_type7`,
  `history_periods_for_target`, `classify_endemic_zone` y el cálculo tabular de
  `compute_current_endemic_channel`. Se conserva el percentil Hyndman–Fan 7,
  exactamente los cinco años anteriores del mismo mes, y las fronteras de zonas:
  EXITO `< p25`, SEGURIDAD `p25 <= c <= p50`, ALERTA `p50 < c <= p75`,
  EXCESO `c > p75`. El canal requiere observación contemporánea e historia completa.
- De `canonical/table.py`: contrato de `validate_source`, `build_table`, roles,
  `predictor_matrix` y `coverage_report`. Se conservan orden, tipos, ausencias,
  conteos reconciliados, clima completo por días válidos, rezagos calendario
  1/2/3/12 y umbrales H5 de T+1/T+2 disponibles al origen. No se rellenan huecos.

Adaptaciones de ingeniería: funciones pequeñas en `domain/`, excepciones
`ValueError`, validación explícita de tipos/valores no finitos y colisiones de
columnas, y comprobación de roles cerrados contra manipulación. Son rechazos de
entradas inválidas, sin cambios conceptuales en los resultados válidos. El canal
solo devuelve la tabla; se excluyen trazas y resúmenes históricos no utilizados.
El adaptador `canonical_from_bundle` consume únicamente el archivo local lógico
`panel`, verifica tamaño/hash y cobertura, y conserva códigos DANE como cadenas.
El CSV de entrada ya es mensual; aquí no se implementa agregación diaria ni una
ingesta nacional. Los mensajes históricos del reporte de cobertura se conservan
para paridad y no certifican disponibilidad nacional.

No se migran persistencia, modelos, tracking, experimentos, notebooks, publicación
ni políticas de partición. El perfil de predictores es el canónico de V2; no se
importa otro perfil histórico de entrenamiento ni la reserva de estrés de 2024.
Las etiquetas y controles se implementan separadamente en la tarea 7.

## Tarea 7: inicio y frontera temporal

De `experiments/onset.py` se adoptan `operational_eligibility` y la semántica
de `labels`: inicio es anterior al objetivo `0` y objetivo `1`; si falta uno,
la etiqueta es ausente. Ambas búsquedas son de meses calendario exactos. Ambos
horizontes exigen no exceso observado en T para elegibilidad. T+2 conserva
`earlier_onset_t1`; un episodio que inicia en T+1 y continúa en T+2 produce un
negativo T+2, con esa marca explícita. El exceso observado se deriva de la zona
contemporánea validada; una zona desconocida permanece desconocida.

Se adopta la disponibilidad relativa de `predictor_projection`, junto con la
allowlist canónica cerrada y roles no solapados de la tarea 6. Los umbrales
`p25_h5_t*`/`p75_h5_t*` usan solo historia al origen y están permitidos;
`p75_t*`, estados/conteos futuros, etiquetas y controles no son predictores.
Los offsets conceptuales se comprueban explícitamente; no certifican latencia
operativa de registros o clima del futuro release. Se conservan como no probadas
las condiciones de disponibilidad histórica operativa.

De `training_preparation/contract.py` y `validation.py` se adoptan los principios
de roles exclusivos, calendario objetivo, binariedad y coherencia entre etiqueta
y evaluabilidad. Los metadatos recibidos se verifican contra el inicio calculado,
sin reutilizar ciegamente etiquetas de otro perfil. La evaluabilidad de inicio
requiere dos estados observados; no se adopta la equivalencia histórica entre
disponibilidad de un único `p75_t*` y evaluabilidad. Se permiten huecos para
representarlos como ausencias, en vez de imponer el soporte mensual completo del
perfil histórico de preparación. Ningún hueco se trata como contiguo.

Adaptaciones V3: selección explícita de orígenes separada de la tabla de
observaciones; nombres `target_period_t*`/`y_t*`; estados de ausencia explícitos;
compuerta anterior a cualquier lectura de etiquetas; y X/y/claves separados en
`PreparedSet`. El conjunto utilizable combina elegibilidad al origen, X completo
y etiqueta evaluable, sin modificar la elegibilidad operativa. La auditoría
contabiliza cada condición separadamente.

`TemporalPolicy.reserved_start` empieza en `2025-01` y puede adelantarse para
reservar una ventana adicional; no puede retrasarse y habilitar 2025 consumido.
Rechaza cualquier observación/origen reservado y cualquier objetivo que cruce el
límite. Octubre de 2024 T+2 puede evaluar diciembre; noviembre T+2 y diciembre
T+1 se rechazan antes de consultar etiquetas. No se importan la reserva rígida de
2024 ni las particiones experimentales de V2. `select_origins` solo selecciona
una ventana fija por objetivo y, opcionalmente, impide cruzar el rol anterior con
el origen (principio de embargo de `partitions`); no construye rolling-origin.

El grafo `pipelines/preparation` tiene compuerta y preparación, se prueba con
`MemoryDataset` y no se registra para operación ni supone un release real.
Los centinelas usan únicamente claves artificiales y marcadores, nunca datos ni
etiquetas científicas de 2025: fallan ante lectura de una etiqueta reservada y
comprueban cero invocaciones al consumidor posterior y a la construcción de
etiquetas. La preparación directa repite la protección. Las etapas futuras
deberán consumir esta frontera; aquí no se implementan modelos ni ajustes.

La referencia adicional `onset_expected.json` ejecuta las definiciones puras V2
en siete estados artificiales hasta junio de 2024 y compara ambos horizontes
exactamente, incluidos tipos y ausencias. Su recibo `onset_receipt.json` registra
commit/fuente/método, entrada SHA-256
`d8a563eb35d55de6f33c8d5bc57be7130862143cd3f909a2cd6f6f578a99a1d5`
y salida SHA-256
`b047dd7ed8ed259beaf1238851fc5f4bad21519d49ed02e2c36823f1ccff2550`.
El mismo generador optativo verifica ambas referencias; los tests normales no
necesitan V2.

## Referencia de ingeniería

La muestra construida en `canonical_fixture.py` contiene 167 filas artificiales,
2018–2024, dos municipios ficticios de Meta/Tolima (`50998`, `73998`), ceros,
ausencias fuera de cobertura, un mes faltante y clima incompleto. No contiene
observaciones de 2025. No procede de datos reales ni de filas de V2.

El generador optativo ejecuta mediante AST solo las definiciones puras necesarias
de los blobs fijados, sin imports de V2, persistencia ni lectura de sus datos.
La referencia se generó antes de implementar el productor V3. Reproducción:

```sh
uv run --directory pipeline python tools/generate_v2_reference.py \
  --v2 /ruta/local/SAT-Dengue-V2 --verify
```

NumPy `2.5.4` y pandas `3.0.6` coinciden con V2 y están fijados en `uv.lock`.
Entrada canónica SHA-256:
`047b39ba90f102f3549f82a52bdf6e06dd8bd3892efe5a8896c0c9cd7bfd206d`.
Salida canónica SHA-256:
`b5593b161ac9187602b4e8b4aee6464b43c4f465408ef3fb65f0709c1e61fac5`.
La serialización registra nombres, orden, tipos, valores y nulos; incluye tabla,
esquema/roles, X y cobertura. La comparación es exacta, sin tolerancias numéricas.

Las pruebas normales cargan solo esta referencia local y bloquean acceso a V2,
red, imports inversos y resultados publicados. V2 no es dependencia de ejecución.
No se leyó, copió, movió ni utilizó el CSV local de aproximadamente 426 MB; tampoco
se descargaron datos científicos reales. No se realizó ninguna escritura en V2.
Durante el trabajo su estado Git mostró cambios externos adicionales respecto al
inventario inicial; no se restauraron ni sobrescribieron. Por ello no se afirma
que ese árbol permaneciera idéntico: la procedencia comprobable son los blobs
inmutables del commit fijado, cuyas huellas se verificaron nuevamente.
Al control posterior, el árbol V2 estaba limpio con HEAD externo
`e5fc87ae79efa87e8526643626ecb494d1dcbb76`; `origin/main` seguía en el commit
autorizado. Esta implementación no creó ese commit ni cambió referencias V2.
Esta evidencia demuestra paridad sintética de ingeniería;
**no demuestra equivalencia científica ni reproducción con datos reales**.
La validación con un release público permanece pendiente en la tarea 15.
