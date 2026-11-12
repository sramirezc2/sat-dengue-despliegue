# EXP004 R2 — cierre científico NEGATIVE

Fecha de cierre: 12 de noviembre de 2026. Resultado científico: **NEGATIVE**,
por decisión explícita del equipo SAT DENGUE comunicada por la persona usuaria
en esta conversación. Cierre autorizado del registro: **COMPLETED/NEGATIVE**,
mediante la interfaz oficial. `champion_status: NOT_SELECTED`; sin aprobación
de modelo ni autorización operativa.

La decisión y las comprobaciones de cierre se registran en `CLOSURE.json`.
Los recibos cerrados conservan sus estados originales, incluido
scientific_conclusion NOT_APPROVED: no se reescriben para simular una decisión
humana previa a su producción. Este cierre usa exclusivamente evidencia existente.

Aprobación humana: [APPROVAL.md](APPROVAL.md), commit
`a075b0d6e87627b4cabc650b729afbc298c498f5`. Protocolo SHA-256
`ee40e74fa0dbf7bdd150340c9103961ef9fe0300c87743faab1c3337aa6ab2fd`;
configuración SHA-256
`ed55aedb9259ae253863fd97cf255d48b56cba2a15854e4746e666df32e7132f`.
No se modificó la receta después de observar resultados.

## Hipótesis

Dar más peso a la historia reciente mejora la anticipación de nuevos inicios de
exceso frente a la misma logística climática con pesos uniformes. Se formaliza
una hipótesis ya explorada; 2018–2024 no es confirmación independiente.

Los brazos uniform_history y recent_history_36m solo difieren en sample_weight
del ajuste: `2 ** (-age_months / 36)`, normalizado a media 1 por train efectivo
del fold. Ambos conservan filas, predictores, preparación, roles, calibración,
umbral, comparadores y presupuesto. No hubo HPO, otras vidas medias, exclusión
de observaciones antiguas, transferencia de estado ni selección de semilla.

## Resultado

Un único comando real de fábrica completó sus nueve nodos, con salida 0 y
duración informada por Kedro de 856,7 segundos:

```sh
uv run --locked --directory pipeline kedro run --pipeline experiment_run --params experiment_id=EXP004
```

Ejecución: `04a0554e6fa7470394b185b5dab36d7a`. Fuente de verdad:
[docs/evidence/experiments/EXP004/04a0554e6fa7470394b185b5dab36d7a/inventory.json](../../evidence/experiments/EXP004/04a0554e6fa7470394b185b5dab36d7a/inventory.json),
SHA-256 `9eb1aa806d301efc7e2ec2d363d831446d94925cfd18c3eab31b161f66c3c219`.
Inventario verificado; 105 archivos agregados, ninguno mayor de 512 kB.
No contiene filas de predicción o pesos por fila. Se entrenaron las 140 variantes
y 210 modelos de la receta; se conservaron las cinco semillas.

El retroanálisis predeclarado tuvo un intento fallido previo al ajuste y una
única invocación adicional de recuperación autorizada, con el mismo comando:

```sh
uv run --locked --directory pipeline kedro run --pipeline retroanalisis --env exp004
```

El primer intento terminó con salida 1 en raw_input, por caché corregida ausente
en inbox: [fallo preservado](RETROANALYSIS_ATTEMPT_1.json) y
[diagnóstico](RETROANALYSIS_RECOVERY.md). La
[recuperación autorizada](RECOVERY_AUTHORIZATION.md) completó 15/15 nodos,
salida 0, en 724,7 segundos: [segundo intento](RECOVERY_ATTEMPT_2.json),
[resultado y hashes](RECOVERY_RESULT.md) y [validación](RECOVERY_VALIDATION.json).
Se conservan seis CSV bajo `pipeline/data/retroanalisis/EXP004/run1/`, con
815 pares de folds, 1.630 registros de ajuste, 81.240 predicciones y cero
omisiones. El cierre no repite ninguno de estos recorridos ni sus modelos.

