# EXP003 — Regresión logística sin clima con ventana expansiva (Tolima y Meta)

Tipo: `scientific`. Hipótesis: EXP003-H1. Estado: `PROPOSED`. Requiere revisión y aprobación de otra persona del equipo antes de ejecutarse.

## Pregunta
¿Una regresión logística L2 sin variables climáticas detecta más inicios de brote que el canal endémico fuera de exceso, emitiendo cada mes el mismo número de alertas, en Tolima y Meta, 2019-2024?

## Cambio respecto a la referencia
El candidato es `logistic_onset` v1 (C = 1, max_iter = 5000), sin las 9 variables de clima, con log1p de conteos y umbrales y estandarización aprendida en el entrenamiento. Protocolo `rolling_origin`: un reentrenamiento por mes de origen, de 2019-01 a 2024-12. Población: departamentos 50 (Meta) y 73 (Tolima).

## Datos y periodos
Manifiesto privado aprobado `satd-raw-a1a7f237`. Horizontes T+1 y T+2. Las etiquetas respetan una demora de 1 mes. 2025 queda fuera.

## Métricas y líneas base
Definiciones de la política v2: inicios detectados, falsas, carga por 100 municipio-mes e IC 95 % bootstrap por municipio. Líneas base: canal P75, canal ajustado y canal fuera de exceso (principal), además de las dos de la fábrica. Regla operativa: las mismas alertas por mes que el canal fuera de exceso.

## Criterio
- **POSITIVE:** en T+1, más inicios que el canal fuera de exceso con IC 95 % por encima de 0.
- **NEGATIVE:** IC por debajo de 0.
- **INCONCLUSIVE:** IC que incluye 0.

T+2 se reporta como informativo.

## Evidencia previa y límites
En la tanda 10 (retroanálisis con el mismo protocolo, fuera de la fábrica), T+1 dio 301 vs 280 y T+2 217 vs 179. La ventaja de T+1 viene sobre todo de brotes pequeños o de un solo mes; en los brotes sostenidos empata con el canal. No autoriza campeón ni uso operativo.
