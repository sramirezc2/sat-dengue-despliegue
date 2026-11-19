# Cuadernos

Dos cuadernos, los dos ejecutables desde un clon limpio de este repositorio. No
necesitan token, ni reconstruir el panel, ni reentrenar nada: leen el panel
publicado en `datos/panel/` y las predicciones versionadas en `docs/evidence/`.

| Cuaderno | Qué hace | Necesita |
| --- | --- | --- |
| `01-resultado-principal.ipynb` | Vuelve a calcular la Tabla 2 del informe y la curva de presupuesto de la Figura 2 | `datos/panel/`, `docs/evidence/reserva-2023-2024-t2/` |
| `02-panel-y-etiqueta.ipynb` | Describe el panel y caracteriza la etiqueta de inicio de brote | `datos/panel/` |

## Cómo correrlos

Desde la raíz del repositorio:

```sh
uv sync --locked --project pipeline
uv run --locked --project pipeline jupyter lab
```

Los cuadernos resuelven la raíz del repositorio por sí solos, así que funcionan
tanto si se abren desde `notebooks/` como desde la raíz.

Si solo quiere comprobar que siguen dando lo mismo, sin abrir Jupyter:

```sh
uv run --locked --project pipeline jupyter nbconvert --execute --inplace \
    notebooks/01-resultado-principal.ipynb notebooks/02-panel-y-etiqueta.ipynb
```

## Qué comprueba el primero

El cuaderno `01` no se limita a mostrar una tabla parecida a la del informe: la
celda 6 compara su resultado contra las cifras publicadas en
`docs/evidence/reserva-2023-2024-t2/reserva.csv`, que son las que produjo el
evaluador original en su momento, y **falla** si no coinciden. Esa es la razón
de ser del cuaderno: que la tabla central del artículo sea verificable por
alguien que no estuvo en el proyecto.

La función `boot`, que calcula el intervalo por bloques de mes, es copia literal
de `pipeline/tools/noche/veredicto.py`, con su semilla derivada de la celda. Se
copia en lugar de importarse porque ese archivo es un script que carga el panel
al importarlo. Unificar las dos implementaciones en el paquete queda pendiente;
mientras tanto, la comprobación de la celda 6 es lo que garantiza que coinciden.

## Dónde está el resto del trabajo

La construcción del panel, el retroanálisis completo y la fábrica de
experimentos viven en `pipeline/`, como pipelines de Kedro, no como cuadernos:
son el camino que produce los artefactos certificados y corren con sus propias
pruebas. La bitácora experimental, con la preinscripción y el resultado de cada
hipótesis —incluidas las negativas—, está en `docs/bitacora/`.
