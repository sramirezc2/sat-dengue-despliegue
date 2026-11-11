# Tanda 13, línea U — Acercar el banco y el retroanálisis, una diferencia a la vez

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Línea reclamada por Stevan. Estado: **corrida 1 cerrada**; ver Resultados.

## El problema que hay que resolver

La tanda 12 dejó una distancia sin explicar. El banco de la línea O reportó
**388 inicios sin el bloque G y 467 con él**, a unas 1 830 alertas. El
retroanálisis, con los mismos hiperparámetros y sobre la base común, detecta
**515 y 519** a 1 866 alertas.

Esa distancia no se puede atribuir a nada todavía, porque banco y retroanálisis
difieren en tres cosas a la vez (ver `tanda-12-linea-T.md`):

1. **Insumos.** El banco arma su matriz desde el `features.csv` de un *replay*
   archivado: 29 variables, sin clima. El retroanálisis usa las 33 del contrato.
2. **Cadencia de reentrenamiento.** El banco reentrena **una vez al año**. El
   retroanálisis reentrena **en cada mes de origen**: 82 ajustes en vez de 7.
3. **Reparto de alertas.** El banco usa un cupo mensual (`top_cupo`,
   `MESES_CUPO = 12`). El retroanálisis iguala el volumen total contra el de la
   línea base y deja que el umbral decida dónde caen.

Mientras las tres estén juntas, **ninguna cifra del banco es comparable con
ninguna cifra del pipeline**, y eso incluye el veredicto sobre la línea G.

## Hipótesis

**La cadencia explica la mayor parte de la distancia.** Un modelo que reentrena
cada mes ve, en promedio, seis meses más de historia que uno que reentrena en
enero y se queda quieto todo el año, y reparte ese aprendizaje sobre los meses
en los que el brote está empezando. La cadencia es además la única de las tres
diferencias que no cambia ni los insumos ni la métrica: cambia cuántas veces se
mira.

## Qué se corre

Una sola diferencia a la vez, en este orden. Esta tanda cubre **solo la
primera**; las otras dos quedan preinscritas aquí pero se corren después y con
su propio cierre.

**Corrida 1 — cadencia.** El retroanálisis con reentrenamiento anual en vez de
mensual, sobre el mismo panel, el mismo calendario, las mismas filas y los
mismos presupuestos de la tanda 12. Dos brazos, con y sin el bloque G, y los dos
modelos del banco (`xgboost_banco.yml` y `xgboost_banco_g.yml`). Horizontes T+1
y T+2.

La implementación no puede tocar el contrato del arnés: la cadencia entra como
un corte de entrenamiento declarado que, cuando no se declara, deja los folds
byte a byte como están hoy.

## Qué métrica decide

Inicios detectados al presupuesto de alertas de cada línea base, sobre la base
común, igual que las tandas 11 y 12. Nada de AUROC ni de métricas nuevas.

## Qué contaría como respuesta, declarado antes de mirar

Sobre el brazo **sin** bloque en T+1, que hoy detecta 515 de 641 a 1 866
alertas, contra los 388 del banco. La distancia a explicar es de **127 inicios**.

- **La cadencia explica la distancia** si con reentrenamiento anual el brazo sin
  bloque baja a **452 o menos**, es decir al menos la mitad de la distancia.
- **La cadencia no la explica** si baja a **483 o más**, es decir menos de un
  cuarto.
- Entre 452 y 483 el resultado es **parcial**: se reporta como tal y se corre la
  segunda diferencia sin declarar nada sobre la primera.

Y por separado, sobre el aporte del bloque:

- **El aporte de G reaparece** si bajo cadencia anual el bloque suma **32
  inicios o más** (los 5 puntos de la sección 0 sobre 641) con la cota inferior
  del intervalo por encima de cero.
- **No reaparece** si suma menos, que es lo que ya midió la tanda 12 bajo
  cadencia mensual: entre −2 y +12.

## Qué contaría como fracaso de la tanda

