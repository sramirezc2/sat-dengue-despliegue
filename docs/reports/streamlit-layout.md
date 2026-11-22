# Ajustes de presentación Streamlit

Base revisada: `60dc688665fc6613def2bc2eacfece8149041b06`.
Rama: `feature/streamlit-configurable-prioritization`, PR
[#18](https://github.com/sramirezc2/sat-dengue-despliegue/pull/18).
Árbol inicial limpio, HEAD remoto del PR coincidente y sin cambios ajenos.

## Aplicabilidad y cambios

Streamlit 1.67.0 admite `st.expander(..., expanded=False)`, apertura local sin
rerun por defecto (`on_change="ignore"`), columnas responsivas y altura de iframe
medida a partir de su contenido. No se agregaron dependencias, CSS, componentes
personalizados ni infraestructura.

- El respaldo científico queda dentro de un único acordeón nativo, cerrado por
  defecto. Se retira el subtítulo duplicado. El error de respaldo inválido queda
  dentro de ese acordeón; ranking, mapas y tabla permanecen disponibles.
- Resultados: título/capacidad, advertencia de déficit, mapas, leyenda común,
  tabla a todo el ancho, no elegibles, nota retrospectiva y respaldo científico.
  Tolima queda a la izquierda y Meta a la derecha. Ambos SVG tienen altura de
  200 px, ancho del contenedor y el mismo marco `270 0 460 400`, que contiene
  todos sus polígonos con margen. El iframe conserva altura de contenido para
  evitar desplazamiento interno. En la vista estrecha las columnas se apilan.
- El aviso inicial usa exactamente: «Las alertas de 2025 no se utilizan para
  evaluar aciertos ni medir el desempeño del modelo.» La leyenda sobre
  probabilidades calibradas y autorización operativa permanece.

El control de la vista estrecha detectó truncamiento del título largo y de una
etiqueta de la segunda gráfica. Se conservan todas sus palabras: el título se
presenta en dos líneas, con margen derecho de 56 px y altura de gráfica de
175 px. Son propiedades nativas de Altair; no cambian datos, escalas, tasas,
intervalos ni contenido científico. No hay barras superpuestas.

Archivos existentes modificados: `demo/app.py`, `demo/respaldo_cientifico.py`
(solo presentación de gráficas), `demo/tests/test_app.py` y
[guía de operación](../operations/streamlit-demo.md). Este informe y sus capturas
son evidencia de software nueva; no sustituyen ni editan evidencia científica.

## Verificación local

- `demo/.venv/bin/python -m pytest demo/tests -q`: **99 passed**.
- Ruff explícito de `demo/app.py`, `demo/inferencia.py`, `demo/configuracion.py`,
  `demo/contexto_paquete.py`, `demo/ejemplos.py`, `demo/respaldo_cientifico.py`,
  `demo/tests` y `streamlit_app.py`: **PASS**.
- `uv run --directory pipeline python tools/check_experiment_preservation.py`:
  **PASSED**.
- El mismo comprobador con `python -O`: **PASSED**.
- `git diff --check` y `git diff --check origin/main...HEAD`: **PASS**.

Se amplían pruebas existentes de ambos entrypoints: orden de componentes,
columnas iguales, una leyenda, tabla fuera de columnas, 47/29 polígonos con
sus títulos, todos los puntos dentro del marco, acordeón científico cerrado y
sin widget de rerun, dos gráficas/cuatro métricas y errores confinados. Permanecen
las pruebas de veinte capacidades sin segundo scoring, posiciones estables,
0/5/74 elegibles, descargas idénticas, carga CSV/Excel y métricas invariables.

Selección de gates: solo presentación de la demo, sin modificaciones a pipeline,
API, React ni sus contratos. No se repiten localmente las suites de esos
componentes; la publicación autorizada activa los checks remotos completos del
nuevo SHA. La CI anterior no acredita el nuevo commit: su resultado terminal se
registra en la descripción del PR después de comprobarlo.

## Preservación

Cotejo SHA-256 de los **654 archivos versionados de la base**: únicamente los
cuatro archivos existentes autorizados difieren. Modelo, inferencia, ranking,
contexto publicado, JSON de respaldo, fuente CSV, evidencia, publicaciones,
los 22 JSON históricos, receta, presupuesto científico de ocho, dependencias y
`plan.md` permanecen byte a byte iguales.

Cotejo AST: `load_support`, `descriptive_metrics`, `spanish` y `chart_data` tienen
implementación idéntica. El contenido de `scientific_support` es idéntico al
retirar únicamente su subtítulo y normalizar el salto de línea del título de eje.
No se entrenó, ejecutó la fábrica, regeneró contexto ni consultaron desenlaces.

## Recorrido visual en Chrome

Ventana de escritorio de 960 px y vista estrecha de aproximadamente 405 px,
obtenida acoplando DevTools a la derecha; no se afirma prueba en hardware móvil.
Las capturas estrechas incluyen el panel del navegador, sin datos sensibles.
Se usaron solo las 24 notificaciones artificiales y el contexto ya verificado.

Se comprobó 5 % → 4 seleccionados, 10 % → 8 y 100 % → 74 elegibles, con déficit
explícito de dos. Las primeras posiciones permanecen iguales. Los mapas están
completos, con los tres colores originales y sin desplazamiento interno. La
vista estrecha apila Tolima y Meta; la tabla conserva sus columnas y admite su
navegación horizontal nativa cuando es necesaria. Ambos acordeones abren y
cierran desde su encabezado. El respaldo comienza cerrado y conserva dos
gráficas y cuatro tarjetas legibles al abrirlo.

Evidencias:

- [Escritorio: ocho filas y respaldo cerrado](streamlit-layout/desktop-10-cerrado.png).
- [Escritorio: respaldo abierto](streamlit-layout/desktop-respaldo-abierto.png).
- [Escritorio: déficit al 100 %](streamlit-layout/desktop-100-deficit.png).
- [Escritorio: motivos de exclusión](streamlit-layout/desktop-excluidos.png).
- [Vista estrecha: mapas apilados](streamlit-layout/estrecho-405-mapas.png).
- [Vista estrecha: gráficas](streamlit-layout/estrecho-405-graficas.png).
- [Vista estrecha: cuatro métricas](streamlit-layout/estrecho-405-metricas.png).

La autorización remota explícita previa de la sesión permite publicar únicamente
en la rama de este PR. No se realiza merge ni despliegue externo.
