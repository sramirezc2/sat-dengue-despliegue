# Resumen de la exploración nocturna del 10 al 11 de noviembre de 2026

> Tandas 14 a 33, líneas V a AO. Cada tanda tiene su archivo con la preinscripción
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
4. **El mecanismo de la tanda 11 se confirma**: sin log1p la logística pierde 43
   inicios en T+1, y el bloque G recupera la mayor parte (tanda 16).

## Lo que no funcionó (sin efecto o peor)

- Ensambles: logística + XGBoost (tanda 14) y entre logísticas (tanda 23).
- Regularización: C de 1 a 100 da igual; C = 0,01 empeora (tanda 16).
- Ventanas móviles de 3, 5 y 8 años (tanda 21).
- Formas del clima: recortes, log1p de la lluvia, C = 10 (tanda 22).
- Mes cíclico, con y sin clima (tanda 24).
- Un modelo por departamento: empeora (tanda 26).

## Lo que se acepta

- La logística mínima de cinco variables no pierde más de 5 puntos (tanda 17).

## Correcciones durante la noche

- **Tanda 33**: la primera versión calculó el presupuesto sobre las filas
  elegibles y concluyó que nada pasaba la barra. Se retiró y se recalculó sobre
  los 76 municipios por mes, que cambia la conclusión para T+2.
- Cuatro corridas se detuvieron por falta de memoria en el equipo y se relanzaron
  de a una.

## En curso o pendiente

- Tanda 18 (entrenamiento nacional), 27 (indicador de departamento), 28 (sin
  2020) y 31 (XGBoost de profundidad 2 con cinco semillas).
