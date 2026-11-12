# EXP004 — resultado técnico de la recuperación autorizada

Fecha: 12 de noviembre de 2026. **PASS de la recuperación y validación técnica**.
EXP004 continúa **RUNNING/PENDING**, scientific_conclusion NOT_APPROVED y
champion_status NOT_SELECTED, sin autorización operativa. Este resultado no
resuelve la ausencia de la curva completa en la evidencia de fábrica ni asigna
una conclusión científica.

Esta entrada es posterior al borrador de conclusiones y al diagnóstico del
primer intento. Los conserva byte a byte; no reescribe sus estados históricos.
La [autorización adicional](RECOVERY_AUTHORIZATION.md) permite una recuperación
local y una sola invocación adicional del retroanálisis, sin repetir la fábrica.

## Materialización local

Se reutilizaron exclusivamente los cinco archivos del release corregido
satd-raw-173d5856, desde la caché de experiments al inbox requerido. El destino
no existía; se reservó de forma exclusiva. Se rechazaron symlinks, inventarios
adicionales y destinos preexistentes. El resolver existente copió a temporales,
verificó tamaño/SHA-256 y promovió cada archivo mediante reemplazo atómico.

[Recibo de materialización](RECOVERY_MATERIALIZATION.json): cinco archivos,
2.621.954.146 bytes, cero descargas y ningún acceso a credenciales. Tamaños y
hashes del origen y destino se verificaron antes y después. El origen no cambió.
No se modificaron código, dependencias, receta R2, entorno o parámetros.

## Invocación adicional y archivos

```sh
uv run --locked --directory pipeline kedro run --pipeline retroanalisis --env exp004
```

Una invocación adicional, salida **0**, **15/15 nodos** completados en **724,7 s**.
Release, operational_full y certificado son los de la receta congelada.
[Registro operacional del segundo intento](RECOVERY_ATTEMPT_2.json).
El primer intento fallido y su diagnóstico permanecen intactos. No hubo ninguna
otra invocación de retroanálisis ni repetición de la fábrica.

Salida local ignorada por Git: `pipeline/data/retroanalisis/EXP004/run1/`.
Se conservaron exactamente los seis CSV:

| Archivo | Filas | SHA-256 |
|---|---:|---|
| resumen.csv | 80 | `a89171dc2dbc9d9c6d3e88ba2dc8fd089eae22c39fc040b83a2ddf2dfb019c28` |
| por_anio.csv | 140 | `b4b4747a8040b811fd51b49347a3536bfa221708fa535bf93715d78cf6a9ff7a` |
| curva.csv | 620 | `a38b1035f6b046881b6a3edf182f198262e570bf53b5d6f267300b10a9f25dfa` |
| omitidos.csv | 0 | `79aa87ddf2ea78dc6c10a83b25fdf0be7a2da4a189ddfd4c88023f94402e3099` |
| conjunto.csv | 1.630 | `9e303378d63e5d84b9ba6dfeb7aa7cf665b1777529dc126de3607e75c6ea727d` |
| predicciones.csv | 81.240 | `59e9e9e414a4a72d0d7e1c3f7c7d5eb55d53a1f9b0337625df1a03d7a42010cf` |

## Igualdad efectiva y controles temporales

[Validación completa](RECOVERY_VALIDATION.json), solo lectura de los CSV y del
canónico producido. Se verificaron 815 pares de folds (1.630 ajustes), sin folds
omitidos, para horizontes T+1/T+2 y semillas 7, 13, 31, 53, 101.

- Training keys, training labels, número de filas y conjuntos de predicción
  coinciden entre brazos en conjunto.csv, por horizonte, lectura, semilla y fold.
- Las claves efectivas de predicciones.csv coinciden entre brazos y sus digests
  reconstruidos coinciden con conjunto.csv. No hay claves duplicadas ni scores
  ausentes, infinitos o fuera de [0,1].
- Los digests de las etiquetas de evaluación coinciden entre brazos y con los
  desenlaces H5 reconstruidos desde el canónico, sin entrenar o recalibrar.
- La única lectura de este instrumento es **primaria**, verificada contra el
  estado conocido sin exceso en T. Los CSV no traen una columna reading; la
  auditoría identifica esa dimensión constante a partir de la cohorte efectiva.
  secondary_t2 no está declarada en el retroanálisis y no se añadió al recuperarlo.
  Su evaluación separada de fábrica permanece intacta.
- T+1: 82 orígenes por brazo/semilla, 2018-01–2024-10; objetivos
  2018-02–2024-11. T+2: 81 orígenes, 2018-01–2024-09; objetivos
  2018-03–2024-11. Ambos horizontes cubren años 2018–2024.
- Todas las etiquetas de entrenamiento están disponibles antes del origen.
  Orígenes, objetivos y disponibilidad de etiquetas terminan antes de 2025-01.
  El canónico termina en 2024-12 y coincide exactamente con fábrica/certificado:
  SHA-256 `b4562ba50def7a98dceede0b7e95feed0e799b4652939d8037f1604bef37a23d`.
- Los 1.630 resúmenes de pesos conservan las políticas aprobadas, referencia
  exclusiva de train, pesos positivos y media uno. No se guardan pesos por fila.
- Las bases y sus presupuestos de alertas coinciden entre brazos en resumen,
  por_anio y curva. Los seis hashes siguen iguales después de validar.

## Resumen descriptivo, sin decisión científica

Punto propio del retroanálisis frente a canal_fuera_exceso, con igual volumen
realizado por mes. Las cinco semillas coinciden exactamente; no se seleccionó
una ni se sumaron observaciones entre ellas.

| Horizonte | Inicios | Alertas por brazo | TP canal | TP uniforme | TP reciente | Reciente−uniforme |
|---|---:|---:|---:|---:|---:|---:|
| T+1 | 641 | 817 | 323 | 359 | 361 | +2 |
| T+2 | 459 | 1.158 | 207 | 253 | 251 | −2 |

Son resultados del instrumento descriptivo predeclarado, con ventanas y
presupuesto distintos a los de fábrica. No sustituyen la comparación contractual
de fábrica ni se mezclan con sus intervalos, cohortes, votos o veredictos.
Los intervalos presentes en resumen.csv comparan cada candidato con su base;
no son intervalos de reciente−uniforme. No se añade un criterio o análisis
confirmatorio posterior a observar los resultados.

curva.csv contiene la curva del **retroanálisis**. No incorpora la curva completa
que falta en el inventario de **fábrica**, no repara esa limitación y no autoriza
una conclusión científica, campeón o uso operativo. La recuperación termina con
el reporte técnico; el registro no se cierra y no se solicita otra ejecución.
