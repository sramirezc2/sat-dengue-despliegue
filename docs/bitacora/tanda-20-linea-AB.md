# Tanda 20, línea AB — Ajustes de XGBoost sobre la base común

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **preinscrita, sin correr.** Se corre sobre la base común del
> retroanálisis: `canonical.mode=approved`, calendario y departamentos de
> `parameters_retroanalisis.yml` sin tocar, `conjunto.csv` reportado.

## Hipótesis

En la tanda 12 la logística le ganó al XGBoost del banco en todos los
presupuestos. Antes de concluir que la familia de árboles es peor hay que
descartar que sea esa configuración: 300 rondas, profundidad 4 y eta 0,05,
heredadas de la tanda 7 sin búsqueda. Si alguna variante razonable alcanza a la
logística, la conclusión es sobre la configuración y no sobre la familia.

Una nota que se descubrió al preparar esta tanda: el XGBoost del banco usa las
33 variables del contrato, **con clima**, mientras que la logística de
referencia es sin clima. La comparación de la tanda 12 mezcla familia y clima.

## Qué se corre

Contra el XGBoost del banco (semilla 53), una diferencia a la vez:

- profundidad 2 y profundidad 6;
- eta 0,1, y eta 0,02 con 600 rondas;
- profundidad 3 con 150 rondas;
- **sin clima**, con las mismas variables de la logística de referencia.

Para esta tanda la referencia de la sección de mejora es el XGBoost del banco, y
se reporta además cada variante contra la logística sin clima. Una variante que
supere al banco por pocos inicios no se declara mejor sin cinco semillas
(regla 9); si alguna se acerca a la logística, se corre con cinco semillas
antes de cerrar.

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