Que el brazo sin bloque **suba** con reentrenamiento anual, o que la corrida no
produzca folds en algún horizonte. Lo primero invalidaría la hipótesis del
mecanismo y habría que decirlo así, no buscarle una explicación después.

## Qué no decide esta tanda

No decide sobre la línea G. G sigue **no reproducida** hasta que el banco
reproduzca, y esta tanda solo mide una de las tres diferencias que lo impiden.
Tampoco decide si el banco estaba bien o mal construido: decide cuánto de la
distancia explica la cadencia.

## Trampa conocida, anotada antes de caer en ella

Los 647 inicios coinciden entre banco y pipeline, y **eso no valida el
instrumento**: la etiqueta depende del panel, no del modelo ni del protocolo.
Coincidir en las etiquetas no es coincidir en la medición, y la tanda 12 estuvo
a punto de usar esa coincidencia como si lo fuera.

## Resultados

> Estado: **corrida 1 cerrada. La hipótesis se rechaza por su propio criterio.**

Mismas filas que las tandas 11 y 12 —7 612 en T+1 y 7 572 en T+2—, cero
orígenes omitidos, mismo panel y mismo calendario. Lo único que cambió es la
cadencia.

**El brazo sin bloque, en T+1 a 1 866 alertas: 515 con cadencia mensual, 520 con
cadencia anual.** El criterio declarado era bajar a 452 o menos para explicar la
distancia, y a 483 o más para no explicarla. No solo no bajó: **subió**, que es
exactamente la condición de fracaso que esta preinscripción había escrito.

Al presupuesto de cada línea base, T+1, inicios detectados:

| Brazo | Canal P75 (315) | Condicionado (817) | Ajustado (1 128) |
| --- | --- | --- | --- |
| Sin bloque, mensual | 160 | 328 | 385 |
| Sin bloque, anual | 156 | 325 | 376 |
| Con bloque, mensual | 169 | 340 | 391 |
| Con bloque, anual | 174 | 337 | 388 |

En T+2 el patrón es el mismo: sin bloque pasa de 106, 242 y 243 a 113, 241 y
242. Nada se mueve más allá del ruido, y lo poco que se mueve va en los dos
sentidos.

**Veredicto declarado: la cadencia no explica nada de los 127 inicios.** Siete
reentrenamientos al año producen prácticamente el mismo modelo que ochenta y
dos. Eso es un hallazgo por sí solo: la ventaja del retroanálisis sobre el banco
no viene de mirar más veces.

**Y el bloque G sigue sin reaparecer.** Bajo cadencia anual suma +12 inicios al
presupuesto del canal condicionado y +10 a 1 866 alertas, contra los **32 o más
con cota inferior sobre cero** que esta preinscripción exigía. Es el mismo orden
de magnitud que midió la tanda 12 bajo cadencia mensual.

## Qué sigue, y un cambio de orden declarado antes de correr

Quedan dos diferencias: los insumos (29 variables sin clima contra las 33 del
contrato) y el reparto de alertas (cupo mensual contra volumen igualado).

**Se cambia el orden declarado en esta preinscripción, y la razón se escribe
antes de medir:** la siguiente corrida es el **reparto de alertas**, no los
insumos. El motivo es mecánico. El cupo mensual del banco obliga a repartir las
alertas parejo entre los doce meses; el retroanálisis deja que el umbral las
concentre donde la probabilidad es alta, que es justamente donde el brote está
ocurriendo. Un instrumento que gasta el mismo número de alertas en un mes de
enero tranquilo que en el pico de la epidemia tiene que detectar menos inicios,
y esa pérdida crece con lo estacional que sea el fenómeno. Después de la tanda 6
sabemos que este lo es bastante.

Criterio, declarado igual que el anterior: el reparto explica la distancia si
imponer el cupo mensual baja el brazo sin bloque de 515 a **452 o menos** en
T+1 a 1 866 alertas; no la explica si queda en **483 o más**; en medio es
parcial. Si tampoco la explica, quedan los insumos, y si los insumos tampoco,
hay que volver a leer el script del banco buscando una cuarta diferencia que no
vimos.
