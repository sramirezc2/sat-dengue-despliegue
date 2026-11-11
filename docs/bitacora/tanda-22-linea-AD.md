# Tanda 22, línea AD — Qué parte del clima aporta

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **preinscrita, sin correr.** Se corre sobre la base común del
> retroanálisis: `canonical.mode=approved`, calendario y departamentos de
> `parameters_retroanalisis.yml` sin tocar, `conjunto.csv` reportado.

## Origen

Se escribe después de ver la tanda 15, y se declara así. En la tanda 15 el
clima sumó 12 inicios en T+1 (IC −4 a 28) y quedó a favor en los siete años, sin
llegar a la barra de mejora. Es la única señal consistente de la noche, y por eso
se prioriza esta tanda. Esa falta de ceguera se compensa con una regla fija: la
referencia de esta tanda es la **logística con clima** de la tanda 15, no la sin
clima, así que ninguna variante gana por repetir lo que el clima ya dio.

## Hipótesis

Si el clima aporta, debería aportar más con una forma mejor: menos variables
ruidosas, la lluvia en escala log, o sobre la versión mínima del modelo.

## Qué se corre

Contra la logística con clima, una diferencia a la vez:

- solo lluvia, temperatura y punto de rocío;
- todo el clima menos el viento;
- log1p en lluvia y escorrentía;
- C = 10;
- la logística mínima más las nueve variables de clima, contra la mínima sin clima.

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
