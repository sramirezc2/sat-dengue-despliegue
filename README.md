# SAT Dengue, despliegue del tablero de alerta temprana

Sistema de alerta temprana de brotes de dengue para los municipios de **Tolima
y Meta**. Este repositorio contiene la aplicación desplegada y la fábrica
científica V3 independiente: la API sirve resultados persistidos, el tablero los
presenta y `pipeline/` los construye sin introducir Kedro en el producto.

Universidad de los Andes, Maestría en Inteligencia Artificial.
Proyecto: Despliegue de Soluciones. **Grupo 11**.

---

## 1. El problema y la solución

En Colombia el dengue se vigila con el **canal endémico**, que compara los
casos del mes contra los percentiles históricos de ese mismo municipio. Es una
herramienta retrospectiva: dice que el municipio ya está en exceso, no que va a
estarlo. Para una secretaría de salud esa diferencia es la que separa reaccionar
de anticipar, porque las acciones de control (fumigación, búsqueda de
criaderos, refuerzo de diagnóstico) necesitan semanas para surtir efecto.

La solución es un clasificador binario por municipio y mes. Para cada par
municipio-mes se arma un vector con la información disponible al cierre del mes
y se estima la probabilidad de que el mes siguiente (T+1) o el subsiguiente
(T+2) supere el **percentil 75 del canal endémico** de ese municipio. La salida
es una probabilidad calibrada y una decisión de alerta contra un umbral
explícito.

El criterio de utilidad que fijó el proyecto tiene tres condiciones: detectar
una fracción apreciable de los **inicios** de brote, no solo de los meses en
exceso; superar al canal endémico y a la persistencia sobre exactamente las
mismas filas; y mantener la tasa de falsas alarmas dentro de un margen que la
secretaría pueda absorber.

### Qué hace esta aplicación

El tablero responde dos preguntas distintas y las separa en dos pestañas,
porque mezcladas en una sola página ninguna se leía entera.

**Qué municipios vigilar**, que es la pregunta de operación:

- el triaje del departamento: los municipios ordenados por riesgo estimado,
  con búsqueda, filtro por zona del canal y filtro de solo alertados;
- el detalle del municipio elegido, que arranca por la decisión —se emite o no
  se emite alerta— y deja la probabilidad como sustento, no como titular;
- la serie del municipio en casos divididos por el P75 de cada mes, de modo
  que el umbral queda fijo en 1,0 y dos municipios se pueden comparar;
- el pronóstico T+1 y T+2 con probabilidad, umbral aplicado y estado de alerta,
  en un panel con escala propia: el modelo estima con qué probabilidad se cruza
  un umbral, no cuántos casos habrá, y dibujarlo sobre la serie sugeriría una
  magnitud que nadie calculó;
- la representación territorial del departamento coloreada por alerta.

**Qué tan bien acierta**, que es la pregunta de confianza:

- el desempeño de cada candidato evaluado frente al **canal endémico**, que es
  la regla con la que hoy se vigila, y frente a la línea base que declaró la
  evaluación;
- un **retroanálisis de ventana expansiva** sobre 2018–2024, en su propia
  sección, que mide 647 brotes en siete años en vez de 86 en doce meses;
- el contexto histórico de desempeño del procedimiento evaluado.

### Qué no hace, y por qué

La API **no ejecuta inferencia en línea**. Sirve resultados ya calculados y
persistidos. Esto es deliberado y no una limitación de implementación: el
proyecto mantiene la compuerta G5 en `NOT_APPROVED` y el champion en
`NOT_SELECTED`, de modo que ningún modelo está autorizado todavía como sistema
operativo de alertas. El tablero lo declara en pantalla y la respuesta de la
API lo declara en su bloque `governance`. Mostrar predicciones calculadas al
vuelo daría a entender una autorización que el proyecto no ha otorgado.

---

## 2. Instrucciones de uso

El tablero se abre en el navegador y no requiere credenciales.

1. Elegir el departamento en las pestañas superiores: **Tolima** o **Meta**.
2. Elegir el municipio en el selector.
3. Elegir el periodo de referencia (mes T) en el selector de la derecha.

El selector de mes ofrece **solo los periodos que el servicio tiene
publicados**, que consulta en `/api/salud` al cargar. No es un calendario
abierto: así nadie llega por accidente a un mes sin datos.

