# Artefactos del modelo

`logistica-conclima-t2/` contiene el modelo final del proyecto: la regresión
logística con variables climáticas, en el horizonte T+2, congelada.

| Archivo | Qué es |
| --- | --- |
| `model.json` | El estado predictivo completo: receta, 33 predictores en orden, 36 columnas de matriz, coeficientes, intercepto, medias y desviaciones del escalado, dtypes, y las huellas del conjunto con el que se ajustó |
| `manifest.json` | Contrato, `sha256` del artefacto y huella del estado efectivo |

## Dos huellas, y cuál identifica al modelo

El artefacto trae dos, y conviene no confundirlas:

- **`effective_state_sha256` es la identidad del modelo.** Resume el estado
  predictivo: coeficientes, intercepto, medias, desviaciones, tipos de entrada y
  parámetros nativos del estimador. Dos ajustes con este valor igual son el mismo
  modelo.
- **`artifact_sha256` es la identidad del sobre.** Es el sha256 de los bytes del
  archivo, que además del estado incluye la **procedencia del código**: commit,
  huella del árbol fuente y del archivo de bloqueo. Cambia con cada commit del
  repositorio, aunque el modelo sea idéntico.

Esto no es teoría. El 19 de noviembre se materializó el modelo en dos máquinas
x86 distintas: las dos dieron `effective_state_sha256`
`d59ce5af5c001352da1aa2e81b9d5d51cef4db0e701de2aaf65d6fbaec64ed2f` —el mismo
modelo— y **dos `artifact_sha256` diferentes**, porque cada una partía de un
commit distinto de la rama.

Por eso, para comprobar que un artefacto es el modelo que describe el informe, lo
que se compara es el estado efectivo y las tres huellas de entrenamiento, no el
sha256 del archivo.

La certificación N=3 del 14 de noviembre ajustó el modelo tres veces en procesos
aislados en una máquina `arm64` y las tres dieron
`artifact_sha256 = 7830c6cbb8d5b4f3bd5798440d1766953bb274ae5723015ff450c384fc9320d3`
y `effective_state_sha256 = 845312c753e2bf312b592bcc1fb48b706220d96203b190fc21c2ffe39eac37ea`
([recibo](../docs/evidence/risk-2025/20261114-r7-final-e1d3946f0f.json)).

## Qué modelo es

Regresión logística con penalización L2, `C = 1`, 5000 iteraciones,
scikit-learn 1.7.2. La receta es
`pipeline/conf/retroanalisis/noche/log_conclima.yml`, SHA-256
`7d67f0595cfdd990e331682ae581d4f49d1f74f83a107f4d9474540412443ec8`, y el
procedimiento es `SATD-RISK-2025-LOG-CLIMATE-v1`.

Recibe los conteos de dengue, de dengue grave y su suma con rezagos de 1, 2, 3 y
12 meses; los percentiles del canal endémico del mes en curso y de los meses
objetivo; la zona del canal; el mes del año; y las nueve variables climáticas del
mes de origen. Los conteos y umbrales entran con `log(1 + x)` y todo se
estandariza con la media y la desviación del entrenamiento.

Se ajustó **una sola vez**, con objetivos entre 2012-01 y 2024-09 y una demora de
etiqueta de un mes, de modo que la última observación disponible es de 2024-10,
anterior al primer origen que se publica. El artefacto registra `fit_calls: 1` y
la carga lo verifica.

## Cómo se usa

La clase que lo carga es `FrozenLogistic`, en
`pipeline/src/sat_dengue_pipeline/risk/frozen.py`. **No expone `fit`**: es
deliberado, para que el servicio no pueda reentrenar por accidente ni caer en un
reentrenamiento como respaldo si falta el archivo.

```python
from pathlib import Path
from sat_dengue_pipeline.risk.frozen import load_artifact

modelo = load_artifact(
    Path("modelos/logistica-conclima-t2"),
    "7830c6cbb8d5b4f3bd5798440d1766953bb274ae5723015ff450c384fc9320d3",
    procedencia,
)
margen = modelo.score(X)
```

