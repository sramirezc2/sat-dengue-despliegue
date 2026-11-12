# Tanda EXP004 — resultados de la receta R2 aprobada

Fecha: 12 de noviembre de 2026. Resultado científico de cierre: **NEGATIVE**,
por decisión humana explícita del equipo SAT DENGUE. Estado final autorizado:
**COMPLETED**, mediante el CLI oficial. Esta entrada actualiza resultados sin editar la
[preinscripción R2](tanda-exp004-recencia.md).

## Hipótesis y receta ejecutada

Recencia exponencial fija de 36 meses frente a pesos uniformes en la misma
logística con clima. Solo sample_weight del ajuste cambia; normalización a
media 1 dentro del train efectivo del fold. Hipótesis ya explorada, sin carácter
confirmatorio independiente. Misma receta y hashes aprobados por la persona en
la conversación, [aprobación registrada](../experiments/EXP004/APPROVAL.md).

## Qué se corrió

Una fábrica E2E, nueve nodos completados, salida 0, 856,7 segundos. Release
corregido satd-raw-173d5856; operational_full reconstruido y validado contra el
certificado N=3 fijado. 140 variantes, 210 modelos, cinco semillas
7/13/31/53/101, siete cortes 2018–2024. Evaluación enero–noviembre; ningún uso
de 2025 en aprendizaje, selección, calibración, umbrales o evaluación.

```sh
uv run --locked --directory pipeline kedro run --pipeline experiment_run --params experiment_id=EXP004
```

[Inventario de fábrica](../evidence/experiments/EXP004/04a0554e6fa7470394b185b5dab36d7a/inventory.json),
SHA-256 `9eb1aa806d301efc7e2ec2d363d831446d94925cfd18c3eab31b161f66c3c219`.

## Resultados emparejados de fábrica

Agregado Meta/Tolima de los siete cortes, sin sumar semillas. Los cinco
resultados coinciden exactamente; no se selecciona uno.

| Lectura | TP uniforme / reciente | Diferencia de sensibilidad (pp), IC95 % |
|---|---:|---|
| T+1 primaria | 130 / 131, de 593 inicios | +0,1686 [−0,8293; 1,1746] |
| T+2 primaria | 81 / 84, de 431 inicios | +0,6961 [−0,6609; 2,1284] |
| T+2 secundaria | 97 / 101, de 593 inicios | +0,6745 [−0,5320; 1,9516] |

T+1 no satisface la regla de mejora predeclarada: cota inferior no positiva y
3/7 cortes con diferencia positiva, frente a mayoría exigida de 4/7; dos
empates y dos deterioros. Ningún T+2 rescata T+1. El equipo establece NEGATIVE
por el incumplimiento de la hipótesis predeclarada, sin inferir equivalencia
exacta entre brazos ni ausencia de cualquier efecto.

## Pregunta del proyecto y límites

Contrato 1.0.0 APPROVED, ganancia frente al canal y cota inferior ≥10 pp.
Ambos brazos obtienen 0/7 votos completos por lectura en cada semilla. En T+1
ningún corte alcanza siquiera 10 pp puntuales. En T+2 primaria, 2021 pasa
ganancia y cota, pero excede la carga; 2024 no alcanza la cota. En secundaria,
2023/2024 pasan ganancia y cota pero fallan B y otras condiciones históricas;
2021 supera persistencia y tiene precisión insuficiente frente al canal.
B secundaria se evaluó como informativa y obligatoria en los siete cortes.
Los controles negativos no pasaron. La curva contractual completa de fábrica
permanece **NOT_PRODUCED/DEFERRED**, por decisión explícita del equipo de no
implementarla ahora. curva.csv del retroanálisis no la sustituye. EXP004 no
acredita cumplimiento integral del contrato, no puede seleccionar champion ni
producir un resultado afirmativo del proyecto. Esa limitación no impide concluir
NEGATIVE sobre la hipótesis específica de recencia en el punto predeclarado.

## Retroanálisis recuperado e intento fallido conservado

```sh
uv run --locked --directory pipeline kedro run --pipeline retroanalisis --env exp004
```

El primer intento terminó con salida 1 en raw_input por caché corregida ausente
en inbox, antes de construir el canónico o entrenar. Se conservan el
[fallo](../experiments/EXP004/RETROANALYSIS_ATTEMPT_1.json) y su
[diagnóstico](../experiments/EXP004/RETROANALYSIS_RECOVERY.md).
La recuperación humana autorizada materializó solo la caché local y completó
una única invocación adicional: [resultado y hashes](../experiments/EXP004/RECOVERY_RESULT.md).
Los seis CSV verifican, con 815 pares de folds, 81.240 predicciones, cero
omisiones e igualdad de claves y etiquetas entre brazos por horizonte,
lectura primaria, semilla y fold. No se añadió secondary_t2 al retroanálisis.

| Horizonte | TP uniforme | TP reciente | Reciente−uniforme |
|---|---:|---:|---:|
| T+1 | 359 | 361 | +2 |
| T+2 | 253 | 251 | −2 |

Son resultados idénticos en las cinco semillas, en el punto descriptivo propio
frente a canal_fuera_exceso y con igual presupuesto entre brazos. No muestran
mejora estable entre horizontes; no se combinan con las cohortes, intervalos
o votos de fábrica. Los objetivos y la disponibilidad de etiquetas terminan
antes de 2025 en ambos instrumentos.

## Evidencia, aprendizaje y decisión científica de cierre

[CONCLUSIONS.md](../experiments/EXP004/CONCLUSIONS.md) separa hipótesis de pesos,
evaluación contractual, desgloses, disponibilidad retrospectiva, soporte
departamental y limitaciones. [Resumen agregado](../experiments/EXP004/RESULTS_SUMMARY.json)
conserva las cinco semillas y las celdas conjuntas. MLflow padre
dad66d3b49894b518a0b3805858b0d3c y sus dos hijos terminaron FINISHED.

Las diferencias pequeñas no prueban mejora; un margen aislado frente al canal
no sustituye carga, B, A/C y consistencia. No se ajusta la receta para favorecer
un resultado. La [revisión posterior](../experiments/EXP004/POST_RUN_REVIEW.md)
contrasta receta, evidencia y decisión: fue realizada por el mismo agente y
**no es independiente**. El equipo decidió NEGATIVE y autorizó el cierre oficial.

La decisión rechaza únicamente la ponderación exponencial de 36 meses evaluada
en EXP004. No demuestra que toda estrategia de actualización temporal sea inútil.
La evidencia sigue siendo retrospectiva y exploratoria, sin confirmación
independiente ni acreditación de disponibilidad operativa. Las cinco semillas
7/13/31/53/101 se conservaron sin elegir la mejor; no se suman como nuevas cohortes.
El cierre utiliza solo lo ya producido, sin adquirir, construir, entrenar,
repetir recorridos ni reconstruir predicciones o curvas. Sin publicación, push,
PR, merge, aprobación de modelo, champion o autorización operativa.