Las tarjetas de pronóstico muestran la probabilidad estimada y el umbral
aplicado a ese horizonte. Un municipio puede aparecer como **No disponible**
cuando no hay historia suficiente, cuando no es elegible por el criterio de
endemicidad, o cuando el procedimiento no produjo resultado para ese periodo.
Esos estados se muestran de forma explícita en vez de rellenarse con ceros.

### La API directamente

```bash
# Qué es este servicio y qué rutas expone
curl http://<host>/

# Estado del servicio y qué resultados tiene cargados
curl http://<host>/api/salud

# Resultados de un departamento y periodo
curl "http://<host>/api/dashboard?department_code=73&period=2026-09"
```

`department_code` admite `73` (Tolima) y `50` (Meta). `period` usa formato
`AAAA-MM`.

El contrato completo está publicado en `/api/openapi.json` y se puede explorar
en `/api/docs`. Esa interfaz carga sus recursos desde un CDN público;
`SATD_EXPONER_DOCS=false` la apaga y deja el servicio sin esa dependencia.

---

## 3. Enlaces

| Recurso | Dirección |
| --- | --- |
| Aplicación desplegada | http://34.206.240.59 |
| Repositorio del despliegue | https://github.com/sramirezc2/sat-dengue-despliegue |
| Procedencia de los datos publicados | corrida `88e3ad9decce8bd4d`, evaluación congelada G5 |
| Bitácora experimental | [`docs/bitacora-experimental.md`](docs/bitacora-experimental.md) |
| Estado y secuencia de implementación | [`plan.md`](plan.md) |
| Diseño detallado del E2E | [`PLAN_pipeline_e2e_experimentos_sat_dengue.md`](PLAN_pipeline_e2e_experimentos_sat_dengue.md) |
| Arquitectura objetivo V3 y transición del pipeline E2E | [`docs/architecture/pipeline-e2e.md`](docs/architecture/pipeline-e2e.md) |
| Operación, recuperación y migraciones del pipeline | [Guía operativa](docs/operations/pipeline-operations.md) |
| Registro y ejecución de experimentos | [Manual de la fábrica](docs/experiments/manual_pipeline.md) |
| Contrato científico V3 | [Pregunta de grado y reglas de decisión](docs/experiments/contrato.md) |
| Capacidades reutilizables para agentes | [Catálogo de skills](docs/agents/skills-catalog.md) |
| Revisión científica y de seguridad | [Revisión científica](docs/reviews/scientific-review.md) · [Revisión de seguridad](docs/security/security-review.md) |
| Subproyecto Kedro y smoke test sintético | [`pipeline/README.md`](pipeline/README.md) |
| Propuesta de política de decisión v2 | [`docs/politica-de-decision-v2.md`](docs/politica-de-decision-v2.md) |
| Antecedente científico congelado | `SAT-Dengue-V2` (procedencia histórica, no fuente activa) |
| Informe de avance | entregado el 25 de octubre de 2026 |

---

## 4. Dependencias y entorno

### API

Python 3.12. Pines propios en `app/api/requirements.txt`; las dependencias
científicas se mantienen separadas en `pipeline/pyproject.toml` y nunca entran
en la imagen de la API.

| Paquete | Versión |
| --- | --- |
| fastapi | 0.161.0 |
| pydantic | 2.14.1 |
| uvicorn | 0.54.0 |
| boto3 | 1.42.6 |

### Tablero

Bun 1.4.4 para construir, Node 22 para ejecutar. Dependencias bloqueadas en
`app/dashboard/bun.lock`. React 19, TanStack Start y Router, Recharts para las
gráficas, Tailwind 4.

El proyecto se construye con el preset **`node_server`** de nitro. El preset por
defecto del código original es `cloudflare`, que produce un worker y no corre en
una instancia propia; el `Dockerfile.dashboard` fija la variable para evitarlo.

### Infraestructura

Docker y Docker Compose. Tres servicios: `api`, `dashboard` y `proxy`.

---

## 5. Reproducir el despliegue

### En local

```bash
git clone <repositorio>
cd sat-dengue-despliegue
cp .env.example .env            # ajustar PUERTO_PUBLICO si el 80 está ocupado
docker compose -f docker/docker-compose.yml --env-file .env up -d --build
```

