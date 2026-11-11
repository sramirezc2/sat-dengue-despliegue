# Tanda 63, línea BS — Dónde gana el modelo, en la reserva

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **cerrada** el 11 de noviembre de 2026. Se corre sobre la base común del
> retroanálisis: `canonical.mode=approved`, calendario y departamentos de
> `parameters_retroanalisis.yml` sin tocar, `conjunto.csv` reportado.

## Hipótesis

Si los patrones de las tandas 35, 42 y 46 (el modelo gana en municipios poco
endémicos y en inicios desde cero casos, y está bien calibrado) se mantienen en la
reserva 2023-2024, son propiedades del modelo y no de los años de búsqueda.

## Qué se corre

Ningún modelo nuevo. Sobre 2023-2024, al 10 %, logística con clima: la lectura por
tercios de endemicidad de la tanda 35 (cortes fijados con todos los años, como allá),
los inicios desde cero casos de la tanda 46 y la calibración por deciles de la tanda
42.

## Qué no decide

Es una lectura de la reserva; con dos años, ningún tercio se interpreta solo.

## Resultado: dónde gana se mantiene; la calibración no

Reserva 2023-2024:

- T+1 reserva endemicidad bajo: inicios 93 canal 33 modelo 40
- T+1 reserva endemicidad medio: inicios 75 canal 43 modelo 38
- T+1 reserva endemicidad alto: inicios 56 canal 22 modelo 25
- T+1 reserva desde cero casos: 58 inicios, canal 0, modelo 10
- T+1 reserva calibración: media predicha 0.225 observada 0.272; decil alto 0.66/0.66; decil 9 0.43/0.51
- T+2 reserva endemicidad bajo: inicios 61 canal 19 modelo 31
- T+2 reserva endemicidad medio: inicios 42 canal 21 modelo 18
- T+2 reserva endemicidad alto: inicios 44 canal 17 modelo 21
- T+2 reserva desde cero casos: 43 inicios, canal 0, modelo 15
- T+2 reserva calibración: media predicha 0.129 observada 0.176; decil alto 0.40/0.45; decil 9 0.21/0.30

- **Dónde gana se mantiene en la reserva**: en municipios poco endémicos el modelo
  detecta más (40 frente a 33 en T+1; 31 frente a 19 en T+2), y en los medios empata
  o pierde un poco, como en la tanda 35.
- **Los inicios desde cero casos también**: el canal no anticipa ninguno, y el modelo
  10 de 58 en T+1 y 15 de 43 en T+2.
- **La calibración no se sostiene**: en la reserva el modelo **subestima** el riesgo,
  predice 0,23 donde se observa 0,27 en T+1 y 0,13 donde se observa 0,18 en T+2. El
  orden sí sirve (el decil alto queda en 0,66/0,66), pero el nivel depende de la
  frecuencia de inicios del año, que en 2023-2024 fue alta. Esto **corrige la lectura
  de la tanda 42**, que lo daba por calibrado con los siete años juntos.

Logística con clima y canal condicionado al 10 % de la sección 0, reserva 2023-2024; tercios de endemicidad con los cortes de los siete años; predicciones de la tanda 15, sin modelos nuevos.
