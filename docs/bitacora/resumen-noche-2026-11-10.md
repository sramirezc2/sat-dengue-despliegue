# Resumen de la exploración nocturna del 10 al 11 de noviembre de 2026

> Tandas 14 a 47, líneas V a BC. Cada tanda tiene su archivo con la preinscripción
> escrita antes de correr y su resultado. Este resumen se actualiza durante la noche.

## Cómo se midió

- Todo sobre la base común del retroanálisis de main (tanda 11): release
  `satd-raw-173d5856`, panel certificado `de49b11b…`, calendario y departamentos de
  `parameters_retroanalisis.yml` sin tocar.
- **La base reproduce la tanda 11 exactamente**: 7 612 y 7 572 filas comunes, 641
  y 459 inicios, y al presupuesto del canal condicionado 323 contra 347 en T+1 y
  207 contra 248 en T+2.
- Las corridas usan el mismo nodo del retroanálisis, llamado directamente sobre el
  panel ya construido para no reconstruirlo en cada corrida
  (`pipeline/tools/noche/correr.py`).
- Las comparaciones entre recetas son emparejadas: mismas alertas por mes de
  origen. Hasta la tanda 32, «5 %, 10 % y 20 %» en esas tablas son fracciones de
  las **filas elegibles** de cada mes (unas 49), no del presupuesto de la sección
  0.1. El veredicto de la sección 0, con el presupuesto sobre los 76 municipios
  por mes, está en la tanda 33.
- Opciones nuevas del retroanálisis, en el PR #6 (borrador, sin merge): puntaje
  por fila, entrenamiento nacional, ventana móvil, mes cíclico, indicador de
  departamento y exclusión de años del entrenamiento.

## Lo más importante

1. **Al presupuesto de referencia del 10 % (sección 0), en T+2 las cuatro
   logísticas pasan la barra de 5 puntos** (+5,9 a +7,2 pp, con la cota inferior
   del IC por bloques de mes entre 2,0 y 3,5), sin aumentar la carga. En **T+1
   ninguna** pasa; con clima se cumple A (+3,1 pp, IC 0,3 a 5,9). XGBoost queda en
   +4,7 en T+2 de media y solo una de cinco semillas pasa (tanda 33).
2. **El clima es la única señal consistente de la noche, y es de T+1 y de Meta.**
   Suma entre 12 y 15 inicios en T+1, a favor en seis de siete años (tandas 15 y
   22); sale casi todo de Meta (tanda 25), y solo aparece si el modelo entrena con
   los dos departamentos juntos (tanda 26). Con el remuestreo por bloques de mes
   excluye el cero en 3 de 8 celdas (tanda 32). Es chico, unos 2 puntos.
3. **La logística le gana a XGBoost con las cinco semillas** (−14 inicios de media
   en T+1), y la semilla 53 de la tanda 12 era la más favorable a XGBoost (tanda
   14). Ningún ajuste de XGBoost alcanza a la logística; cuanto más simple el
   árbol, más se le acerca (tanda 20).
4. **La ventaja de T+2 es consistente y desplegable.** Cada logística gana en cinco
   o seis de los siete años al 10 % (tanda 34). Con umbrales fijados con el año
   anterior, como los podría fijar una secretaría en enero, la logística con clima
   anticipa 169 inicios a dos meses con 557 alertas, frente a 141 con 601 del canal
   (tanda 41). En T+2 el canal emite 3,2 falsas alertas por acierto y el modelo 2,4
   (tanda 33).
5. **Dónde gana el modelo** (tanda 35): donde el canal no puede ver, municipios
   poco endémicos y filas con pocos casos frente al umbral; pierde 13 a 24 inicios
   donde el canal está seguro. Repartir el presupuesto entre los dos no ayuda
   (tanda 36). Con las dos listas juntas, la logística con clima avisa a uno o dos
   meses 353 de 641 inicios, frente a 327 del canal (tanda 37).
6. **Qué aprende** (tanda 39): es sobre todo el margen contra el umbral en escala
   log; del clima pesa el punto de rocío, con signo positivo.