La aplicación queda en `http://localhost:${PUERTO_PUBLICO}`. Sin bucket
declarado, el servicio usa los resultados versionados en `datos/resultados/`,
de modo que un clon limpio arranca sin depender de ningún servicio externo.

Comprobación:

```bash
./scripts/verificar_despliegue.sh http://localhost:8080
```

### En AWS Academy

El laboratorio **detiene las instancias EC2 al terminar la sesión** y las
vuelve a arrancar al iniciarla de nuevo. Dos consecuencias de diseño:

- la instancia lleva una **IP elástica**, para que la dirección no cambie entre
  apagados;
- los contenedores usan `restart: unless-stopped` y un servicio systemd, de
  modo que la aplicación vuelve sola sin intervención manual.

La instancia se configura sola. `scripts/arranque_instancia.sh` se pasa como
**user-data** al lanzarla: instala Docker y Compose, clona el repositorio,
escribe el `.env` con la región y la IP pública que lee del metadata service,
habilita el servicio systemd, construye las imágenes y espera a que
`/api/salud` responda antes de darse por terminado. No hace falta entrar por
SSH, que en AWS Academy suele estar cerrado.

```bash
aws ec2 run-instances \
  --image-id "$(aws ssm get-parameter \
      --name /aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64 \
      --query Parameter.Value --output text)" \
  --instance-type t3.small \
  --iam-instance-profile Name=LabInstanceProfile \
  --security-group-ids <grupo-con-el-puerto-80> \
  --user-data file://scripts/arranque_instancia.sh
```

El registro del arranque queda en la instancia en `/var/log/arranque-sat.log`.
Si algo falla, ahí está la causa.

Para actualizar un despliegue ya montado basta volver a ejecutar el mismo
script: detecta que el repositorio ya está clonado y hace `fetch` y `reset`.

El laboratorio **no** se usa para entrenar. Los créditos están destinados al
despliegue; el entrenamiento y la evaluación se ejecutan en el subproyecto
independiente `pipeline/`, fuera de los contenedores del producto.

---

## 6. Ejemplos de entrada y salida

### Entrada

La API es de solo lectura y su entrada son dos parámetros de consulta:

```
GET /api/dashboard?department_code=73&period=2026-09
```

La entrada del **sistema**, en cambio, son los resultados publicados: archivos
JSON en el directorio que declara `SATD_DIRECTORIO_RESULTADOS`, con la
convención de nombre `resultado_<departamento>_<AAAA-MM>.json`. Publicar un
periodo nuevo es dejar un archivo; no hay que editar código ni volver a
construir la imagen.

`scripts/construir_resultados.py` es la envoltura compatible del publicador de
`pipeline/`, que recibe panel, predicciones y comparación locales ya calculados.
Desde la raíz, con el entorno bloqueado:

```bash
uv run --project pipeline python scripts/construir_resultados.py \
  --panel       <corrida>/stages/data/<id>/bundle/panel.csv \
  --predicciones <corrida>/predictions.csv \
  --comparacion  <corrida>/comparison.csv \
  --procedimiento 88e3ad9decce8bd4d \
  --version-datos g5-frozen-2025 \
  --salida datos/resultados
```

El umbral de decisión no viene explícito en las corridas. El script lo recupera
del propio archivo de predicciones como la probabilidad más baja que sí emitió
alerta, y **falla** si las dos clases no quedan separadas, porque entonces el
umbral sería una invención. En la corrida publicada el margen de separación es
de 5,9e-04 en T+1 y 1,3e-03 en T+2.

Solo se publican los meses de referencia que tienen los dos horizontes. Un mes
con un solo horizonte dejaría la mitad del tablero en "no calculado" sin
aportar nada.

No lleva `--candidato`: cuál de los candidatos evaluados maneja la vista de
municipio lo decide un criterio escrito, no una bandera. La sección 14 lo
explica. El script publica además el desempeño de **todos** los candidatos de
`comparison.csv`, no solo el elegido, y calcula del panel la fila de referencia
del canal endémico.

### Salida

