# Tanda 12, línea T — G sobre el modelo del banco

> Entrada detallada. El resumen y el enlace están en
> [la bitácora principal](../bitacora-experimental.md), sección 5.

**Preinscrito en la tanda 11:** correr la misma comparación con XGBoost, que es
donde G ganó su confirmación, sobre la base común y las mismas filas. Decide lo
mismo que decidió la tanda 5: inicios detectados al mismo presupuesto.

**El modelo no es EXP001.** La receta XGBoost registrada de la fábrica es de
cuatro rondas y profundidad 2; el modelo del banco, el que produjo el 388 → 467,
está en `experimentos/tanda_07/origen_movil.py` y es `n_estimators=300`,
`max_depth=4`, `learning_rate=0.05`, `subsample=0.8`, `colsample_bytree=0.8`.
Correr EXP001 habría medido otra cosa y la habríamos llamado «G sobre XGBoost».
Las recetas `xgboost_banco.yml` y `xgboost_banco_g.yml` citan esa procedencia en
su encabezado.

#### Resultado: el bloque mueve unos pocos inicios, en los dos sentidos

Mismas filas que la tanda 11 —7 612 en T+1 y 7 572 en T+2—, cero orígenes
omitidos. Inicios detectados al presupuesto de cada línea base:

| T+1, 641 inicios | Alertas | Canal | XGBoost | XGBoost + G | Efecto de G |
| --- | --- | --- | --- | --- | --- |
| Canal P75 | 315 | 177 | 160 | 169 | +9 |
| Canal condicionado | 817 | 323 | 328 | 340 | +12 |
| Canal ajustado | 1 128 | 360 | 385 | 391 | +6 |

| T+2, 459 inicios | Alertas | Canal | XGBoost | XGBoost + G | Efecto de G |
| --- | --- | --- | --- | --- | --- |
| Canal P75 | 378 | 99 | 106 | 111 | +5 |
| Canal ajustado | 1 147 | 206 | 242 | 240 | −2 |
| Canal condicionado | 1 158 | 207 | 243 | 241 | −2 |

El efecto va de −2 a +12 sobre 641 y 459, con intervalos que se solapan en casi
todas las celdas. A lo largo de toda la curva de alertas el patrón es el mismo:
a 1 866 alertas en T+1, 515 inicios sin el bloque y 519 con él.

**G sí ayuda más a los árboles que a la logística** —+12 contra +2 al presupuesto
del canal condicionado—, que es exactamente lo que predijo el mecanismo medido en
la tanda 11. Pero el tamaño del efecto no alcanza para nada: no llega a la barra
de la sección 0 en ninguna celda, y ni siquiera recupera lo que la logística
consigue sin bloque.

#### Comparación entre familias, al mismo presupuesto y sobre las mismas filas

| T+1, 641 inicios | 315 alertas | 817 alertas | 1 128 alertas |
| --- | --- | --- | --- |
| Canal | 177 | 323 | 360 |
| Logística sin clima | **176** | **347** | 391 |
| Logística + G | 176 | 349 | 396 |
| XGBoost del banco | 160 | 328 | 385 |
| XGBoost + G | 169 | 340 | 391 |

**La logística le gana a XGBoost en todos los presupuestos**, con bloque o sin
él. La configuración vigente declarada tras la tanda 5 —XGBoost con el bloque G—
es, sobre la base común, la peor de las cuatro en dos de los tres presupuestos.

#### El banco y el retroanálisis no son el mismo instrumento

El banco reportó 388 inicios sin el bloque y 467 con él, a unas 1 830 alertas.
Sobre la base común, con los mismos hiperparámetros, el mismo modelo detecta 515
sin el bloque y 519 con él a 1 866 alertas.

**Esa comparación de totales no está autorizada**, y conviene decirlo antes de
que alguien la cite. Leyendo `experimentos/tanda_07/origen_movil.py`, el banco y
el retroanálisis difieren en tres cosas estructurales, no solo en el bloque:

1. **Los insumos.** El banco arma su matriz desde la preparación de un *replay*
   (`features.csv` de una corrida archivada), no desde el panel canónico. Son
   29 variables contra las 33 del contrato, y el clima está entre las que
   faltan.
2. **La cadencia de reentrenamiento.** El banco reentrena **una vez al año** y
   evalúa el año completo. El retroanálisis reentrena **en cada mes de origen**.
3. **Cómo se reparten las alertas.** El banco usa un cupo mensual (`top_cupo`
   sobre los primeros del mes), así que sus 1 830 alertas están repartidas doce
   por doce. El retroanálisis iguala el volumen total contra el de la línea base
   y deja que el umbral decida dónde caen.

Con tres diferencias así, atribuir los 127 inicios de distancia a cualquiera de
ellas sería inventar. Lo que sí queda establecido, y es lo que importa:

**Dentro del mismo instrumento, sobre las mismas filas y los mismos folds, el
bloque G mueve entre −2 y +12 inicios. La diferencia de +79 que reportó la tanda
7 no aparece.** Eso no dice que la tanda 7 estuviera mal; dice que su resultado
está atado a su instrumento y que no sobrevive al cambio de instrumento, que es
precisamente lo que un banco de evaluación debería haber garantizado.

#### Veredicto y lo que queda preinscrito

La línea G pasa a **no reproducida sobre la base común**, en las dos familias.
No se cierra: cerrar una línea exige haber medido lo que se quería medir, y aquí
el instrumento que la confirmó y el que la desmiente no son el mismo.

Queda preinscrito, en este orden:

1. **Acercar los dos instrumentos, una diferencia a la vez.** Son tres y están
   enumeradas arriba. La más barata de probar es la cadencia: correr el
   retroanálisis con reentrenamiento anual en vez de mensual. La segunda, el
   conjunto de variables. La tercera, el reparto de alertas por cupo mensual.
   Mientras las tres estén juntas, ninguna cifra del banco es comparable con
   ninguna cifra del pipeline, y eso incluye los 647 inicios, que sí coinciden
   pero por una razón que no depende del modelo.
2. **Solo después, volver sobre G.** Si al acercar los instrumentos el aporte
   del bloque reaparece, la línea se sostiene con una condición declarada; si no
   reaparece, G se reporta como medida en un instrumento que no reproducimos, y
   el informe lo dice así.

#### Lección de método

La tanda 7 declaró a G confirmada «con mucha más evidencia» porque el banco daba
ocho veces más señal que los tres cortes. Era cierto que daba más señal. Lo que
nunca se verificó es que midiera lo mismo que el sistema que iba a producir el
resultado final, y cuando por fin se corrieron los dos sobre la misma base, el
instrumento entero se movió mucho más que el efecto que se le estaba midiendo.

**Más potencia no vale nada sin trazabilidad al sistema que entrega.** Y el
corolario práctico, que es lo que hay que cambiar: un banco de evaluación se
contrasta contra el pipeline **antes** de usarlo para confirmar líneas, no
después de haber confirmado tres.
