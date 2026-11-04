# SAT Dengue, despliegue del tablero de alerta temprana

Sistema de alerta temprana de brotes de dengue para los municipios de **Tolima
y Meta**. Este repositorio contiene la aplicación desplegada: la API que sirve
los resultados del modelo y el tablero que los presenta.

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

El tablero presenta, por departamento y periodo de referencia:

- la situación observada del mes y la zona del canal endémico de cada municipio;
- el pronóstico T+1 y T+2 con probabilidad, umbral aplicado y estado de alerta;
- el canal endémico del municipio seleccionado a lo largo del año;
- la representación territorial del departamento coloreada por alerta;
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
| Repositorio del despliegue | este repositorio |
| Procedencia de los datos publicados | corrida `88e3ad9decce8bd4d`, evaluación congelada G5 |
| Aplicación desplegada | se publica al crear la instancia, antes de la revisión |
| Repositorio científico (pipelines, notebooks, evidencia) | `SAT-Dengue-V2` |
| Informe de avance | entregado el 25 de octubre de 2026 |

---

## 4. Dependencias y entorno

### API

Python 3.12. Pines en `app/api/requirements.txt`, alineados con el
`pyproject.toml` del repositorio científico para que el contrato se comporte
igual en los dos lados.

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
despliegue; el entrenamiento y la evaluación corren en el repositorio
científico.

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

Esos archivos se generan con `scripts/construir_resultados.py` a partir de las
corridas de Kedro del repositorio científico:

```bash
python scripts/construir_resultados.py \
  --panel       <corrida>/stages/data/<id>/bundle/panel.csv \
  --predicciones <corrida>/predictions.csv \
  --comparacion  <corrida>/comparison.csv \
  --candidato xgboost \
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
y la evaluación corren en el repositorio científico sobre un panel mensual de
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
3. si hay bucket declarado, al arrancar el servicio sincroniza desde S3 y
   descarga solo lo que falta o cambió de tamaño.

Si la sincronización falla pero ya hay resultados locales, el servicio registra
la advertencia y arranca con la última copia conocida. Servir el dato anterior
es mejor que no responder.

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
├── datos/resultados/            # resultados publicados, un JSON por periodo
├── docker/                      # Dockerfiles, compose y nginx
├── modelos/                     # artefactos de modelo
├── notebooks/                   # análisis y evaluación
└── scripts/                     # construcción de resultados, verificación y systemd
```

---

## 12. Pruebas

Dos suites, una por lado. Ambas corren sin levantar la aplicación.

```bash
# API: 22 pruebas sobre la capa de despliegue
cd app/api && python -m pytest

# Tablero: 24 pruebas de contrato, adaptador e integración
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

El tablero no usa el aspecto por defecto de una librería de componentes. Tres
decisiones lo gobiernan.

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
evaluación congelada que el repositorio científico identifica como la corrida
`88e3ad9decce8bd4d`, y cubren **once meses de referencia**, de diciembre de
2024 a octubre de 2025, para los 76 municipios de Tolima y Meta.

| Pieza | Origen |
| --- | --- |
| Casos observados y canal endémico (P25, mediana, P75, zona) | `stages/data/.../bundle/panel.csv` |
| Probabilidad calibrada y decisión por municipio, mes y horizonte | `predictions.csv` de la evaluación |
| Desempeño del procedimiento (AUROC, AP, Brier, falsas alertas, sensibilidad) | `comparison.csv` de la evaluación |

El candidato publicado es **XGBoost**, con el rol `PROVISIONAL_CANDIDATE` que
le asigna la gobernanza del proyecto. La compuerta G5 sigue en `NOT_APPROVED` y
no hay champion seleccionado, de modo que el tablero presenta resultados de
evaluación trazables y no alertas operativas autorizadas.

Una advertencia sobre la serie del canal: los casos de los meses posteriores al
de referencia se publican en nulo. En el mes T nadie los conoce todavía, y
mostrarlos convertiría el tablero en una vista retrospectiva disfrazada de
pronóstico. Los percentiles sí se conservan, porque se calculan con la historia
previa.

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
