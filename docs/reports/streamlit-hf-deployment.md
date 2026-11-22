# Integración académica Streamlit + Hugging Face

Fecha: 2026-11-21. Base: `a2b2411`.

El contexto real fue publicado con autorización del usuario en el Dataset público
`sat-dengue/hf_hub_download`, commit
`3935f67b9b79a0e8810f7804867d919615d3840a`.
La descarga anónima devolvió 284.552 bytes con SHA-256
`59fad5e1f56b5603feca036656756a8e04d19b502925ad0157ff03639d25ff6e`,
idéntico al paquete validado previamente. No se publicaron fuentes crudas ni
archivos nuevos en GitHub; el ZIP permanece en Hugging Face.

## Implementación

- `demo/contexto_paquete.py`: cliente oficial del Hub, revisión completa,
  `repo_type=dataset`, `token=False`, copia regular antes de verificar y extraer.
- `demo/context-release.json`: identidad pública inmutable de contexto.
- `streamlit_app.py`: entrada de Community Cloud; configura el release público
  y ejecuta la misma interfaz existente.
- `requirements.txt`: instalación editable del paquete local y versiones
  compatibles con `pipeline/uv.lock` y `demo/requirements.lock`.
- CI: detección de cambios del launcher/requirements e instalación limpia Linux.

El modo editable conserva las rutas del checkout que usa el paquete científico.
La primera instalación no editable se descartó tras comprobar que resolvía
incorrectamente las rutas de recetas/modelo. La prueba posterior en entorno
vacío recorrió contexto real, muestra artificial, inferencia, tabla y mapa sin
errores; primera interfaz utilizable observada en 4,58 segundos en macOS.
Ese tiempo no es una medida de Community Cloud.

## Validación de software

- Demo: **70 PASS**, incluidos cinco casos nuevos del transporte Hub y la
  regresión del launcher con contexto artificial.
- Ruff: PASS para pipeline, demo y launcher.
- Descarga real anónima en caché vacía: PASS, revisión y hash exactos.
- Instalación limpia Python 3.12.13: PASS; sin dependencias de desarrollo ni MLflow.
- Preservación normal y `python -O`: PASS; 22 JSON, 49 protecciones originales,
  127 extendidas y recibos T16 intactos.
- Registro experimental: VALID.
- Pipeline completo: **896 PASS**, seis avisos heredados de OmegaConf, 525,89 s.
- API: **54 PASS**, un aviso heredado de TestClient.
- Dashboard: **72 PASS / 1 omitida** por condición externa preexistente;
  instalación frozen, lint y build PASS; avisos heredados de Fast Refresh/Vite.
- Kedro sintético: PASS, cinco nodos.
- Diff e higiene de secretos: PASS.
- CI del nuevo commit: pendiente de la publicación del commit.

## Accesos y entrega pública

GitHub confirmó `push=true` y `admin=false` para `j-mauro-r` sobre el repositorio
oficial. El PR existente es #18. La creación de la app en Community Cloud puede
requerir intervención del propietario/administrador para conectar ese repositorio.
No se crea un fork automáticamente ni se eluden reglas de revisión o merge.
La pantalla de Community Cloud confirmó el bloqueo con el mensaje
“You do not have admin permissions on GitHub for this repository” y el botón
Deploy deshabilitado. La cuenta de Streamlit sí quedó autenticada.

La integración local y la publicación del contexto no acreditan una app pública.
URL, prueba en navegador externo, capturas y tiempos de nube permanecen pendientes
hasta crear la app. La demo conserva su alcance académico, T+2 y simulación de
capacidad; no incorpora evaluación de aciertos de 2025 ni habilitación operativa.