```json
{
  "metadata": {
    "reference_period": "2026-09",
    "data_version": "demo-data-2026-09-v1.1"
  },
  "governance": {
    "governance_gate": "G5",
    "governance_status": "NOT_APPROVED",
    "champion_status": "NOT_SELECTED"
  },
  "department": {
    "department_code": "73",
    "department_name": "Tolima",
    "requested_period": "2026-09"
  },
  "municipalities": [
    {
      "municipality_code": "73001",
      "municipality_name": "Ibagué",
      "cases_t": 48,
      "endemic_zone_t": "ALERTA",
      "p25": 22.0, "median": 35.0, "p75": 47.0,
      "results": [
        {
          "horizon": "T1",
          "target_period": "2026-10",
          "probability": 0.61,
          "threshold": 0.55,
          "alert_status": "ALERT",
          "availability_status": "AVAILABLE",
          "model_family": "xgboost",
          "model_role": "PROVISIONAL_CANDIDATE"
        }
      ]
    }
  ]
}
```

Respuesta de salud:

```json
{
  "servicio": "sat-dengue-api",
  "version": "1.0.0",
  "entorno": "produccion",
  "resultados_cargados": 2,
  "periodos_por_departamento": {"50": ["2026-12"], "73": ["2026-09"]},
  "origen_durable": null
}
```

### Errores

| Situación | Código | `error_code` |
| --- | --- | --- |
| Departamento no admitido | 400 | `INVALID_DEPARTMENT_CODE` |
| Periodo mal formado | 400 | `INVALID_PERIOD_FORMAT` |
| No hay resultado para esa combinación | 404 | `DASHBOARD_DATA_NOT_FOUND` |
| Resultado persistido inválido o inconsistente | 500 | `INTERNAL_ERROR` |
| Ruta que no existe | 404 | `NOT_FOUND` |
| Método distinto de GET | 405 | `METHOD_NOT_ALLOWED` |

Todas las respuestas de error usan la misma forma, `{"error_code", "message"}`,
también en las rutas que el contrato no cubre. Un cliente no tiene que
entender dos formatos.

---

## 7. Consideraciones del modelo

**Tamaño y hardware.** La aplicación desplegada no carga artefactos de modelo
ni ejecuta inferencia, así que no tiene requisitos de cómputo asociados al
modelo. La imagen de la API pesa alrededor de 180 MB y el servicio opera con
menos de 256 MB de memoria. Una instancia `t3.small` (2 vCPU, 2 GB) sostiene
los tres contenedores con holgura.

**Tiempos de respuesta.** La API lee el JSON del periodo solicitado y lo valida
contra el esquema en cada petición. Para Tolima, el departamento más grande con
47 municipios, el archivo pesa 64 KB y la respuesta se sirve en milisegundos.
No hay cola ni trabajo asíncrono.

**Tiempos del modelo, que ocurren fuera de esta aplicación.** El entrenamiento
y la evaluación histórica se ejecutaron sobre un panel mensual de
2007 a 2025 para los 76 municipios de Tolima y Meta. Las familias evaluadas son
gradient boosting sobre árboles (XGBoost y LightGBM), un modelo aditivo
generalizado y una regresión logística con penalización L2, cada una en los
horizontes T+1 y T+2. La evaluación final incluye remuestreo bootstrap con 2000
réplicas para los intervalos de sensibilidad sobre inicios y de tasa de falsas
alarmas.

**Estado científico.** Las seis combinaciones candidato-horizonte evaluadas
sobre el bloque congelado de 2025 quedaron en `does_not_meet` frente al criterio
de utilidad. Por eso G5 está en `NOT_APPROVED` y el champion en
`NOT_SELECTED`, y por eso cada resultado que sirve esta API viaja etiquetado
como `PROVISIONAL_CANDIDATE`. El tablero no es un sistema de alertas
autorizado: es la presentación trazable de resultados de evaluación.

---

## 8. Credenciales

La aplicación **no tiene autenticación** y no maneja credenciales de usuario.
No hay inicio de sesión, no hay datos personales y toda la información servida
es agregada a nivel municipal.

La única credencial que interviene es la de AWS para leer el bucket de
resultados, y no se escribe en ningún archivo del repositorio: en la instancia
EC2 la provee el **perfil de instancia** (`LabRole` en AWS Academy), de modo que
`boto3` la obtiene del metadata service. En local, dejar `SATD_BUCKET_S3` vacío
desactiva la sincronización y el servicio usa los resultados versionados.

