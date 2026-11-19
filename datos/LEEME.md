# Datos

Tres cosas distintas viven aquí y conviene no confundirlas: los **datos de
entrada** con los que se construye y evalúa todo (`panel/`), los **resultados
publicados** que sirve la aplicación (`resultados/`) y una **evaluación anual
auxiliar** que usa el tablero (`retro/`).

## `panel/` — el dato de entrada

`panel_meta_tolima.csv` es el panel canónico municipio-mes de Meta y Tolima:
76 municipios (47 de Tolima, 29 de Meta) por 216 meses, de enero de 2007 a
diciembre de 2024. Cada fila trae los conteos de notificación, las variables
climáticas del mes, los percentiles del canal endémico y los rezagos.

`esquema.json` acompaña al CSV y no se escribe a mano: lo produce el propio
constructor canónico. Dice el tipo, la nulabilidad, el rol y el origen de cada
columna, y en su bloque `panel` guarda la **huella semántica** del artefacto del
que salió el recorte. Un CSV no conserva tipos; el esquema es lo que permite
restaurarlos y lo que ata este archivo al artefacto certificado.

Se regenera con:

```sh
uv run --locked --directory pipeline python tools/exportar_entregable.py \
    <ruta/canonical.json> <huella_semantica>
```

### Por qué el panel y no los crudos

Las fuentes originales son microdato de notificación individual y no se publican
aquí: `dengue.csv` pesa 875 MB y el release vive detrás de token en Hugging Face.
Lo que sí está versionado es su manifiesto, en
`pipeline/conf/releases/approved-raw.json`, con el `sha256` de cada uno de los
cinco archivos y la revisión exacta del release. Con eso cualquiera puede
comprobar que los crudos de los que salió este panel son los declarados, aunque
no tenga acceso a descargarlos.

El panel, en cambio, son agregados municipio-mes. Publicarlo es lo que permite
que un tercero reproduzca el resultado principal del informe sin credenciales:
los cuadernos de `notebooks/` leen de aquí.

Las fuentes son SIVIGILA (eventos 210 y 220) vía Datos Abiertos Colombia,
ERA5-Land y CHIRPS vía Google Earth Engine, integradas por código DIVIPOLA.

## `resultados/` — lo que sirve la aplicación

Veinticuatro documentos JSON, uno por departamento y mes objetivo, con la
reproducción retrospectiva de 2025 en T+2: los ocho municipios priorizados de
cada mes. **No contienen probabilidades, umbrales, desenlaces reales de 2025 ni
métricas de acierto.** Son una reproducción retrospectiva, no una evaluación ni
una autorización de uso operativo.

## `retro/` — evaluación anual auxiliar

`ventana_expansiva.json` es una evaluación por ventana expansiva con
reentrenamiento anual, que el tablero usa como contexto histórico. Compara varios
candidatos (`vigente`, `vigente_mas_g`, el canal en tres variantes y la
persistencia) **sin imponer un presupuesto común de alertas**, y sobre todas las
filas con etiqueta.

Sus cifras **no son** las de la Tabla 2 del informe y no deben leerse como tales:
el informe mide sobre la cohorte evaluable —los municipios que no están en exceso
en el mes de origen— y obliga a los dos métodos a emitir el mismo número de
alertas por mes. Son dos preguntas distintas, y la del informe es la que decide
si una alerta llega a tiempo.
