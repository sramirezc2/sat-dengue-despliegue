# Validación de la presentación académica Streamlit

Fecha: 2026-11-21. PR [#18](https://github.com/sramirezc2/sat-dengue-despliegue/pull/18).
Rama: `feature/streamlit-configurable-prioritization`.

## Aplicabilidad y alcance

Árbol inicial limpio en el worktree solicitado. HEAD inicial de la sesión:
`a2b2411b5737c0b152e93c5e4789db44006a544d`. Se comprobó que el PR abierto tenía
exactamente el HEAD revisado `24945fc5c0df8af85f2773917c5273683640e801` y se integró
por fast-forward antes de editar. Ese commit es la base de esta validación.
Los tres cambios son aplicables sin modificar el procedimiento científico.

- Ambos botones sirven los mismos bytes de `sample_csv` del último mes de contexto
  verificado y el mismo nombre `muestra-artificial.csv`. Se retiró `template_csv`
  al desaparecer sus consumidores. Son 24 notificaciones inventadas de seis
  municipios; el archivo se acepta sin edición.
- Veinte porcentajes de 5 % a 100 %, predeterminado 10 %. Capacidad con
  `ceil(76 × porcentaje / 100)`. La tabla contiene solo `Priorizado == True`, en su
  posición original. El selector reutiliza el ranking almacenado; mapa completo
  de 76 municipios y motivos de exclusión conservados. Se explicita el déficit.
- Debajo del resultado se presentan dos gráficas horizontales desde cero y cuatro
  tarjetas. Los conteos históricos y las métricas permanecen iguales al cambiar la
  simulación. Un respaldo ausente o corrupto produce un error local en la sección,
  conservando ranking, tabla y mapa.

Cambios: `demo/app.py`, `demo/ejemplos.py`, `demo/inferencia.py`, el nuevo JSON y
módulo `demo/respaldo_cientifico.py`, pruebas de la demo, lista explícita de Ruff en
CI, `.gitattributes` y [guía de operación](../operations/streamlit-demo.md). No se agregaron
dependencias, servicios ni infraestructura.

## Revisión científica de la presentación

Recomendación: **APPROVED_WITH_LIMITATIONS**, exclusivamente para presentar
agregados existentes de la receta. No constituye aprobación científica nueva ni
aprobación independiente del modelo congelado.

Fuente única: [reserva.csv](../evidence/reserva-2023-2024-t2/reserva.csv), fila
`receta=log_conclima`, `horizonte=2`, `presupuesto=0.1`. Su
[README](../evidence/reserva-2023-2024-t2/README.md) documenta la procedencia y el
bootstrap por bloques de mes de origen (2.000 réplicas).
SHA-256 de la fuente:
`35d2c8d0c3082374272fa17c6ff32ce727427f8a5f10c8c2661547c9eff2172f`.

| Presentación | Cálculo a partir de conteos | Valor mostrado |
|---|---|---|
| Sensibilidad del modelo | 70 / 147 | 47,6 % |
| Sensibilidad del canal | 57 / 147 | 38,8 % |
| Precisión del modelo | 70 / 200 | 35,0 % |
| F1 del modelo | 2 × 70 / (200 + 147) | 0,403 |
| Falsas alertas por inicio anticipado | (200 − 70) / 70 | 1,86 |
| Carga del modelo por 100 municipio-mes | 100 × 130 / 836 | 15,6 |
| Carga del canal por 100 municipio-mes | 100 × 143 / 836 | 17,1 |

Diferencia de sensibilidad publicada: +8,8 pp, IC 95 % [+1,4; +16,3]. Diferencia de
carga publicada: −1,56 por 100 municipio-mes, IC 95 % [−2,87; −0,24]. Los intervalos
son de las diferencias; no se dibujan como intervalos individuales de las barras.
Presupuesto nominal histórico del 10 %: 200 alertas por método en 23 meses,
8,7 mensuales. Este agregado histórico no cambia el presupuesto científico
congelado de **ocho** municipios.

Limitación explícita: es **confirmación retrospectiva 2023–2024** de la receta,
no una reserva independiente ni una evaluación del archivo del visitante o del
artefacto actual sobre ese archivo. La UI reproduce la distinción solicitada.
No se consultaron desenlaces de 2025, no se entrenó ni recalibró, y no se ejecutó la
fábrica experimental. Las pruebas con fixtures artificiales solo validan software.

## Gates locales

| Comando o comprobación | Resultado |
|---|---|
| `uv lock --check --project pipeline` | PASS |
| `uv sync --locked --project pipeline` | PASS, lock sin cambios |
| `uv run --directory pipeline ruff check .` | PASS |
| Ruff explícito de demo, módulo nuevo, pruebas y `streamlit_app.py` | PASS |
| `demo/.venv/bin/python -m pytest demo/tests -q` | 99 passed |
| `uv run --directory pipeline pytest` | 896 passed, 6 advertencias preexistentes de OmegaConf (504,42 s) |
| `app/api/.venv/bin/python -m pytest app/api` | 54 passed; 1 advertencia Starlette/httpx preexistente |
| Dashboard: `bun install --frozen-lockfile` | PASS, sin cambios |
| Dashboard: `bun run lint` | PASS, 6 advertencias Fast Refresh preexistentes |
| Dashboard: `bun run test` | 72 passed, 1 skipped |
| Dashboard: `NITRO_PRESET=node_server bun run build` | PASS; aviso preexistente de vite-tsconfig-paths |
| `uv run --directory pipeline python -m sat_dengue_pipeline.experiment_management validate` | VALID |
| `tools/check_experiment_preservation.py`, normal y `python -O` | PASSED en ambos |
| `git diff --check` y `git diff --check origin/main...HEAD` | PASS |
| `tools/validate_publication_consumers.py` con los 22 JSON históricos | PASS, Pydantic y Zod |

Ruff explícito:

```sh
uv run --locked --project pipeline ruff check --config pipeline/pyproject.toml \
  demo/app.py demo/inferencia.py demo/configuracion.py demo/contexto_paquete.py \
  demo/ejemplos.py demo/respaldo_cientifico.py demo/tests streamlit_app.py
```

El único test omitido del dashboard requiere `SATD_RISK_E2E_RESPONSE`, ausente;
no se sustituyó por una respuesta fabricada. Bun local 1.4.0; la CI usa 1.4.4.

Las pruebas cubren las veinte capacidades y su redondeo, selección sin nuevo
scoring en ambos entrypoints, descargas idénticas y carga CSV/Excel, ranking y
posiciones estables, cero/5/74 elegibles, 76 polígonos con colores coherentes,
cuatro métricas invariables, dos gráficas y ausencia de scores individuales,
reconciliación con la única fila fuente, validación de esquema/identidad/hashes,
y errores aislados ante JSON ausente o corrupto. Se prueba el contraste de las
etiquetas numéricas en temas claro y oscuro. La regresión de checkout ejecuta
`git -c core.autocrlf=true cat-file --filters`: el JSON conserva exactamente su
SHA-256. Antes de fijar LF para este archivo, esa simulación producía CRLF y un
hash distinto. El ajuste es de checkout; el contenido del JSON y la UI no cambian.
Las suites acumuladas se ejecutaron antes de ese ajuste de LF. Después se repitieron
las 99 pruebas de demo, lock/sync, Ruff, preservación normal/-O y diff; la CI del SHA
final valida además las suites completas y los runners nativos.

## Preservación

Se cotejaron los SHA-256 de los 647 archivos de la base revisada: únicamente
cambiaron los ocho archivos existentes autorizados de producto/pruebas/CI/guía.
El modelo, `plan.md`, manifiestos, dependencias, receta, contexto publicado,
evidencia científica y publicación histórica conservan sus bytes.
La comprobación de preservación informa 49 archivos protegidos, 127 extendidos,
22 JSON publicados y 16 recibos anteriores, con identidad N=3 conservada.

- Modelo `modelos/logistica-conclima-t2/model.json`:
  `d0a883a7528afd5d3d1fdbe43d44e5c5a396c109ab20ed49845a198ccdb75c8c`.
- `demo/context-release.json`:
  `24f233f0e579b98c0ab3a1c0836a08919275f6e64f01e1f2c70089d02f6c4bc8`.
- Publicación histórica:
  `4d3ddd3890a6a622b658fc2b1ef0159d0da6bc855cacc2c5b62854290623e16e`.

Se revisaron archivos nuevos y diff para no agregar secretos, datos privados,
predicciones por fila, modelos ni archivos pesados. Las tres capturas de software
ocupan aproximadamente 393 KB en total; ninguna supera 154 KB.

## Recorrido visual en Chrome

App raíz `streamlit_app.py`, servidor local en loopback, ancho de 960 px y zoom
normal. Se descargó el CSV inicial y se cargó ese mismo archivo sin editar:
24 notificaciones aceptadas, seis municipios con casos, un mes (2025-10) y objetivo
T+2 (2025-12). Son notificaciones artificiales; no son desenlaces observados.
El contexto verificado disponible tiene 74 elegibles para esa muestra.

| Porcentaje probado en Chrome | Cupos solicitados | Seleccionados |
|---|---:|---:|
| 5 % | 4 | 4 |
| 10 % | 8 | 8 |
| 25 % | 19 | 19 |
| 50 % | 38 | 38 |
| 90 % | 69 | 69 |
| 95 % | 73 | 73 |
| 100 % | 76 | 74, déficit explícito de 2 |

Se comprobaron las primeras posiciones estables, tabla solo con el top, mapa
completo con las categorías originales y desplegable de excluidos conservado.
Las dos gráficas muestran valores y métodos; las cuatro tarjetas tienen nombres
y definiciones legibles. La revisión detectó y corrigió etiquetas negras sobre
fondo oscuro y el truncamiento del nombre de la cuarta tarjeta.

Evidencias finales, solo muestra artificial y agregados históricos públicos:

- [Tabla de ocho y mapa completo](streamlit-academic-ui/seleccion-10.png).
- [Introducción y dos gráficas históricas](streamlit-academic-ui/respaldo-graficas.png).
- [Carga de falsas alertas y cuatro tarjetas](streamlit-academic-ui/respaldo-tarjetas.png).

## Recuperación de los límites de tiempo de CI

La ejecución [44938492833](https://github.com/sramirezc2/sat-dengue-despliegue/actions/runs/44938492833),
sobre `b5c7d95`, aprobó las 98 pruebas de demo y la instalación de Community Cloud,
pero agotó los límites de los jobs: quality a los 15 minutos y portabilidad
Ubuntu/Windows a los 20. El último progreso de quality fue 80 %, sin aserción
fallida registrada; su log conserva `The operation was canceled`. macOS completó
la portabilidad con PASSED. Los logs originales y los intentos cancelados se
conservan en GitHub; la ausencia de recibos Ubuntu/Windows es consecuencia de la
terminación, no se fabrican recibos para completar esos intentos.

Recuperación mínima: ampliar únicamente el límite de ambos tipos de job a
45 minutos, manteniendo íntegros comandos, pruebas, aserciones, matriz, versiones
y procedimiento científico. Es un límite operativo de CI, independiente del
presupuesto científico de ocho. No se cambia código de cálculo ni se omiten tests.
No corresponde un nuevo ID experimental: son gates de software, no una ejecución
científica. Validación local de YAML y equivalencia de todas las demás claves;
la recuperación solo queda acreditada cuando la CI del SHA final termine verde.

## Entrega remota

El resultado terminal de CI corresponde al SHA final del PR, y se registra en la
descripción actualizada del [PR #18](https://github.com/sramirezc2/sat-dengue-despliegue/pull/18).
La autorización permite push únicamente a la rama indicada. No se abre otro PR
ni se realiza merge. La aprobación humana de revisión sigue siendo independiente
de los gates técnicos.