---

## 9. Parametrización

Todo lo que cambia entre entornos está en variables de entorno, documentadas en
`.env.example`. Ninguna ruta, umbral, origen ni acceso está quemado en el
código.

| Variable | Qué controla | Valor por defecto |
| --- | --- | --- |
| `SATD_ENTORNO` | Etiqueta del entorno, visible en `/api/salud` | `local` |
| `SATD_NIVEL_LOG` | Nivel de registro | `info` |
| `SATD_NOMBRE_SERVICIO` | Nombre del servicio en la salud | `sat-dengue-api` |
| `SATD_DIRECTORIO_RESULTADOS` | Dónde busca los resultados publicados | `datos/resultados` |
| `SATD_DEPARTAMENTOS` | Códigos DANE servidos | `50,73` |
| `SATD_ORIGENES_CORS` | Lista explícita de orígenes; no admite comodín | `http://localhost:3000,http://localhost:5173` |
| `SATD_BUCKET_S3` | Bucket con los resultados durables; vacío lo desactiva | vacío |
| `SATD_PREFIJO_S3` | Prefijo dentro del bucket | `resultados/` |
| `SATD_SINCRONIZAR_AL_ARRANCAR` | Bajar resultados al iniciar | `true` |
| `SATD_ESPERA_S3_SEGUNDOS` | Tiempo máximo de la sincronización | `20` |
| `SATD_EXPONER_DOCS` | Publica `/api/docs` y `/api/openapi.json` | `true` |
| `SATD_CACHE_SEGUNDOS` | Vigencia del caché de un resultado publicado | `300` |
| `PUERTO_PUBLICO` | Puerto que expone el proxy | `80` |
| `VERSION_IMAGEN` | Etiqueta de las imágenes construidas | `local` |

El servicio **falla al arrancar** si `SATD_DEPARTAMENTOS` incluye un código que
el contrato no admite, si `SATD_ORIGENES_CORS` trae un comodín o si un valor
numérico no es válido. Es preferible no arrancar a arrancar mal.

---

## 10. Persistencia

En el despliegue anterior la aplicación devolvía 500 en las predicciones porque
la instancia arrancaba con el disco vacío y sin corridas cargadas. El disco era
efímero.

Aquí el disco local es una **caché**, no la fuente. El diseño tiene tres capas:

1. los resultados están **versionados en el repositorio**, así que un clon
   limpio ya arranca con datos;
2. el volumen con nombre `resultados` sobrevive al reinicio del contenedor y al
   apagado de la instancia;
3. si hay bucket declarado, al arrancar el servicio sincroniza desde S3. Cada
   objeto se descarga a un temporal, se valida con el contrato existente y
   reemplaza atómicamente la copia local, incluso si conserva el mismo tamaño.

Si la sincronización falla pero ya hay resultados locales, el servicio registra
la advertencia y arranca con la última copia conocida. Servir el dato anterior
es mejor que no responder.

La sincronización comprueba el tamaño remoto y la validez semántica del JSON.
El publicador local genera tamaños y SHA-256 en `.publication/manifest.json`
desde la tarea 14. La verificación de ese manifiesto durante sincronización S3
sigue pendiente; esta tarea no cambia el transporte remoto. Un ETag de S3 no se
trata como MD5 universal.

---

## 11. Estructura