## Métricas principales

Fábrica, población común Meta/Tolima, agregado de los siete cortes predeclarados.
Las cinco semillas (7, 13, 31, 53 y 101) producen exactamente estos mismos
conteos, diferencias e intervalos. Se informa una vez cada resultado coincidente;
no se suman observaciones, inicios o cortes entre semillas.

| Lectura | N / inicios | TP uniforme / reciente | Alertas uniforme / reciente | Diferencia reciente−uniforme (pp), IC95 % |
|---|---:|---:|---:|---|
| T+1 primaria | 3.848 / 593 | 130 / 131 | 292 / 291 | +0,1686 [−0,8293; 1,1746] |
| T+2 primaria | 3.871 / 431 | 81 / 84 | 265 / 265 | +0,6961 [−0,6609; 2,1284] |
| T+2 secundaria | 5.852 / 593 | 97 / 101 | 361 / 364 | +0,6745 [−0,5320; 1,9516] |

Intervalos emparejados por mes objetivo, 2.000 réplicas y semilla 42, sin
reentrenar ni cambiar umbrales. Todas las cotas inferiores cruzan cero.
Estos agregados describen la hipótesis de pesos; no añaden votos al proyecto.

En T+1 reciente−uniforme por corte, las diferencias de TP son
2018: −1; 2019: 0; 2020: +1; 2021: 0; 2022: −1; 2023: +1; 2024: +1,
idénticas en las cinco semillas. Hay 3/7 cortes positivos frente a los 4/7
exigidos, dos empates y dos deterioros. Tampoco se alcanza cota inferior >0
en el agregado T+1. No se satisface el criterio predeclarado de evidencia a
favor de la hipótesis. El equipo asigna NEGATIVE por ese incumplimiento,
sin afirmar que los procedimientos sean equivalentes o que el efecto sea cero.
T+2 primaria tiene tres cortes positivos y cuatro empates; secundaria tiene
cuatro positivos, dos deterioros y un empate. Ninguna rescata T+1.

## Comparación

Las condiciones implementadas de la pregunta del proyecto se evaluaron bajo
contrato **1.0.0 APPROVED**: ganancia
frente al canal condicionado ≥10 pp y cota inferior ≥10 pp, además de carga,
intervalo, A/C primaria o A/B/C secundaria, soporte, controles y consistencia.
No se usaron los 5 pp históricos como sustituto. Estas comprobaciones del punto
predeclarado no acreditan cumplimiento integral del contrato: falta la curva
completa de fábrica y la evidencia no es confirmatoria independiente.

| Brazo | Lectura | Cortes que pasan solo ganancia y cota ≥10 pp | Votos de las condiciones implementadas / cortes utilizables |
|---|---|---:|---:|
| uniform_history | T+1 primaria | 0/7 | 0/7 |
| recent_history_36m | T+1 primaria | 0/7 | 0/7 |
| uniform_history | T+2 primaria | 1/7 | 0/7 |
| recent_history_36m | T+2 primaria | 1/7 | 0/7 |
| uniform_history | T+2 secundaria | 2/7 | 0/7 |
| recent_history_36m | T+2 secundaria | 2/7 | 0/7 |

Cada fila es idéntica en las cinco semillas. En T+1, ambos brazos tienen
NO_CUMPLE_POR_EFECTO en los siete cortes de cada semilla: la ganancia puntual
no alcanza 10 pp. En T+2 primaria, 2021 pasa ganancia y cota, pero excede la
carga máxima: +5,10 falsas/100 municipio-mes (cotas superiores 5,94 uniforme y
5,99 reciente). En 2024 la ganancia puntual pasa y la cota inferior no.
Los restantes cortes no alcanzan la ganancia puntual.