`score` devuelve el **margen lineal**, no una probabilidad. Es a propósito: la
calibración no se sostuvo en los años recientes, así que los puntajes se usan
únicamente para ordenar municipios por riesgo dentro de un mismo mes. La
aplicación no publica probabilidades.

`load_artifact` falla antes de calcular nada si cambia la identidad: contrato,
receta, huella de la receta, procedimiento, procedencia, lista de predictores,
columnas de matriz, corte temporal, número de ajustes, versión o parámetros
nativos del estimador, o la huella del estado efectivo.

## Qué reproduce y qué no

El 19 de noviembre se volvió a materializar el modelo en otra máquina, y conviene
dejar escrito lo que se encontró, porque acota lo que el proyecto puede afirmar
sobre su propia reproducibilidad.

**Los datos de entrenamiento reprodujeron exactamente.** Las tres huellas que el
artefacto registra —`training_keys_sha256`, `training_matrix_sha256` y
`training_labels_sha256`— salieron idénticas a las de la certificación, con las
mismas 7 596 filas, el mismo corte en 2024-09 y la misma receta. Lo que entra al
ajuste es bit a bit lo mismo.

**Los coeficientes no.** El estado efectivo dio `d59ce5af…` en lugar de
`845312c7…`. La diferencia entre las corridas es la máquina: el recibo de la
certificación declara `arm64` con Python 3.12.13, y las dos corridas del 19 de
noviembre fueron x86-64. Una regresión logística ajustada con `lbfgs` sobre
implementaciones distintas de BLAS converge a valores que difieren en los
últimos bits.

Que **dos** máquinas x86 independientes hayan llegado al mismo `d59ce5af…` es lo
que permite afirmar que se trata de la arquitectura y no de azar ni de un estado
corrupto: dentro de una familia de máquina el ajuste sí es reproducible.

Conviene no confundir dos cosas que esto deja separadas:

- **El artefacto es portable.** `load_artifact` compara el sha256 de los bytes
  del archivo; no reajusta nada. El `model.json` versionado aquí carga y puntúa
  igual en cualquier máquina, porque puntuar es un producto matriz-vector.
- **El ajuste no es reproducible bit a bit entre arquitecturas.** La
  certificación N=3 demuestra determinismo dentro de una máquina, que es lo que
  protege contra un ajuste accidental o un estado corrupto. No demuestra, ni
  pretendía demostrar, que dos máquinas distintas lleguen al mismo estado.

Por eso una materialización que dé un `artifact_sha256` distinto **no es señal
de que algo esté mal**, siempre que las tres huellas de entrenamiento coincidan.
Si alguna de esas tres se moviera, entonces sí cambió lo que entra al modelo y
hay que averiguar qué antes de usarlo.

## Requisitos de ejecución

Son 36 coeficientes: el modelo cabe en memoria sin esfuerzo, no necesita GPU y
una inferencia sobre los 76 municipios de un mes es un producto matriz-vector.
Por eso el artefacto se versiona aquí en lugar de dejarlo fuera del repositorio
con un enlace de descarga, como permitiría la rúbrica para modelos grandes.

## Cómo se regenera

Requiere acceso privado al release de datos crudos:

```sh
uv run --locked --directory pipeline kedro run --pipeline risk_2025_publication \
    --params 'risk_2025.mode=materialize,risk_2025.artifact_directory=data/risk-2025/materializacion'
```

Después se copian `model.json` y `manifest.json` a `modelos/logistica-conclima-t2/`.
Lo que hay que comprobar son las tres huellas de entrenamiento y el estado
efectivo; el `artifact_sha256` cambiará con el commit y con la arquitectura, por
lo que explica la sección anterior. El procedimiento completo, con sus
compuertas, está en
[operación de la publicación 2025](../docs/operations/risk-2025.md).
