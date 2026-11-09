# Auditoría final de merge — T27

Fecha de consulta: 2026-11-09. **Veredicto: `READY_WITH_EXTERNAL_ACTION`.**
**T27 BLOQUEADA; progreso 26/27. No autoriza merge.**

## Revisión y alcance comprobados

- PR único: [#1](https://github.com/sramirezc2/sat-dengue-despliegue/pull/1),
  abierto desde `feature/pipeline-e2e` hacia `main`.
- Commit auditado: `0222d6d0c3e1cb9ad2a2cc7253584f1c8de41843`, cierre publicado
  de T26. HEAD local, tracking y PR coincidían; árbol limpio antes de esta auditoría.
- GitHub informó `mergeable=true` y `mergeable_state=blocked`: ausencia de conflicto
  no acredita los gates de merge.
- T25 y T26 completas. T27 se inició solo después de los siete checks verdes
  del cierre de T26; queda bloqueada por controles y aprobación externos.
- Esta auditoría agrega exclusivamente documentación. Sus propios checks deben
  consultarse sobre el SHA que la publique: el snapshot siguiente acredita
  únicamente `0222d6d`, nunca un descendiente. La descripción del PR registra
  el HEAD final y su resultado sin crear otro commit tras la aprobación humana.

## Checks remotos del cierre de T26

[Snapshot por SHA](../evidence/task27/t26-closure-checks.json), con nombres,
URLs, tiempos, aplicación GitHub Actions (`15368`) y avisos observados.

| Check exacto | Resultado | Duración | Evidencia |
|---|---|---:|---|
| API tests | success | 14 s | [Job](https://github.com/sramirezc2/sat-dengue-despliegue/actions/runs/42708063596/job/129470026381) |
| Dashboard quality | success | 23 s | [Job](https://github.com/sramirezc2/sat-dengue-despliegue/actions/runs/42708063920/job/129470027058) |
| Pipeline portability (Ubuntu) | success | 209 s | [Job](https://github.com/sramirezc2/sat-dengue-despliegue/actions/runs/42708063904/job/129470028567) |
| Pipeline portability (Windows) | success | 346 s | [Job](https://github.com/sramirezc2/sat-dengue-despliegue/actions/runs/42708063904/job/129470028181) |
| Pipeline portability (macOS) | success | 241 s | [Job](https://github.com/sramirezc2/sat-dengue-despliegue/actions/runs/42708063904/job/129470028258) |
| Pipeline quality | success | 155 s | [Job](https://github.com/sramirezc2/sat-dengue-despliegue/actions/runs/42708063904/job/129470027733) |
| Publication contract | success | 37 s | [Job](https://github.com/sramirezc2/sat-dengue-despliegue/actions/runs/42708063531/job/129470025864) |

Persisten avisos conocidos de Starlette/httpx, react-refresh, Vite y OmegaConf;
no se modifican dependencias ni se ocultan. Los logs de portabilidad capturan
salidas de subprocesos; una lista vacía de avisos no afirma ausencia de avisos.
Por instrucción expresa del usuario no se repiten suites localmente: se consultan
los resultados de GitHub sobre cada HEAD publicado.

## Ruleset: consulta exclusivamente en lectura

[Ruleset 26765445, «proteger main»](https://github.com/sramirezc2/sat-dengue-despliegue/rules/26765445):
activo, aplicado a `~DEFAULT_BRANCH` (`main`), sin exclusiones observadas.
Su `updated_at` observado es `2026-11-07T12:47:11.976-05:00`.
No se realizó ni se autoriza ninguna modificación remota del ruleset.

| Control exigido por T27 | Configuración observada | Resultado |
|---|---|---|
| Cambios mediante PR | Regla `pull_request` | Cumple |
| Al menos una aprobación | `required_approving_review_count=1` | Cumple configuración |
| Descartar aprobaciones obsoletas | `dismiss_stale_reviews_on_push=true` | Cumple |
| Resolución obligatoria de conversaciones | `required_review_thread_resolution=false` | Falta |
| Checks obligatorios | No existe regla `required_status_checks` | Falta |
| Bloqueo de borrado | Regla `deletion` | Cumple |
| Bloqueo de force push | Regla `non_fast_forward` | Cumple |

La cuenta publicadora `j-mauro-r` tiene `push=true`, `admin=false` y no puede
bypassear el ruleset. Un workflow verde no equivale a un check obligatorio.
La restricción vigente del usuario es lectura solamente: no hay operación de
escritura, payload aplicable, intento de elevar permisos ni solicitud de excepción.

## Acciones pendientes del propietario

Estas son diferencias de configuración para revisión humana, no instrucciones
que Codex esté autorizado a aplicar. El propietario deberá decidirlas fuera de
esta ejecución o bajo una autorización futura expresa:

1. En Settings → Rules → Rulesets → «proteger main», exigir resolución de
   conversaciones (`required_review_thread_resolution=true`).
2. Exigir los siete nombres exactos de la tabla anterior, de GitHub Actions
   (integration ID `15368`), mediante una regla `required_status_checks`.
3. Conservar las protecciones existentes: PR, una aprobación como mínimo,
   descarte de aprobaciones obsoletas, bloqueo de borrado y force push.
4. Tras el último push, una persona distinta de `j-mauro-r`, autor del PR,
   debe revisar y aprobar el HEAD final. Volver a comprobar ruleset, reviews,
   conversaciones y todos los checks de ese SHA antes de declarar T27 completa.

El impacto pendiente es impedir merge sin los siete checks y conversaciones
resueltas. No se propone relajar ninguna protección. No se envió una solicitud
formal de review ni se simuló aprobación.

## Revisión independiente y conversaciones

La consulta de reviews devolvió cero; `reviewDecision=REVIEW_REQUIRED`.
La consulta de review threads devolvió cero, sin conversaciones pendientes
observadas. Esto no sustituye ni la aprobación independiente ni la regla de
resolución obligatoria. Una aprobación anterior a otro push puede descartarse.

## Preservación y límites

El [recibo T26](../evidence/task26/publication-validation.json) conserva el gate
local previo a la instrucción de no repetir suites: 578 pruebas pipeline,
35 API, 55 tablero, contratos 22+22, registro y preservación verdes.
Las revisiones documentales posteriores no cambian ciencia, configuración,
registro experimental, evidencia protegida ni producto; la CI del cierre T26
ya verificó su árbol exacto.

Se preservan 49 archivos protegidos, 22 JSON publicados y 16 recibos T16, EXP001
y EXP002. La identidad N=3 histórica permanece
`899ba8b2c48b69dbf2e9094a6efedfa838cbfe4c800bed25fa1823503d06d52f`;
no se repitió N=3 real ni adquisición privada, entrenamiento o experimentos.
Las comprobaciones locales finales se limitan al diff, metadatos de Git y
estructura de estos documentos; no repiten las suites ejecutadas por GitHub.

El [reporte ejecutivo](../reports/pipeline-e2e-executive-report.md), la
[revisión científica](scientific-review.md) y la
[revisión de seguridad](../security/security-review.md) conservan sus límites.
T16 valida ingeniería, EXP001/EXP002 son fixtures, EXP003 no está integrado;
el contrato sigue `PROPUESTA_PARA_APROBACION`, no hay campeón,
G5 sigue `NOT_APPROVED` y 2025 es evidencia retrospectiva consumida.
No se autoriza operación sanitaria ni se afirma superioridad científica.

## Diagnóstico y condición de reanudación

Bloqueo confirmado de gobernanza, sin fallo de código ni ejecución científica
que recuperar. No aplican IDs de experimento o ejecución nuevos. Se conserva
la evidencia y no se alteran registros, recibos, cachés o locks.

La recuperación mínima es verificar posteriormente las acciones externas de
configuración y aprobación sobre el HEAD final. Hasta entonces T27 sigue
`BLOQUEADA`, 26/27, `READY_WITH_EXTERNAL_ACTION`. No se crea cierre 27/27,
no se hace merge y no se requiere otro commit para sustituir la aprobación.
