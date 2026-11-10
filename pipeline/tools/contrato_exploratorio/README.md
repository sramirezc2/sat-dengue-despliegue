# Exploración bajo el contrato científico (tanda 10)

Herramientas exploratorias. No pasan por el registro de la fábrica, no generan evidencia y no cambian estados. Usan el motor de `experiment_run` (cinco roles fijos) y una copia local de la evaluación del contrato (`contrato_local.py`; la evaluación oficial de la fábrica es la del PR #3) sobre el panel canónico construido desde el manifiesto privado aprobado.

- `corrida.py <receta.yml> <desplazamiento> <salida.json>`: una corrida en Tolima y Meta. El desplazamiento 0 usa los roles de EXP001 (evaluación 2024); 1, 2 y 3 los mueven 12, 24 y 36 meses hacia atrás. En las cohortes antiguas, el entrenamiento se recorta a 2016-08, el primer mes con el canal de 5 años completo, y se declara su soporte real.
- `corrida_nacional.py`: igual, pero entrena con todo el país y evalúa el contrato solo en Tolima y Meta (§4.4).
- `analisis.py <carpeta> <salida.json>`: consolida las corridas. Incluye las cohortes combinadas con bootstrap por bloques de mes, el ensamble, los brotes sostenidos frente a picos, la sensibilidad a la meta y al presupuesto, la heterogeneidad, la comparación entre modelos y el presupuesto elegido en desarrollo.
- `recetas/`: las recetas probadas.

Se ejecuta desde `pipeline/`. `PANEL_DIR` indica la carpeta del panel canónico construido (por defecto `data/retro-real`; para el release 2007-2024, `data/canonical-2007`) y `PISO_TRAIN` el primer mes objetivo con variables completas (`2016-08` con el release histórico y `2012-03` con el de 2007). El resumen de resultados está en `docs/bitacora/tanda-10-contrato-resumen.csv`, y la interpretación en `docs/bitacora/tanda-10-retroanalisis.docx`.