En T+2 secundaria B fue informativa y obligatoria en todos los cortes. Ambos
brazos superan persistencia solo en 2021, cuya cota inferior frente al canal
es 9,43 pp uniforme o 6,25 pp reciente, insuficiente. Los cortes 2023/2024
pasan las dos condiciones de ganancia, pero fallan B, A y C históricas.
No se omite esa discrepancia. B primaria conserva NO_EVALUABLE por
DEGENERATE_PRIMARY_COHORT; no se atribuye victoria frente a cero alertas.

Las seis vistas conjuntas producen el estado automático
INCONCLUSO_POR_INESTABILIDAD bajo el contrato: cada semilla tiene 0/7 votos,
consistencia NO_CUMPLE, y ninguna satisface unanimidad afirmativa. Ese nombre
canónico no describe variación numérica entre semillas: aquí coinciden las cinco.
Tampoco es una decisión científica INCONCLUSIVE del equipo.

El [resumen agregado](RESULTS_SUMMARY.json) conserva todas las semillas, celdas
conjuntas, intervalos, A/B/C, cargas y estados. El inventario original conserva
además AP, AUROC, Brier y desgloses anuales/territoriales. No hubo
controles negativos con CUMPLE ni violaciones de presupuesto en las celdas
conjuntas. Los resultados departamentales con soporte insuficiente siguen visibles.

Retroanálisis, lectura primaria, punto descriptivo propio frente a
canal_fuera_exceso y su volumen realizado por mes. Los cinco resultados coinciden;
no se elige una semilla ni se mezclan cifras con la fábrica:

| Horizonte | Inicios | Alertas por brazo | TP canal | TP uniforme | TP reciente | Reciente−uniforme |
|---|---:|---:|---:|---:|---:|---:|
| T+1 | 641 | 817 | 323 | 359 | 361 | +2 |
| T+2 | 459 | 1.158 | 207 | 253 | 251 | −2 |

El cambio de signo entre horizontes no muestra una mejora estable del instrumento
adicional. Los intervalos de resumen.csv comparan cada brazo con su canal,
no reciente con uniforme. No se reinterpretan como intervalos de la hipótesis.
El retroanálisis no declara secondary_t2 y no se le atribuyen los resultados
de esa lectura de fábrica.

La [auditoría de fábrica](EXECUTION_AUDIT.json) conserva 105 pares de modelos por
horizonte y 525 comparaciones de claves, predictores y matrices en los cinco
roles. Las etiquetas productoras se verificaron antes de ajustar y las de
evaluación tras predecir. La [validación de recuperación](RECOVERY_VALIDATION.json)
conserva igualdad de claves y etiquetas train/evaluación por horizonte, lectura
primaria, semilla y fold; las claves efectivas del CSV y los desenlaces H5 se
contrastaron con el canónico ya producido. No se recalculan ahora predicciones
ni desenlaces. Se mantienen las cohortes propias de cada lectura, sin exigir
igualdad entre primaria y secundaria.

## Limitaciones

- Evidencia exploratoria en periodos conocidos: no prueba confirmación,
  utilidad sanitaria, disponibilidad operacional o ausencia de backfill.
- La demora de un mes y el embargo son supuestos retrospectivos. El presupuesto
  proxy del 10 % no mide capacidad sanitaria.
- En Meta/Tolima conjunto todos los cortes tienen ≥30 inicios; algunas celdas
  departamentales no. T+2 primaria en Meta queda NO_EVALUABLE en ambos brazos
  al agregar semillas. No se oculta con el resultado conjunto.
- La vista genérica national de la fábrica recibe aquí solo los 76 municipios
  filtrados; no es una evaluación nacional ni una cohorte adicional.
- La certificación N=3 del canónico no es N=3 E2E de estos modelos. El recibo
  tiene un seed base 53 heredado de la plantilla; sus variantes y bloque
  científico incluyen las cinco identidades, sin escoger una.
- El retroanálisis recuperado usa ventanas, ranking y presupuesto distintos;
  es descriptivo y no sustituye la evaluación contractual de la fábrica.