```
.
├── app/
│   ├── api/
│   │   ├── sat_api/
│   │   │   ├── contrato/         # contrato read-only, reutilizado sin modificar
│   │   │   ├── configuracion.py  # parametrización por entorno
│   │   │   ├── repositorio.py    # índice sobre el directorio de resultados
│   │   │   ├── almacenamiento.py # recuperación desde S3
│   │   │   └── main.py           # composición, CORS, salud y esquema
│   │   ├── tests/
│   │   └── requirements.txt
│   └── dashboard/                # tablero TanStack Start
│       └── src/
│           ├── components/
│           │   ├── tabla-triaje.tsx       # municipios ordenados por riesgo
│           │   ├── detalle-municipio.tsx  # decisión, cifras y serie del elegido
│           │   └── comparacion-modelo.tsx # modelo contra canal y línea base
│           ├── lib/                       # contrato Zod y adaptador de vista
│           └── test/                      # contrato, adaptador e integración
├── pipeline/                     # Kedro, dominio, fábrica, pruebas y lock propios
├── .agents/skills/               # cuatro skills canónicas de operación y revisión
├── datos/resultados/            # resultados publicados, un JSON por periodo
├── docker/                      # Dockerfiles, compose y nginx
├── docs/
│   ├── bitacora-experimental.md    # registro de experimentos, métricas y decisiones
│   ├── agents/                      # catálogo de capacidades reutilizables
│   ├── experiments/                 # registro, manual, recetas y conclusiones
│   ├── operations/                  # guía operativa central
│   ├── reviews/ y security/         # revisiones científica y de seguridad
│   ├── politica-de-decision-v2.md  # propuesta de revisión de la compuerta G5
│   └── politica-de-decision-v2.json # la misma propuesta, legible por máquina
├── modelos/                     # artefactos de modelo
├── notebooks/                   # análisis y evaluación
└── scripts/                     # construcción de resultados, verificación y systemd
```

---

## 12. Pruebas

Dos suites, una por lado. Ambas corren sin levantar la aplicación.

```bash
# API: suite de la capa de despliegue
cd app/api && python -m pytest

# Tablero: suite de contrato, adaptador e integración
cd app/dashboard && bun run test
```

Las pruebas de la API cubren el índice del directorio de resultados, el
rechazo de configuraciones inválidas al arrancar, los códigos de error del
contrato, las cabeceras de caché y que un resultado corrupto devuelva 500 sin
filtrar detalles internos. Las del tablero leen **los mismos archivos de
`datos/resultados/` que sirve el despliegue**, no una copia: si el formato
cambia, las pruebas lo acusan.

Y la verificación de extremo a extremo, que es lo que hará el jurado:

```bash
./scripts/verificar_despliegue.sh http://localhost:8080
```

---

## 13. Decisiones de interfaz

El tablero no usa el aspecto por defecto de una librería de componentes. Seis
decisiones lo gobiernan: tres sobre qué pregunta responde cada pantalla y tres
sobre cómo se ve.

**Cada pestaña responde una pregunta.** Una versión anterior resolvía "cómo
está este municipio", de a uno, por un desplegable de 47 entradas. La pregunta
que una secretaría de salud tiene que resolver primero es otra: a cuáles de sus
municipios manda equipo este mes. El triaje responde esa y la vista de
municipio pasa a ser el detalle al que se entra desde ahí. La pregunta de
confianza —qué tan bien acierta el procedimiento— vive en su propia pestaña,
porque es de otra audiencia y de otro momento.

**La decisión va antes que la cifra.** El detalle del municipio abre con la
frase que hay que leer, "se emite alerta para noviembre de 2025", y la
probabilidad la sostiene. Antes la probabilidad era lo más grande de la
pantalla, y es justamente lo que peor se lee solo: no dice magnitud ni
duración, solo con qué probabilidad se cruza un umbral.

**Una escala, una cosa.** La serie del municipio va en casos divididos por el
P75 de ese mes y no en casos crudos, porque el P75 se mueve mes a mes y
municipio a municipio —en Ibagué va de 141 a 683 según el mes—, de modo que una
escala en casos aplasta el año entero para acomodar enero. En esa unidad el
umbral queda fijo en 1,0. El pronóstico va en un panel aparte con su propia
escala, a propósito: es una probabilidad, no un número de casos.

**El color tiene significado o no está.** La única escala cromática es la del
canal endémico: éxito, seguridad, alerta y exceso. Las superficies son grises
neutros, sin tinte, para que nada compita con esa escala. El acento frío de la
interfaz se usa en el foco, los enlaces y la pestaña activa, nunca para
rellenar un botón grande que pueda confundirse con un estado epidemiológico.

**Las cifras se leen en columna.** Toda probabilidad, umbral, conteo, código
DANE e identificador va en IBM Plex Mono con alineación tabular. Las fuentes
se empaquetan con la aplicación: el tablero se ve igual aunque la red de quien
lo abre bloquee recursos de terceros.

