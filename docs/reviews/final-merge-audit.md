# Auditoría final de merge — T27

Última revisión local: 2026-11-09. **Veredicto vigente: `NOT_READY`.**
Aceptación operacional real: **`BLOCKED`**. La consulta de gobernanza descrita
abajo corresponde a la auditoría previa; no se volvió a consultar ni modificar
el ruleset en la aceptación.
**T27 BLOQUEADA; progreso 26/27. No autoriza merge.**

## Aceptación operacional real incorporada a T27

HEAD sometido al preflight y pruebas específicas:
`c729f1936f1e637f992c1a6167cb9ff15595cef2`; rama correcta y árbol inicialmente
limpio. El permiso nuevo amplía exclusivamente la comprobación operacional dentro
de T27 (DEC-028); no aprueba ciencia, campeón ni operación sanitaria.

[Recibo de este intento](../evidence/task27/acceptance-preflight-ecb0f761ba1c48e3a724549d4496362d.json).

| Comprobación | Resultado observado |
|---|---|
| HF_TOKEN de entorno | Ausente en el proceso ejecutor, también tras aviso de habilitación del usuario |
| whoami | No ejecutado: falta credencial explícita; no se recurrió a login cacheado |
| Revisión inmutable corregida | NOT_VERIFIED; no se pudo consultar el dataset privado |
| Cinco archivos por nombre/tamaño/SHA-256 | NOT_VERIFIED sobre el release corregido |
| Enero 2020: 1.122 municipios, 31 días, 34.782 claves, sin duplicados inesperados | NOT_VERIFIED; no se leyeron microdatos |
| Ya no limitado a 76 municipios de Meta/Tolima | NOT_VERIFIED |
| Clon limpio e instalación bloqueada | No iniciados por bloqueo del prerrequisito privado |
| Comando único real | NOT_EXECUTED; sin código de salida, duración, RSS o identidad de salida atribuibles |
| Pruebas específicas | 292 PASS, cero fallos/errores/omisiones; 21,293 s |
| Registro y preservación | VALID; 49/49, 22 JSON, 16 recibos e identidad N=3 intactos |

Comando solicitado, **no ejecutado**:

```sh
uv run --locked --directory pipeline python tools/build_approved_canonical.py
```

La referencia local conserva
`pipeline/conf/releases/approved-raw.json`, revisión configurada
`a1a7f237a4baa6ffa848fabeef474f811f3b3f33`. **No se afirma que sea el release
corregido ni que se haya verificado remotamente en este intento.** No se modificó
ningún manifiesto ni referencia anterior. No hay medición real de memoria,
identidad canónica nueva o recibo operacional del helper: los valores ausentes
quedan nulos en el recibo, sin reutilizar resultados de T16 como si fueran nuevos.

### Viabilidad del experimento técnico opcional

La inspección del registro y las configuraciones confirma que EXP001 y EXP002
son `synthetic_fixture` con `data.mode=synthetic`. El registro solo admite
`synthetic_fixture` o `scientific`; `load_configuration` impide intercambiar sin
más fuentes sintéticas y reales. No hay receta real registrada reutilizable ni
un tipo de aceptación técnica real separado. T16 es una validación cerrada,
con especificación y configuración propias, y no se vuelve a ejecutar.

Además, `experiment_management/runner.py:acquire_and_build` reconstruye el
canónico desde crudos: no recibe el canónico provisional producido previamente
por el helper. Introducir ese consumo sería otra modificación de interfaz.
No se cambia el esquema, no se convierte un fixture en experimento real y no se
inventa una receta. EXP003 continúa libre, sin reserva ni ejecución. No hay receta
real sometida a preaprobación: su revisión es `NOT_VERIFIED`, no una aprobación.

Fuentes: [registro](../experiments/registry.yml),
[configuración](../../pipeline/src/sat_dengue_pipeline/experiment_management/configuration.py),
[ejecutor](../../pipeline/src/sat_dengue_pipeline/experiment_management/runner.py),
[manual](../experiments/manual_pipeline.md) y
[contrato todavía propuesto](../experiments/contrato.md).
La adquisición y construcción reales podrían validar las novedades operativas
sin entrenamiento, como permite la instrucción del usuario, pero **aún no se han
comprobado**. Las pruebas artificiales no sustituyen esa aceptación.

### Diagnóstico y reanudación de la aceptación

La comprobación de presencia informa ausencia de variable, no token inválido.
No hubo fallo de autenticación de Hugging Face porque `whoami` no pudo iniciarse
con una credencial explícita. No se buscó, imprimió ni almacenó ningún token.

La acción externa necesaria es hacer que HF_TOKEN esté disponible en el entorno
heredado por el proceso que ejecuta la prueba. Tras comprobar presencia y
`whoami`, reanudar desde la consulta del release, fijar la revisión corregida y
verificar enero 2020 antes del comando real. No hace falta ID de experimento para
este preflight; ninguna ejecución científica quedó fallida o debe repetirse.

No se creó clon temporal. Las pruebas específicas usaron fixtures temporales y
el entorno ya instalado; dejaron el árbol versionado limpio antes del registro
documental. No se repitieron suites completas de pipeline/API/tablero/portabilidad.
Solo se agregan este diagnóstico, su recibo y el registro del plan; el commit de
documentación queda **local**, sin atribuirle la CI verde del HEAD anterior.

No se confirma como corregida ninguna novedad que requiera los datos privados.
T27 permanece BLOQUEADA, 26/27; aceptación BLOCKED y auditoría NOT_READY. Los
controles remotos y la aprobación independiente señalados en la auditoría previa
siguen pendientes de verificación antes de cualquier merge.

## Auditoría previa de gobernanza y alcance comprobado

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
Durante la publicación anterior no se repitieron suites locales tras la
instrucción del usuario; la nueva aceptación permite únicamente las pruebas
específicas registradas arriba. No se repiten suites completas.

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

## Diagnóstico previo de gobernanza y condición de reanudación

Bloqueo confirmado de gobernanza, sin fallo de código ni ejecución científica
que recuperar. No aplican IDs de experimento o ejecución nuevos. Se conserva
la evidencia y no se alteran registros, recibos, cachés o locks.

La recuperación mínima es verificar posteriormente las acciones externas de
configuración y aprobación sobre el HEAD final. Hasta entonces T27 sigue
`BLOQUEADA`, 26/27. La auditoría de gobernanza previa quedó
`READY_WITH_EXTERNAL_ACTION`; el veredicto vigente es `NOT_READY` por la aceptación
real adicional bloqueada. No se crea cierre 27/27,
no se hace merge y no se requiere otro commit para sustituir la aprobación.
