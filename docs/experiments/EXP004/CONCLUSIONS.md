# EXP004 R2 — evidencia y conclusiones pendientes del equipo

Fecha: 12 de noviembre de 2026. Resultado científico: **PENDING**.
`scientific_conclusion: NOT_APPROVED`; `champion_status: NOT_SELECTED`;
sin autorización operativa. El registro conserva RUNNING hasta la decisión humana;
el terminal COMPLETED del recibo solo describe la fábrica terminada.

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

El retroanálisis predeclarado se invocó una vez:

```sh
uv run --locked --directory pipeline kedro run --pipeline retroanalisis --env exp004
```

Terminó con salida 1 en raw_input, antes del canónico o del ajuste, por ausencia
del release corregido en inbox. No produjo los seis CSV ni una comparación
retrospectiva. [Intento preservado](RETROANALYSIS_ATTEMPT_1.json) y
[diagnóstico y recuperación propuesta](RETROANALYSIS_RECOVERY.md).
No se ha autorizado ni efectuado un reintento a la fecha de este borrador.

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
favor de la hipótesis; esto no asigna una categoría científica al registro.
T+2 primaria tiene tres cortes positivos y cuatro empates; secundaria tiene
cuatro positivos, dos deterioros y un empate. Ninguna rescata T+1.

## Comparación

La pregunta del proyecto se evaluó bajo contrato **1.0.0 APPROVED**: ganancia
frente al canal condicionado ≥10 pp y cota inferior ≥10 pp, además de carga,
intervalo, A/C primaria o A/B/C secundaria, soporte, controles y consistencia.
No se usaron los 5 pp históricos como sustituto.

| Brazo | Lectura | Cortes que pasan solo ganancia y cota ≥10 pp | Votos con todas las reglas / cortes utilizables |
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
- El diagnóstico adicional de retroanálisis aún no se obtuvo; su instrumento
  descriptivo no sustituiría la evaluación contractual de la fábrica.
- El inventario de fábrica no contiene una curva completa de TP frente a volumen
  de alertas del apartado 9 del contrato. Se conserva el punto predeclarado y sus
  métricas; la curva de retroanálisis todavía no existe. No se afirma cobertura
  completa de ese requisito para una pretensión de superioridad.
- La revisión posterior del mismo agente no constituye revisión independiente.

## Decisión científica

**PENDING**. Se solicita al equipo decidir POSITIVE, NEGATIVE o INCONCLUSIVE
tras revisar la evidencia y el alcance pendiente; no se asigna ninguna aquí.
El registro no se cierra. Sin campeón, publicación ni autorización operativa.

## Qué se aprendió

La recencia fijada cambia uno, tres o cuatro TP en las tres lecturas de fábrica,
con intervalos que incluyen cero. Una diferencia puntual positiva no satisface
la hipótesis primaria predeclarada, y superar un margen frente al canal en
algunos cortes no satisface simultáneamente carga, A/B/C y consistencia.
Se conserva el resultado sin retocar vida media, umbral, soportes o semillas.

## Próximo paso

Resolver por decisión humana la recuperación ambiental del retroanálisis,
conservando el fallo, sin repetir la fábrica. Completar o declarar explícitamente
pendiente ese diagnóstico. Solicitar revisión científica independiente y decisión
del equipo antes de cerrar el registro. No publicar, abrir PR, hacer push o merge.

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