**Los controles no desaparecen.** Cuando una consulta no devuelve resultados,
el encabezado, las pestañas de departamento y los selectores siguen en
pantalla. Una versión anterior reemplazaba la aplicación entera por la tarjeta
de error y dejaba al usuario sin forma de elegir otro periodo; hay una prueba
de regresión que lo impide.

Los estados sin dato se nombran de forma distinta según la causa: *historia
insuficiente*, *no elegible*, *no calculado*, *datos faltantes*. No se rellenan
con ceros ni se colapsan en un guion, porque para vigilancia la diferencia
entre "no hay brote" y "no se pudo calcular" es justamente la que importa.

---

## 14. Procedencia de los resultados publicados

Los 22 archivos de `datos/resultados/` no son datos de ejemplo. Salen de la
evaluación histórica congelada identificada como la corrida
`88e3ad9decce8bd4d`, y cubren **once meses de referencia**, de diciembre de
2024 a octubre de 2025, para los 76 municipios de Tolima y Meta.

| Pieza | Origen |
| --- | --- |
| Casos observados y canal endémico (P25, mediana, P75, zona) | `stages/data/.../bundle/panel.csv` |
| Probabilidad calibrada y decisión por municipio, mes y horizonte | `predictions.csv` de la evaluación |
| Desempeño del procedimiento (AUROC, AP, Brier, falsas alertas, sensibilidad) | `comparison.csv` de la evaluación |
| Fila de referencia del canal endémico en la comparación | se calcula al publicar, sobre `panel.csv` |
| Retroanálisis de ventana expansiva 2018–2024 | `datos/retro/ventana_expansiva.json` |

Esa última fila es la única del bloque `comparison` que no sale de la corrida
evaluada, y por eso viaja marcada: `role: "REFERENCE"` y
`source: "computed_from_panel"`, contra `source: "evaluation_run"` de todas las
demás. Se calcula con la misma definición de canal que usa el proyecto —alerta
si los casos del mes de aviso superan el P75 del mes objetivo— y sobre
exactamente las mismas filas del panel que evaluaron a los modelos.

### Qué cuenta de casos se publica

Todo lo que el tablero muestra como "casos" es `dengue_notifications_count`, la
columna sobre la que el proyecto construye el canal endémico. No es
`total_notifications_count`, que es dengue más dengue grave.

La diferencia importa porque las bandas que el tablero dibuja se calculan sobre
la primera: en `channel_history.csv`, `current_count` coincide con
`dengue_notifications_count` en el **100 %** de las filas y con el total solo
en el **89 %**, y `zona_canal_t == "EXCESO"` equivale exactamente a que esa
columna supere el P75. Publicar el total contra esas bandas dejaba al tablero
diciendo dos cosas a la vez: en el periodo publicado había un municipio-mes
dibujado por encima de su P75 cuya zona no era exceso. Ahora la cifra del mes,
la serie de la gráfica, la zona y la fila de comparación hablan todas de la
misma cantidad, y esa incoherencia es cero en los 22 archivos.

El total notificado sigue en el panel para quien lo necesite; lo que no puede
es ir dibujado contra un canal que no lo usa. Está ahí porque la
línea base que declaró la evaluación es la persistencia, que en T+1 no puede
detectar ningún inicio por construcción: comparar contra ella sola hacía ver
bien al modelo por una razón ajena al modelo. La persistencia se conserva
publicada con el rol `BASELINE` y sus mismos números, porque es la línea base
que la gobernanza declaró.

### Qué candidato se publica, y por qué ese

La corrida evaluó tres familias y **la gobernanza no eligió ninguna**: el audit
dice `champion: not_selected` y deja las seis combinaciones candidato-horizonte
en `does_not_meet`. La compuerta G5 sigue en `NOT_APPROVED`. Elegir cuál de los
tres maneja la vista de municipio es, por lo tanto, una decisión de
publicación, y el script la toma con un criterio escrito en vez de con una
preferencia.

El criterio es el que el proyecto ya tenía desde su primera tanda de
experimentos: **anticipar más inicios de brote y que cada acierto cueste menos
falsas alarmas**. Se aplica sobre T+1, que es el horizonte que decide, se
descarta la línea base, y gana el candidato que **domina** a los demás —no
menos inicios y no más falsas por acierto, y estrictamente mejor en alguno—.
Si ninguno domina, gana el de mayor cobertura y el empate se rompe por costo.
Está en `elegir_candidato()` y el script imprime la razón al publicar.

