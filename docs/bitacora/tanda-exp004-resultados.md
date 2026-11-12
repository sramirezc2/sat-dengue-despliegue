# Tanda EXP004 — resultados de la receta R2 aprobada

Fecha: 12 de noviembre de 2026. Resultado científico: **PENDING**, decisión del
equipo pendiente. Esta entrada añade resultados sin editar la
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
empates y dos deterioros. Ningún T+2 rescata T+1. No se declara categoría
científica POSITIVE/NEGATIVE/INCONCLUSIVE en esta entrada.

## Pregunta del proyecto y límites

Contrato 1.0.0 APPROVED, ganancia frente al canal y cota inferior ≥10 pp.
Ambos brazos obtienen 0/7 votos completos por lectura en cada semilla. En T+1
ningún corte alcanza siquiera 10 pp puntuales. En T+2 primaria, 2021 pasa
ganancia y cota, pero excede la carga; 2024 no alcanza la cota. En secundaria,
2023/2024 pasan ganancia y cota pero fallan B y otras condiciones históricas;
2021 supera persistencia y tiene precisión insuficiente frente al canal.
B secundaria se evaluó como informativa y obligatoria en los siete cortes.
Los controles negativos no pasaron. La evidencia no aprueba un modelo,
campeón, utilidad operacional o respuesta afirmativa del proyecto.

## Retroanálisis: intento conservado

```sh
uv run --locked --directory pipeline kedro run --pipeline retroanalisis --env exp004
```

Una invocación, salida 1 en raw_input por caché corregida ausente en inbox,
antes de construir el canónico o entrenar. No hay CSV ni verificación de
conjunto.csv todavía. La fábrica usa otra raíz de caché, con los cinco archivos
íntegros. Se conserva el [registro del fallo](../experiments/EXP004/RETROANALYSIS_ATTEMPT_1.json)
y el [diagnóstico](../experiments/EXP004/RETROANALYSIS_RECOVERY.md).
No se relanza sin autorización humana adicional de la recuperación concreta.

## Evidencia, aprendizaje y decisión pendiente

[CONCLUSIONS.md](../experiments/EXP004/CONCLUSIONS.md) separa hipótesis de pesos,
evaluación contractual, desgloses, disponibilidad retrospectiva, soporte
departamental y limitaciones. [Resumen agregado](../experiments/EXP004/RESULTS_SUMMARY.json)
conserva las cinco semillas y las celdas conjuntas. MLflow padre
dad66d3b49894b518a0b3805858b0d3c y sus dos hijos terminaron FINISHED.

Las diferencias pequeñas no prueban mejora; un margen aislado frente al canal
no sustituye carga, B, A/C y consistencia. No se ajusta la receta para favorecer
un resultado. El equipo debe decidir la recuperación ambiental pendiente y,
tras la revisión científica posterior e independiente, el resultado científico
antes de cerrar el registro. Sin publicación, push, PR, merge o campeón.