7. **Robustez del resultado de T+2** (tandas 44, 45 y 25): al 10 % pasan la barra
   25 de las 36 recetas de la noche, todas las logísticas de un solo modelo con
   log1p; la ventaja aparece desde el 10 % y crece hasta unos 10 puntos al 30 %, y
   gana en los dos departamentos. En T+1 hace falta el 20 % (unas 15 alertas por
   mes) para pasar la barra, y solo con clima.
8. **Límites** (tanda 46): la mitad de los inicios no los anticipa nadie, y la mitad
   de esos arranca con cero casos en el mes de origen. Lo que el modelo gana y el
   canal no son, en buena parte, inicios desde cero casos.
9. **Probabilidades** (tanda 42): bien calibradas en los dos horizontes; se pueden
   presentar como riesgo.
10. **El mecanismo de la tanda 11 se confirma**: sin log1p la logística pierde 43
   inicios en T+1, y el bloque G recupera la mayor parte (tanda 16).

## Lo que no funcionó (sin efecto o peor)

- Ensambles: logística + XGBoost (tanda 14) y entre logísticas (tanda 23).
- Regularización: C de 1 a 100 da igual; C = 0,01 empeora (tanda 16).
- Ventanas móviles de 3, 5 y 8 años (tanda 21).
- Formas del clima: recortes, log1p de la lluvia, C = 10 (tanda 22).
- Mes cíclico, con y sin clima (tanda 24).
- Un modelo por departamento: empeora (tanda 26).
- Repartir el presupuesto entre el canal y el modelo (tanda 36, línea N sigue cerrada).
- Árboles más profundos o con más eta (tanda 20).

## Lo que se acepta

- La logística mínima de cinco variables no pierde más de 5 puntos (tanda 17).
- Contra el canal como ranking con cupo fijo, una línea base más débil que el
  condicionado, el modelo pasa la barra también en T+1 con clima (tanda 38); el
  veredicto que manda es el de la tanda 33.

## Correcciones durante la noche

- **Tanda 33**: la primera versión calculó el presupuesto sobre las filas
  elegibles y concluyó que nada pasaba la barra. Se retiró y se recalculó sobre
  los 76 municipios por mes, que cambia la conclusión para T+2.
- Cuatro corridas se detuvieron por falta de memoria en el equipo a las 22:30 y se
  relanzaron de a una. A las 23:49 se detuvo de nuevo toda la cola en serie (y la
  suite completa de pruebas del PR #6, que se había lanzado en paralelo); solo
  sobrevivió la nacional con clima. Las tandas 27, 28, 31, 40, 43, 48 y 49 quedan
  preinscritas y sin correr hasta relanzarlas.

## En curso o pendiente

- Lecturas sin modelo nuevo: estacionalidad (tanda 47, sin época que concentre la
  ventaja).
- **EXP003 no se preparó**: la skill del experimento exige detenerse si el contrato
  sigue en propuesta, y el de main es la versión 0.2.2-propuesta.
- Tanda 18 (entrenamiento nacional, en curso), 27 (indicador de departamento),
  28 (sin 2020), 31 (XGBoost de profundidad 2 con cinco semillas) y 40 (punto de
  rocío como único clima), en cola en serie.

## Cómo reproducir

- Código: el PR #6 (`retroanalisis/opciones-exploracion`) trae las opciones del
  retroanálisis; las herramientas y recetas están en la rama
  `exploracion/herramientas-noche` (`pipeline/tools/noche/` y
  `pipeline/conf/retroanalisis/noche/`).
- Panel: el canónico del release `satd-raw-173d5856` con digest semántico
  `de49b11b…`, el mismo del certificado de la tarea 27. `correr.py` lo lee de
  `data/noche_panel/<digest>/canonical.json`.
- Una receta: desde `pipeline/`,
  `python tools/noche/correr.py <parametros.yml> "configuraciones=[<receta.yml>]" "salida=data/noche/<lote>"`,
  con los parámetros de `conf/base/parameters_retroanalisis.yml` (calendario y
  departamentos sin tocar).
- Comparar dos recetas: `python tools/noche/comparar.py <carpeta> <referencia> [recetas]`
  y `tabla_md.py` para la tabla.
- Veredicto de la sección 0: `python tools/noche/veredicto.py <carpeta> <recetas>`.
