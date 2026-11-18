# Comparación de familias sobre las mismas filas (tanda 58)

Logística con clima (`log_conclima`), logística sin clima (`logistica_sin_clima`), XGBoost del banco (`xgb_banco`, 300 árboles de profundidad 4, con clima) y XGBoost simple sin clima (`xgb_d2_sinclima`, profundidad 2). Cada XGBoost se corrió con cinco semillas: 7, 13, 29, 42 y 53. Cada modelo se compara contra el canal condicionado con el mismo presupuesto del 10 %, y T+1 y T+2 van por separado. No se reentrenó nada.

## Archivo de predicciones

- Es `data/noche/t58/predicciones.csv`, el mismo de `../reserva-2023-2024-t2/`. Pesa 62 MB y no se sube al repositorio.
- SHA-256: `705f463cac9a0509afdd82f22cdc27790755f61a96ea17a822308a176f607170`
- Cada receta tiene 8124 filas: 4082 en T+1 y 4042 en T+2, con orígenes de 2018 a 2024.

## Periodos evaluados (por año del mes objetivo)

- **2018-2024:** completo.
- **2018-2022:** selección.
- **2023-2024:** reserva.

2025 no entra.

## Archivos

- `comparacion_familias.csv`: una fila por periodo, horizonte y receta. Columnas principales:
  - `objetivo`: alertas del presupuesto, 10 % x 76 x meses de origen.
  - `alertas` y `alertas_mes`: alertas efectivas, iguales para el canal y para el modelo.
  - `f`: el factor del canal elegido.
  - `inicios`, `canal` y `modelo`: inicios evaluables y cuántos anticipa cada uno.
  - `dif_pp` e `ic_mes_pp`: diferencia en puntos e intervalo por bloques de mes (2000 réplicas, semilla por celda).
  - `dif_carga` e `ic_carga`: diferencia en carga de falsas alertas por 100 municipio-mes.
  - `A`, `barra_5pp` y `C`: condiciones de la sección 0.
- `rango_por_familia.csv`: para XGBoost, el mínimo y el máximo entre las cinco semillas de inicios anticipados, de la diferencia en puntos y de la cota inferior del intervalo, y cuántas semillas cumplen la barra.
- `comprobacion_claves_etiquetas.csv`: muestra, por receta y horizonte, que todas usan las mismas claves (municipio, origen) y las mismas etiquetas de inicio. Las tres huellas son iguales en todas las recetas.

## Comandos

Se corren desde `pipeline/`, con `PYTHONPATH=src` y el panel certificado `de49b11b...` en `data/noche_panel/`. `veredicto_anios.py` está en `../reserva-2023-2024-t2/`. La carpeta `data/noche/comp4` contiene solo una copia de `data/noche/t58/predicciones.csv`.

```
R="log_conclima logistica_sin_clima xgb_banco_s7 xgb_banco_s13 xgb_banco_s29 xgb_banco_s42 xgb_banco_s53 xgb_d2_sinclima_s7 xgb_d2_sinclima_s13 xgb_d2_sinclima_s29 xgb_d2_sinclima_s42 xgb_d2_sinclima_s53"
python claves_etiquetas.py data/noche/t58/predicciones.csv $R
ANIOS=2018,2019,2020,2021,2022,2023,2024 FRACS=0.10 SALIDA=v_completo.csv  python veredicto_anios.py data/noche/comp4 $R
ANIOS=2018,2019,2020,2021,2022           FRACS=0.10 SALIDA=v_seleccion.csv python veredicto_anios.py data/noche/comp4 $R
ANIOS=2023,2024                          FRACS=0.10 SALIDA=v_reserva.csv   python veredicto_anios.py data/noche/comp4 $R
python tabla_familias.py data/noche/comp4
```

Con `ANIOS` en 2018-2024, el evaluador da lo mismo que `veredicto.py` de main. La logística con clima reproduce las cifras ya publicadas:
- 2018-2024: T+1 +3.1 (0.3 a 5.9) y T+2 +7.2 (3.3 a 11.1).
- 2023-2024: T+2 +8.8 (1.4 a 16.3).