- **Curva contractual completa de fábrica: NOT_PRODUCED/DEFERRED.** El equipo
  decidió no implementarla ahora. curva.csv del retroanálisis no sustituye la
  curva faltante de fábrica. EXP004 no acredita cumplimiento integral del contrato,
  no puede producir un resultado afirmativo del proyecto ni seleccionar champion.
  Esta limitación no impide la conclusión NEGATIVE sobre la hipótesis específica
  de recencia en el punto predeclarado. No se genera la curva o una nueva evaluación.
- La revisión posterior del mismo agente no constituye revisión independiente.

## Decisión científica

**NEGATIVE**, decisión humana explícita del equipo SAT DENGUE. La hipótesis
predeclarada no se cumplió: los intervalos incluyen cero, T+1 incumple la cota
inferior positiva y la mayoría de cortes, y el retroanálisis no muestra mejora
estable. La [revisión posterior](POST_RUN_REVIEW.md) verifica la correspondencia
con receta y evidencia; fue realizada por el mismo agente, **no es independiente**.

La decisión rechaza únicamente la ponderación exponencial de 36 meses evaluada
en EXP004. No demuestra que toda estrategia de actualización temporal sea inútil,
ni igualdad exacta entre brazos o ausencia de cualquier efecto. Tampoco es una
respuesta confirmatoria negativa a toda la pregunta del proyecto. El registro
se cierra mediante el CLI oficial con COMPLETED y resultado NEGATIVE. No se
aprueba un modelo, campeón, publicación o uso operativo; no se modifican los
veredictos automáticos ni los recibos históricos para hacerlos coincidir con
la categoría humana.

## Qué se aprendió

La recencia fijada cambia uno, tres o cuatro TP en las tres lecturas de fábrica,
con intervalos que incluyen cero. Una diferencia puntual positiva no satisface
la hipótesis primaria predeclarada, y superar un margen frente al canal en
algunos cortes no satisface simultáneamente carga, A/B/C y consistencia.
Se conserva el resultado sin retocar vida media, umbral, soportes o semillas.
El criterio que no se cumplió pertenece a esta receta y a su punto predeclarado;
no permite extrapolar el rechazo a todas las formas de actualización temporal.

## Próximo paso

Conservar EXP004 cerrado como NEGATIVE. La curva completa de fábrica queda
diferida por el equipo; cualquier decisión futura sobre esa capacidad o nuevas
hipótesis necesita su alcance y autorización propios. No se inicia otro experimento
ni se genera nueva evidencia en este cierre. Revisión independiente, disponibilidad
operativa, cohorte confirmatoria y eventual N=3 E2E siguen sin acreditarse; no
son aprobaciones concedidas por este resultado. Sin push, PR, merge o publicación.

## Linaje y tracking

Fábrica desde `a075b0d6e87627b4cabc650b729afbc298c498f5`, dirty=false;
código `4531f1080b62a9a482061bbcf686191274e8ff997b515f15c8dd81dc46a45321`.
Release `satd-raw-173d5856`, operational_full reconstruido: 242.352 claves,
1.122 municipios, 2007-01–2024-12, bytes idénticos al certificado predeclarado.
SHA-256 canónico `b4562ba50def7a98dceede0b7e95feed0e799b4652939d8037f1604bef37a23d`.
2025 fue puesto en cuarentena antes de los productores; los 140 planes y las
etiquetas liberadas terminan antes de 2025. Las evaluaciones de fábrica cubren
enero–noviembre de 2018–2024, con las cohortes propias de cada lectura.

MLflow local `pipeline/.tracking/experiments/tracking.sqlite`:
padre `dad66d3b49894b518a0b3805858b0d3c`, hijos
`9bbe5dab0e1647a1a6519278880fbbee` y `4a631d3203e547249201b66a5fb84d7c`.
Los tres se verificaron FINISHED por lectura SQL en modo solo lectura.
No se persistieron credenciales ni modelos; pesos resumidos y digests quedan en
recibo/linaje, nunca los pesos por fila.
