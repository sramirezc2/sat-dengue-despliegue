# Tanda 23, línea AE — Ensambles entre logísticas

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **preinscrita, sin correr.** Se corre sobre la base común del
> retroanálisis: `canonical.mode=approved`, calendario y departamentos de
> `parameters_retroanalisis.yml` sin tocar, `conjunto.csv` reportado.

## Origen

Se escribe después de ver la tanda 15 y se declara así: la logística con clima
quedó a favor en seis de siete años sin llegar a la barra. Un ensamble con la sin
clima podría conservar lo mejor de cada una.

## Hipótesis

Promediar los rangos de dos logísticas que difieren solo en el clima no debería
aportar casi nada, porque ordenan casi igual. Esta tanda sirve de **control** para
la tanda 14: si un ensamble de dos modelos casi idénticos ya «mejora», la mejora
de un ensamble con XGBoost habría que leerla con cuidado.

## Qué se corre

Con `tools/noche/ensamble.py` sobre las predicciones ya guardadas de la tanda 15:
promedio de rangos percentiles dentro de cada mes de origen entre la logística
sin clima y la logística con clima, y entre la sin clima y la mínima. La
referencia es la logística sin clima; el ensamble se compara también contra la
logística con clima.

## Qué métrica decide

Inicios detectados al presupuesto de alertas de cada línea base (canal P75,
condicionado y ajustado), sobre la base común y las mismas filas, igual que las
tandas 11 y 12. El brazo de referencia es `logistica_sin_clima.yml` corrido **en
la misma corrida**. Se publican también el resumen por año y la curva.

## Qué contaría como mejora, declarado antes de mirar

Al presupuesto del canal condicionado, por horizonte:

- **Mejora** si el brazo suma al menos 5 puntos de inicios sobre la referencia
  (32 de 641 en T+1, 23 de 459 en T+2) y la cota inferior del intervalo
  emparejado queda por encima de cero.
- **Sin efecto** si la diferencia está dentro de ±5 puntos o el intervalo cruza
  el cero. Una diferencia de uno o dos inicios no se reporta como hallazgo
  (regla 9).
- **Empeora** si resta al menos 5 puntos con la cota superior por debajo de cero.

Se exige además consistencia entre años (regla 3) y se declara el número de
inicios por año; ningún año con menos de 30 inicios decide nada (regla 4).

## Qué no decide

No decide sobre la meta del contrato ni registra nada en la fábrica. Es
exploración sobre la base común; lo que sobreviva se propone como experimento
registrado.
