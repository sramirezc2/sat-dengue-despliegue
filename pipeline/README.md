# Pipeline SAT DENGUE: esqueleto sintético

Subproyecto Kedro independiente del despliegue. Actualmente prueba cinco etapas
en memoria: generar observaciones artificiales, validarlas, ajustar una constante,
evaluarla y producir métricas. No es un modelo científico ni autoriza alertas.

Requisitos: Python 3.12 y uv (validado con 0.11.19). Dependencias fijadas en
`pyproject.toml` y resueltas en `uv.lock`: Kedro 1.7.0, pytest 9.2.0 y Ruff 0.17.4.
No se requieren AWS, credenciales, datos externos ni servicios desplegados.

Desde la raíz del repositorio:

```sh
uv lock --check --project pipeline
uv sync --locked --project pipeline
uv run --directory pipeline kedro run --pipeline synthetic
```

El comando único de ejecución es la última línea. `--directory pipeline` cambia
el directorio para que Kedro encuentre su `pyproject.toml`; `--project pipeline`
por sí solo selecciona el entorno de uv y no cambia el directorio del proceso.
El entorno vive en `pipeline/.venv/` y no altera las dependencias de API o tablero.
Kedro 1.7.0 todavía acepta `--pipeline`, aunque avisa que la opción se retirará
en una versión futura. También emite avisos internos de deprecación de OmegaConf.

Validaciones desde la raíz:

```sh
uv run --directory pipeline ruff check .
uv run --directory pipeline pytest
```

El fixture genera valores 2, 4, 6, 8 y 10 para 2020–2024. Ajusta la constante 5
sobre las primeras cuatro observaciones y comprueba la última: una observación,
MAE 5 y MSE 25. Esas métricas sintéticas se muestran en consola. El catálogo usa
solo `MemoryDataset`; nada se publica ni persiste. La configuración de logging
solo escribe a consola y `.telemetry` desactiva la telemetría de Kedro.

La instalación necesita acceso al índice de paquetes; la ejecución del smoke test
no usa red ni lee archivos reales del repositorio. Las comprobaciones del fixture
no sustituyen los controles temporales científicos de la tarea 7.

Quedan aplazados: `DataSource`, bundles y proveedores (tarea 5), migración de V2,
preparación científica, modelos definitivos, MLflow, DVC y publicación en
`datos/resultados/`. Los límites completos están en
[la arquitectura](../docs/architecture/pipeline-e2e.md).
