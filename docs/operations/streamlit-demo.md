# Operación de la demo Streamlit

## Despliegue académico en Community Cloud

El entrypoint de nube es **`streamlit_app.py` en la raíz**, Python **3.12**.
Community Cloud instala el único `requirements.txt` de ese directorio. Este fija
las versiones compatibles con los locks existentes e instala `-e ./pipeline`:
el modo editable es necesario porque el paquete resuelve recetas y artefactos
relativos al checkout. No se necesita preparar una `.venv` en el servidor.
`demo/app.py` y su entorno separado continúan siendo el recorrido local.

El contexto público está en
[sat-dengue/hf_hub_download](https://huggingface.co/datasets/sat-dengue/hf_hub_download),
archivo `context-real-v1.zip`, revisión
`3935f67b9b79a0e8810f7804867d919615d3840a`, SHA-256
`59fad5e1f56b5603feca036656756a8e04d19b502925ad0157ff03639d25ff6e`.
La identidad completa se conserva en `demo/context-release.json`. El launcher
configura esos valores sin pedir credenciales al visitante. El cliente oficial
`hf_hub_download` usa `repo_type=dataset` y `token=False`; el ZIP pasa después
por las validaciones de SHA, inventario, meses, población y release existentes.
La revisión completa evita seguir cambios futuros de `main` en Hugging Face.

Variables públicas adicionales: `SATD_DEMO_HF_REPO_ID`,
`SATD_DEMO_HF_REVISION` (40 caracteres hexadecimales), `SATD_DEMO_HF_FILENAME`.
El nombre admitido es `context-real-v1.zip`. No configurar a la vez estas
variables y `SATD_DEMO_CONTEXT_BUNDLE_URL`. El directorio local existente sigue
teniendo prioridad, y una caché verificada permite reiniciar sin volver a la red.

Para desplegar: conectar el repositorio en Community Cloud, elegir la rama
revisada, `streamlit_app.py` y Python 3.12. No se requiere ningún secreto.
El propietario o administrador del repositorio debe completar la conexión si
la cuenta que publica solo tiene permiso de escritura. El despliegue público y
la aceptación en navegador externo se acreditarán con su URL y recibo; una
prueba local no acredita esa entrega.

Prueba de instalación desde la raíz:

```sh
uv venv .venv-cloud --python 3.12
uv pip install --python .venv-cloud/bin/python -r requirements.txt
.venv-cloud/bin/streamlit run streamlit_app.py
```

El paquete (284.552 bytes) contiene derivados mensuales agregados, no microdatos,
etiquetas ni desenlaces de 2025. Su publicación pública fue autorizada por el
equipo. Las referencias a contexto privado y alojamiento neutral más abajo
describen el mecanismo local/HTTPS previo; Community Cloud utiliza el Dataset
público fijado en esta sección.

La entrega final de aplicación es `demo/app.py`. API/React en `app/` es el
servicio heredado de publicaciones, con despliegue y dependencias independientes.
La demo carga notificaciones en memoria, valida un mes, aplica el modelo
congelado, obtiene posiciones y simula cupos antes de presentar tabla y mapa.
No entrena, publica resultados ni modifica la fábrica. Obtiene un contexto ya
construido mediante el único mecanismo de `demo/contexto_paquete.py`: directorio
local o paquete HTTPS verificado y cacheado. No necesita crudos ni ejecuta Kedro.
El tutor nunca ingresa credenciales; cualquier token pertenece solo al servidor.

## Estado del alojamiento

Community Cloud está elegido para la entrega actual. No hay aún URL pública
comprobada: el formulario confirmó que `j-mauro-r` carece de permiso administrador
sobre el repositorio oficial y deshabilitó Deploy. La instancia AWS Academy del
servicio heredado es independiente. El procedimiento neutral siguiente se
conserva para instalaciones locales o en otro host; la configuración pública de
Hugging Face está descrita al comienzo de esta guía.

La siguiente receta es para un alojamiento Python/Linux que admita instalación
bloqueada, almacenamiento privado persistente y WebSocket detrás de HTTPS. No
supone contratación ni autoriza transferir contexto a un proveedor sin elegir.
No necesita Docker. Un proveedor que publique el árbol completo de archivos o
solo permita repositorios públicos para instalar el contexto es incompatible.

## Instalación bloqueada desde un clon limpio

Requisitos: Python **3.12** (validado localmente con 3.12.13), uv **0.11.19** y
Git. En macOS, `libomp` según la [guía del pipeline](pipeline-operations.md).
Clonar un SHA revisado de esta rama; los comandos parten de la raíz del clon:

```sh
git checkout <SHA-revisado>
uv lock --check --project pipeline
UV_PROJECT_ENVIRONMENT="$PWD/demo/.venv" uv sync --locked --project pipeline --no-dev
uv pip install --python demo/.venv/bin/python --require-hashes -r demo/requirements.lock
```

`pipeline/uv.lock` fija el paquete científico y sus dependencias. El lock
adicional `demo/requirements.lock` fija con hashes Streamlit **1.67.0**, openpyxl
**3.1.5** y sus transitivas, respetando las versiones compartidas del lock
científico. El entorno `demo/.venv` evita introducir PyArrow/Streamlit en el
entorno de validación científica. No ejecutar `uv sync` sobre él después de la
instalación adicional sin volver a instalar el lock de la demo. El inicio usa
directamente su ejecutable y no resuelve dependencias en cada arranque.

Para renovar deliberadamente el lock de la demo (no en cada despliegue):

```sh
mkdir -p pipeline/data/demo-validation
uv export --locked --project pipeline --no-dev --no-emit-project --no-hashes --output-file pipeline/data/demo-validation/pipeline-constraints.txt
uv pip compile demo/requirements.txt --constraint pipeline/data/demo-validation/pipeline-constraints.txt --python-version 3.12 --universal --generate-hashes --no-annotate --output-file demo/requirements.lock
```

Revisar el diff y repetir las pruebas. El lock científico no se modifica.
`--universal` es obligatorio para conservar las dependencias condicionadas por
sistema operativo: Streamlit requiere `watchdog` en Linux/Windows y lo omite en
macOS. CI comprueba la resolución completa con hashes y wheels para los tres
sistemas antes de instalar la demo en su runner Ubuntu. Es una resolución
cruzada; no sustituye ejecutar la demo de forma nativa en cada sistema.

## Rutas e identidad

| Variable | Default relativo a la raíz del repositorio | Recurso |
| --- | --- | --- |
| `SATD_DEMO_MODEL_DIR` | `modelos/logistica-conclima-t2` | `model.json` y `manifest.json` versionados |
| `SATD_DEMO_CONTEXT_DIR` | `pipeline/data/demo` | Contexto local; si existe se valida y tiene prioridad |
| `SATD_DEMO_CONTEXT_BUNDLE_URL` | Sin valor | URL HTTPS final del paquete privado; puede contener una firma y se trata como secreto |
| `SATD_DEMO_CONTEXT_BUNDLE_SHA256` | Sin valor | SHA-256 de 64 caracteres hexadecimales minúsculos, recibido por canal confiable |
| `SATD_DEMO_CONTEXT_TOKEN` | Sin valor, opcional | Credencial servidor: encabezado `Authorization: Bearer …` |
| `SATD_DEMO_CONTEXT_CACHE_DIR` | `pipeline/data/demo-context-cache` | Caché privada local, creada si hace falta |

Las variables solo reubican recursos locales. Una ruta relativa siempre parte
de la raíz del repositorio, con independencia del directorio de ejecución. Se
rechazan valores vacíos, URL en variables de directorio, componentes `..` y enlaces
simbólicos en la ruta o los archivos. Usar rutas físicas; en macOS una ruta bajo
el alias `/var` debe expresarse como su ruta física `/private/var`. El directorio
del modelo debe existir; el de contexto puede estar ausente para activar el
bootstrap. La caché se crea con permisos privados, fuera del contenido público.

El modelo debe conservar el SHA-256 aprobado
`d0a883a7528afd5d3d1fdbe43d44e5c5a396c109ab20ed49845a198ccdb75c8c`.
No hay variable para cambiar el modelo, su identidad, release o procedimiento.
Cambiar su ruta no desactiva `load_artifact` ni sus comprobaciones de manifiesto,
tipos, versión, receta, estado efectivo y cortes de aprendizaje.

El índice de contexto debe tener `raw_manifest_sha256` igual al del modelo y
un mapa no vacío `files` de orígenes `2024-11` a `2025-10` a hashes SHA-256. Puede
instalarse solo el conjunto completo de doce orígenes para arrancar Streamlit. Cada CSV debe coincidir con su hash,
columnas, mes y 76 municipios de Meta/Tolima; los tipos se convierten según el
modelo. Un índice inconsistente, archivo alterado, enlace o release ajeno
detiene toda la carga, sin contexto alternativo ni inferencia de respaldo.

Los hashes detectan inconsistencia con el índice; **no autentican un índice
reemplazado junto con los archivos**. La provisión y los permisos del paquete
son parte de la frontera de confianza. Obtenerlo de su custodio autorizado por
canal autenticado; no aceptar índices suministrados por visitantes de la demo.

## Contexto y CSV de notificaciones: entradas diferentes

El archivo que carga el tutor contiene notificaciones de **un mes completo**.
El contexto contiene los predictores históricos ya preparados: rezagos, clima y
canal endémico para cada origen. Su construcción offline usa historia desde 2007
hasta el respectivo mes de origen, mediante el prefijo temporal existente. Los
orígenes son 2024-11, 2024-12 y 2025-01 a 2025-10: doce archivos con 76 municipios
cada uno. No incluye etiquetas ni desenlaces de 2025. La construcción existente
`demo/contexto.py` es una operación científica separada; **no se ejecuta durante
el arranque, no se reconstruye aquí y no se adquieren datos crudos**.

## Empaquetado offline del contexto existente

El custodio, con el contexto ya construido y el modelo aprobado:

```sh
demo/.venv/bin/python demo/contexto_paquete.py --source pipeline/data/demo --output pipeline/data/demo-distribution/context-v1.zip
```

Valida el índice, hashes internos, release, doce meses, columnas sin etiquetas y
76 municipios por mes. Solo incorpora los trece archivos de contexto y un
`bundle.json` de identidad. Archivos ajenos al inventario no se empaquetan.
Produce un ZIP pequeño `satd-demo-context-v1`, sin rutas absolutas ni secretos.
El orden de miembros, timestamps ZIP y permisos son fijos; los mismos archivos
producen los mismos bytes y SHA-256. Usa ZIP_STORED de la biblioteca estándar,
sin dependencias ni variación por versión del compresor.

El recibo `context-v1.manifest.json` contiene formato, SHA-256 del paquete,
release, SHA del modelo, meses, 76 municipios y fecha UTC de empaquetado. La fecha
queda fuera del ZIP para mantener su determinismo. Ni paquete ni recibo existentes
se sobrescriben. La salida sugerida está ignorada por Git; el paquete real es
privado y **no se sube ni distribuye en esta iteración**.

## Obtención automática y caché

1. Si `SATD_DEMO_CONTEXT_DIR` existe, validar sus doce contextos y usarlo. Un
   directorio presente pero inválido detiene el arranque; no hay fallback que
   oculte corrupción. El valor predeterminado sigue funcionando localmente.
2. Si está ausente, exigir `SATD_DEMO_CONTEXT_BUNDLE_SHA256`. Reutilizar la entrada
   de caché de ese hash si ZIP y extracción continúan íntegros. Una caché válida
   permite reiniciar incluso sin URL/token disponibles, manteniendo el pin SHA.
3. Si no hay caché, exigir `SATD_DEMO_CONTEXT_BUNDLE_URL` y descargar por HTTPS,
   con certificado TLS verificado, timeout de socket de 15 s y máximo 16 MiB.
   HTTP loopback solo se habilita explícitamente en código de pruebas; no existe
   variable de entorno para activarlo en la UI.
4. Si se configura token, enviarlo como Bearer solo al recurso final. Se rechazan
   redirecciones y credenciales incrustadas en URL; se admiten parámetros de URL
   firmada, que tampoco se registran. Usar una URL final compatible con este
   contrato HTTP; no se implementan adaptadores de proveedores.
5. Descargar en un temporal privado, comprobar SHA externo **antes de abrir el
   ZIP**, verificar formato/inventario y extraer solo nombres exactos admitidos.
   Máximo expandido 32 MiB; no rutas absolutas, `..`, unidades Windows, enlaces,
   miembros duplicados, directorios, cifrado ni extras. No se usa `extractall`.
6. Ejecutar después `load_context`: índice, hashes internos, release, meses,
   territorio y tipos. Solo tras validar todo, promover por rename atómico a
   `<caché>/<sha256>/`, con `bundle.zip` y `context/`. No queda una instalación
   parcial expuesta y los temporales corruptos se retiran automáticamente.

En otro arranque se comprueba otra vez el hash externo, el inventario y los
bytes extraídos contra el paquete original, además de las validaciones internas.
Alterar CSV e índice juntos tampoco elude la identidad externa. Dentro del proceso,
`st.cache_resource` evita repetir obtención/carga en cada interacción; el ranking
permanece por sesión y cambiar cupos no vuelve a puntuar.

La fuente del pin SHA debe ser confiable: los hashes no autentican por sí solos
un paquete y pin sustituidos juntos. El contexto y caché deben estar fuera de
servidores estáticos, repositorios, sincronizaciones y volúmenes públicos.
Los archivos subidos por visitantes siguen en memoria y no entran en esta caché.

## Configuración privada del servidor

Un administrador configurará URL, SHA y token opcional como variables de entorno
o secretos del servidor **en la siguiente iteración**, después de elegir
proveedor. No se configura ni se prueba aquí un proveedor real. El tutor no
necesita cuenta, token ni permiso: abre la aplicación y carga su CSV mensual.

El modelo se conserva en `modelos/logistica-conclima-t2`; su variable solo permite
reubicar exactamente los mismos bytes aprobados. Para usar el paquete automático,
`SATD_DEMO_CONTEXT_DIR` debe señalar una ruta ausente (o mantenerse en el default
si no está instalado el contexto local). Configurar los nombres de variables de
la tabla mediante el gestor de secretos; nunca pegar tokens o URL firmadas en
Git, comandos, capturas, recibos o logs. No usar `HF_TOKEN` en el runtime: la
credencial HTTP opcional es neutral respecto al almacenamiento elegido.

Preflight del administrador, una vez configurado el entorno privado:

```sh
PYTHONPATH=demo demo/.venv/bin/python -c 'from inferencia import load_model; from contexto_paquete import obtain_context; print("Contexto verificado:", len(obtain_context(load_model())), "orígenes")'
```

Los errores de disponibilidad/autorización/hash muestran un mensaje fijo sin
URL, token, rutas ni excepción de red encadenada. No se pide resolverlos al tutor.

## Inicio y verificación local

```sh
SATD_DEMO_CONTEXT_DIR=/srv/satd-private/context-v1 demo/.venv/bin/streamlit run demo/app.py --server.address 127.0.0.1 --server.port 8501 --server.headless true --browser.gatherUsageStats false
```

El default local no necesita variables si los recursos están en sus rutas
originales. En el host, conservar `127.0.0.1` si un proxy HTTPS local termina TLS;
usar `0.0.0.0` solo si el runtime gestionado necesita escuchar en su interfaz
interna. El proxy debe soportar WebSocket. No desactivar CORS/XSRF para alojar.

```sh
curl --fail http://127.0.0.1:8501/_stcore/health
```

Debe responder HTTP 200 y `ok`. La salud HTTP acredita el proceso, no la
disponibilidad del contexto: ejecutar también el preflight anterior y el
recorrido funcional. Para validar software sin datos privados:

```sh
UV_PROJECT_ENVIRONMENT="$PWD/demo/.venv" uv sync --locked --project pipeline
uv pip install --python demo/.venv/bin/python --require-hashes -r demo/requirements.lock
demo/.venv/bin/python -m pytest demo/tests -q
```

Estas pruebas instalan contextos artificiales temporales, usan el modelo
versionado, recorren la UI con `streamlit.testing.v1.AppTest`, cambian las veinte
capacidades de 5 % a 100 % sin un segundo scoring, comparan tabla/mapa y reinician sesión. Además
arrancan dos procesos reales de Streamlit, comprueban salud/página HTTP y los
detienen. No crean evidencia científica ni acceden a contexto privado.
CI ejecuta explícitamente `demo/tests` en un entorno separado; el descubrimiento
normal de pytest bajo `pipeline/` no los incluye.

## Recorrido funcional en el alojamiento

Después de elegir y configurar proveedor, SHA, contexto privado y dominio TLS:

1. Instalar desde clon y entorno nuevos; validar modelo/contexto antes del inicio.
2. Abrir la URL HTTPS y comprobar que no hay error de configuración.
3. Pulsar **Cargar muestra artificial**: deben verse 24 notificaciones y seis
   municipios con casos, el origen disponible y su objetivo T+2.
4. Pulsar **Calcular prioridades T+2**: revisar mapas, tabla y excluidos.
   Tolima aparece a la izquierda y Meta a la derecha, con altura SVG común de
   200 px y marco que contiene todos los polígonos. En pantallas estrechas las
   columnas nativas pueden apilarse. Hay una sola leyenda; la tabla ocupa todo
   el ancho debajo de los mapas, seguida del acordeón de no elegibles. El número
   seleccionado es el menor entre elegibles y ocho; el contexto auténtico puede
   excluir municipios que el fixture artificial no excluye.
5. Cambiar 5/10/25/50/90/95/100 %: cupos solicitados 4/8/19/38/69/73/76.
   La tabla contiene solo seleccionados y conserva posiciones; el mapa mantiene
   los 76 municipios. Si faltan elegibles se informa el déficit.
   Ambos botones de descarga sirven `sample_csv` del último mes verificado, con
   los mismos bytes y nombre `muestra-artificial.csv` (24 notificaciones inventadas
   de seis municipios), listo para cargar sin edición.
   Debajo de la nota retrospectiva, el acordeón **Respaldo científico del modelo**
   está cerrado por defecto. Su encabezado abre o cierra el contenido sin rerun
   ni nuevo scoring; no hay subtítulo duplicado. Dentro se conservan dos gráficas
   y cuatro métricas de la receta en
   la confirmación retrospectiva 2023–2024: no evalúan el archivo cargado ni cambian
   con el selector. `demo/respaldo-cientifico.json` fija conteos, intervalos y SHA-256
   de `docs/evidence/reserva-2023-2024-t2/reserva.csv`; si falla su validación, el
   ranking permanece visible y se informa el error solo dentro de ese acordeón.
   El aviso inicial dice: «Las alertas de 2025 no se utilizan para evaluar aciertos
   ni medir el desempeño del modelo».
6. Reiniciar el proceso desde el administrador del servicio; volver a comprobar
   salud y repetir la muestra/inferencia. La sesión nueva no conserva una carga
   anterior y los recursos privados deben seguir disponibles.
7. Desde fuera del host, comprobar certificado y acceso HTTPS, sin `--insecure`:

   ```sh
   curl --fail --proto '=https' https://<dominio>/_stcore/health
   ```

   Debe dar 200 y `ok`; comprobar también la UI y WebSocket en navegador externo.
   Solo después registrar aquí y en el README la URL verificada con fecha y SHA.

## Actualización, reinicio y recuperación

En Linux propio puede usarse systemd (en un PaaS, su administrador equivalente).
Ejemplo de unidad, sustituyendo usuario y rutas físicas del clon:

```ini
[Unit]
Description=SAT Dengue Streamlit
After=network.target

[Service]
User=satd
WorkingDirectory=/srv/satd/release
Environment=SATD_DEMO_CONTEXT_DIR=/srv/satd-private/context-v1
ExecStart=/srv/satd/release/demo/.venv/bin/streamlit run demo/app.py --server.address 127.0.0.1 --server.port 8501 --server.headless true --browser.gatherUsageStats false
Restart=on-failure
UMask=0077
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
```

Instalar como `/etc/systemd/system/satd-demo.service`; luego
`sudo systemctl daemon-reload` y `sudo systemctl enable --now satd-demo`.
El dominio, certificado y proxy HTTPS son configuración externa pendiente,
específica del proveedor. No reutilizar el contenedor de API para inferencia.

Para actualizar: preparar **otro clon/directorio físico** del SHA revisado,
instalar ambos locks, ejecutar preflight y pruebas, y configurar la nueva ruta
WorkingDirectory/ExecStart. Conservar la versión y el contexto anteriores.
Aplicar `sudo systemctl daemon-reload` y `sudo systemctl restart satd-demo`;
repetir salud, muestra, inferencia, porcentajes y HTTPS. Revertir las rutas a la
versión anterior y reiniciar si falla. No usar `reset --hard` ni sobrescribir
el contexto instalado mientras el proceso lo mantiene en caché.

Ante contexto ausente/corrupto/release ajeno: la UI muestra un error sanitizado y
no ofrece resultados. Los temporales descargados se eliminan al fallar; un ZIP
corrupto detectado en la caché se descarta, sin continuar ni redescargar en esa
misma solicitud. La entrada inválida no se considera utilizable. Conservar el paquete fallido para diagnóstico privado;
no editar el índice para aceptar bytes diferentes ni regenerar ciencia como
fallback. Restaurar el directorio local desde el custodio, o configurar una nueva ruta
privada de caché y el pin/URL correctos, sin editar índices para aceptar corrupción.
Ejecutar preflight y reiniciar. El reinicio invalida
la caché de recursos. Consultar [recuperación](pipeline-operations.md#recuperación-y-troubleshooting)
si el problema afecta las fuentes o evidencia, sin repetir experimentos.

## Paso externo pendiente

Se necesitan una **decisión de proveedor**, acceso administrativo al servicio,
una ruta/volumen privado persistente con el **contexto autorizado**, y un
dominio o URL HTTPS con soporte WebSocket. Un token de HF por sí solo no permite
desplegar ni sustituye el contexto. Tras autorizar ese destino, ejecutar la
instalación y preflight de esta guía, configurar inicio/reinicio y completar los
siete pasos del recorrido público. Hasta entonces solo se acredita la
validación local con datos artificiales, sin declaración de despliegue público.


## Alcance diferido de esta iteración

Se valida software, transporte loopback con contexto artificial, salud HTTP y
reinicio local. No se realiza despliegue público, validación desde un navegador
externo, wireframe, mockup ni evidencia final de sustentación. Proveedor, URL HTTPS
y secretos reales se configurarán posteriormente. Ninguna instrucción de
alojamiento de esta guía acredita que esa instalación haya ocurrido.
