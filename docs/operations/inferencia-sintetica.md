# Inferencia retrospectiva T+2 desde el tablero

El tablero usa el ajuste logístico real de EXP314 para Meta y Tolima. El
historial y las nueve variables climáticas provienen del consolidado posterior
`satd-raw-173d5856`. La interfaz identifica el ranking como **Demo retrospectiva
con datos consolidados posteriores**.

## Preparar el paquete privado

Desde la raíz del repositorio:

```sh
uv run --locked --directory pipeline --with pydantic==2.14.3 \
  python -m sat_dengue_pipeline.experiment_management.inference_bundle \
  --experiment-id EXP314 --execution-id 87c361fd4c134b3086a606b68aad9d63
```

El ensamblador verifica el recibo de Kedro, la huella del ajuste y los archivos
locales del inbox. Genera `model.json`, `history.csv`, `climate.csv` y
`manifest.json` en `pipeline/data/inference/87c361fd4c134b3086a606b68aad9d63/retrospective/`.
El paquete preparado admite 59 meses, de febrero de 2021 a diciembre de 2025.

## Activar y probar

En desarrollo, instale las dependencias de la API en su entorno Python 3.12.
Desde la raíz, asigne a `SATD_INFERENCE_DIR` la ruta absoluta del paquete y
a `SATD_INFERENCE_MANIFEST_SHA256` la huella que devuelve el ensamblador.

```sh
python -m pip install -r app/api/requirements.txt
PYTHONPATH="$PWD/pipeline/src" python -m uvicorn sat_api.main:app --app-dir app/api \
  --host 127.0.0.1 --port 8000
```

Vite reenvía `/api` a la API con `API_PROXY_TARGET=http://127.0.0.1:8000`.
Consulte `GET /api/inferencia/t2` para ver el modelo y los meses habilitados.
El tablero envía los conteos agregados al mismo endpoint con `POST`.

En Compose, configure `SATD_INFERENCE_RELEASE_DIR` con la ruta absoluta del
paquete, `SATD_INFERENCE_MANIFEST_SHA256` con la misma huella y
`SATD_INFERENCE_GID` con el grupo autorizado a leer el paquete. Conceda a ese
grupo acceso al directorio y lectura a sus cuatro archivos. La API monta el
paquete en modo de solo lectura y lo verifica al arrancar.

```sh
docker compose -f docker/docker-compose.yml --env-file .env up -d --build --remove-orphans
```

Si el proxy ya estaba en ejecución, reinícielo para que lea el Nginx actualizado.
Si la respuesta de estado contiene `"model": null`, verifique ruta, permisos y
huella y reinicie la API. Los resultados publicados siguen disponibles.

Abra **Carga de demostración** y seleccione un CSV UTF-8 o XLSX de un solo mes,
de hasta 5 MB. Use `INI_SIN`, `confirmados` con 0 o 1 y los códigos de
residencia DIVIPOLA. La columna opcional `COD_EVE` permite distinguir dengue
(210) y dengue grave (220). El resumen muestra ceros explícitos, rechazos y
filas excluidas por cobertura. El archivo `datos/202510_ejemplo.xlsx` permite
probar el ranking y el mapa para diciembre de 2025. La opción **Cargar muestra
dummy** envía una entrada artificial al mismo ajuste entrenado.

## Herramienta de línea de comandos

Desde la raíz, para probar con predictores artificiales:

```sh
uv run --directory pipeline python tools/infer_synthetic_demo.py --example
```

La respuesta contiene `probability` y los predictores usados. Para usar otros
valores, copie el objeto `features` en un archivo JSON local y ejecútelo así:

```sh
uv run --directory pipeline python tools/infer_synthetic_demo.py --features /ruta/predictores.json
```

El JSON debe incluir exactamente los predictores mostrados en el ejemplo;
`zona_canal_t` acepta `EXITO`, `SEGURIDAD`, `ALERTA` o `EXCESO`. Los predictores
deben estar calculados antes de ejecutar la herramienta: esta no genera lags,
canal ni variables a partir de datos crudos. La salida es una probabilidad bruta,
sin umbral o decisión de alerta. El paquete no está versionado en Git; para
usarlo en otro entorno debe trasladarse mediante un canal apropiado.