En la corrida publicada gana **LightGBM**, que domina a los otros dos en T+1:
34 de 86 inicios anticipados a 6,4 falsas por acierto, contra 22 a 8,0 de
XGBoost y 20 a 7,5 del GAM.

**Qué cambia respecto de antes, y por qué no es un capricho.** El tablero
publicaba XGBoost. Esa elección tenía una razón, aunque no estuviera escrita:
XGBoost encabeza el ranking por **precisión promedio**, que es la métrica de
ranking de la política de decisión G5 —0,6757 contra 0,6689 de LightGBM, con
AUROC empatados en la tercera cifra—.

Hay dos problemas con eso. El primero es que esa misma política dice que el
ranking **solo ordena a los candidatos elegibles**, y ninguno lo fue: las seis
combinaciones quedaron en `does_not_meet`. Aplicar el ranking a un conjunto
vacío de elegibles es usarlo fuera de su alcance.

El segundo es más interesante y vale para el informe: **las dos reglas eligen
modelos distintos.** Por precisión promedio gana XGBoost; por el criterio de
utilidad —anticipar inicios, barato— gana LightGBM. Una métrica de ordenamiento
global y un criterio de decisión en un punto de operación no tienen por qué
coincidir, y acá no coinciden. El tablero existe para ayudar a decidir a qué
municipios mandar equipo, así que publica el que gana en utilidad, y deja el
otro visible en la comparación con sus cifras.

Pasar `--candidato <nombre>` anula el criterio, y el script avisa que eso hay
que justificarlo por escrito.

Nada de esto convierte al candidato publicado en un sistema autorizado: sigue
viajando con el rol `PROVISIONAL_CANDIDATE`, y el tablero presenta resultados
de evaluación trazables, no alertas operativas.

Una advertencia sobre la serie del canal: los casos de los meses posteriores al
de referencia se publican en nulo. En el mes T nadie los conoce todavía, y
mostrarlos convertiría el tablero en una vista retrospectiva disfrazada de
pronóstico. Los percentiles sí se conservan, porque se calculan con la historia
previa.

### El retroanálisis de ventana expansiva

El tablero publica una **segunda** evaluación, en su propia sección y nunca
mezclada con la anterior. La corrida congelada mide doce meses de 2025 con 86
brotes que empezaron; el retroanálisis mide **2018 a 2024 con 647**,
reentrenando cada año con toda la historia previa y prediciendo el año
siguiente. Son dos evaluaciones distintas, sobre periodos y filas distintos, y
sus cifras no se suman.

Existe porque doce meses no distinguen diferencias que siete años sí: la tasa
de exceso del panel va de 9,0 % en 2021 a 62,9 % en 2019, y concluir desde una
sola ventana es frágil.

Dos cosas van declaradas en pantalla y no en una nota al pie:

- **Su procedencia.** El campo `provenance` vale `experimental_harness`: lo
  produjo el banco de experimentación del proyecto y **no la tubería
  científica**. No es todavía un resultado del procedimiento evaluado y no
  cambia su estado de gobernanza. Que un tercero reproduzca la misma validación
  sobre la tubería real es el control que falta.
- **Que el bloque congelado de 2025 no se tocó.** El retroanálisis termina en
  2024. La medición contra ese bloque sigue siendo de un solo tiro y sigue sin
  hacerse.

El detalle metodológico y los resultados año por año están en la bitácora, en
la tanda 7, línea O.

### Alcance de la evaluación publicada

El proyecto ha producido más de una evaluación a lo largo de su desarrollo, con
ventanas temporales y conjuntos de municipios distintos. La que publica este
tablero es la del bloque congelado de 2025, sobre 76 municipios y con 86
inicios de brote evaluables.

Cada respuesta de la API declara el periodo evaluado y la geografía en su
bloque `evaluation_context`, de modo que las cifras que se ven en pantalla
siempre vienen con el alcance al que corresponden. Comparar resultados de
evaluaciones con ventanas distintas no es válido, y por eso el alcance viaja
con el dato y no en una nota al pie.
