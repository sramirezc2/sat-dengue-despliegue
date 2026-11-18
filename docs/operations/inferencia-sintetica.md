# Inferencia con el paquete sintético local

El archivo local ignorado `pipeline/data/demo/package.json` contiene una
regresión logística sin clima ya ajustada con datos artificiales para T+2.
Incluye la preparación, los coeficientes y la historia municipal. El tablero
verifica su SHA-256 y calcula probabilidades de demostración en el navegador.

## Preparar el tablero

Desde la raíz, antes de iniciar el tablero o construir su imagen, copie el
**paquete sintético** a la ruta de recursos estáticos ignorada por Git:

```sh
install -D -m 0644 pipeline/data/demo/package.json app/dashboard/public/demo/logistica-t2.json
```

Si `install -D` no está disponible, cree `app/dashboard/public/demo/` y copie el
archivo allí con el nombre `logistica-t2.json`. El tablero sirve ese recurso en
`/demo/logistica-t2.json`. Use HTTPS o `localhost` para que el navegador pueda
verificar el hash. Todo visitante del tablero puede descargar el recurso, por
lo que esta ruta se reserva al paquete de demostración con datos artificiales.

Abra **Carga de demostración**, seleccione el CSV o Excel (o la muestra dummy)
y pulse **Calcular ranking T+2**. El tablero carga el modelo automáticamente y
procesa el archivo en el navegador. El paquete actual admite `2025-10` como mes
de referencia. El archivo debe incluir `INI_SIN`, `confirmados` y los códigos
`COD_DPTO_R` y `COD_MUN_R` o `municipality_code`. Los meses cargados sustituyen
las filas correspondientes de la historia sintética y asumen cero casos graves.
Los municipios sin historia suficiente quedan sin predicción.

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
