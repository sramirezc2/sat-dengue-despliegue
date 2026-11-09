# Auditoría final de merge — T27

Última revisión local: 2026-11-09. **Veredicto vigente: `NOT_READY`.**
Aceptación operacional real: **en curso**, tras autorización expresa del nuevo
release operacional (DEC-029). La autenticación de entorno funciona. La consulta
de gobernanza descrita abajo corresponde a la auditoría previa; no se volvió a
consultar ni modificar el ruleset en esta reanudación.
**T27 BLOQUEADA; progreso 26/27. No autoriza merge.**

## Segundo release operacional autorizado: aceptación pendiente

El usuario autorizó registrar un nuevo manifiesto de adquisición/integridad sin
modificar el contrato científico, la identidad anterior ni evidencia cerrada.
Consulta autenticada fijada exclusivamente a
`173d5856874b89d8aeb0566accc65ce7f6759820`: SHA exacto y `private=true`.
`whoami` volvió a confirmar `mauro114`, organización `sat-dengue`, con credencial
explícita de entorno y sin valores secretos en salidas o archivos.

Se confirmó que únicamente cambia `google_earth_engine.csv`: los dos CSV
epidemiológicos coinciden por tamaño/SHA-256 LFS; los dos archivos pequeños se
descargaron con SHA fijo y sus bytes/tamaños/SHA-256 coinciden. La integridad local
de los cinco archivos se comprobará nuevamente al adquirir el bundle completo.

Nuevo manifiesto:
[`operational-raw-173d5856.json`](../../pipeline/conf/releases/operational-raw-173d5856.json),
SHA-256 de archivo `ee36be0affe23b1bad99044853e48f6396c556f39851852c769002d029f8b550`.
Los cinco nombres/tamaños/hashes son los de la tabla del preflight anterior,
ahora confirmados para el SHA fijado. El manifiesto histórico mantiene SHA-256
`667f4273add97d874ea70344fc698c454c499bea5e9d3e3c5e74c82d8eb70f0c`.

Se añadió exclusivamente la segunda identidad de integridad y su selección
explícita al mecanismo existente: manifiesto → resolver → bundle local. El
constructor y adquiridor directos conservan su default histórico; el helper
operacional selecciona el nuevo manifiesto y acepta `--manifest` para el anterior.
No se cambian configuración científica, encabezados, productores, ventanas,
predictores, roles, modelos ni hiperparámetros. T16 sigue fijada al manifiesto
histórico; `INVENTORY` conserva sus valores. El nuevo release exige repositorio,
proveedor y revisión exactos; las identidades mezcladas se rechazan.

Validaciones previas a la aceptación real: **116 pruebas específicas PASS en
2,57 s**, incluidas nueve nuevas de coexistencia y cuatro variantes adicionales
del helper histórico; cinco regresiones nuevas fallaron antes del cambio y ahora
pasan. Ruff de los siete archivos Python afectados PASS. Registro VALID;
preservación PASS (49 archivos, 22 JSON, 16 recibos T16, N=3 intacto). Solo se
ejecutaron `test_operational_releases.py`, `test_operational_command.py`,
`test_operational_acquisition.py`, `test_private_release.py` y
`test_raw_canonical.py`; no se repiten suites completas.

Pendientes de este intento: descarga real e integridad completa, cobertura de
enero 2020 y comando único desde clon temporal limpio del commit local que
incorpore estos cambios. El registro siguiente conserva el bloqueo anterior y
no representa una solicitud de aprobación todavía pendiente.

## Preflight anterior sobre 8202571: discrepancia de contrato

HEAD comprobado: `8202571e7ba3e0d674e76ec77b9f48c853ffeabf`, rama
`feature/pipeline-e2e`, árbol inicialmente limpio. Solo se comprobó presencia
booleana de `HF_TOKEN`; `HfApi.whoami(token=...)` devolvió usuario `mauro114` y
organización `sat-dengue`. No se imprimió, registró, serializó ni almacenó el valor
del token, ni se usaron credenciales cacheadas.

El primer arranque de `uv` fue impedido por el sandbox al acceder a su caché
(`Operation not permitted`, código 2), antes de ejecutar `whoami`. La repetición
con permiso de acceso terminó con código 0. La consulta autenticada de metadatos
también terminó con código 0; no hubo fallo HTTP de autenticación. `uv` advirtió
que el `VIRTUAL_ENV` heredado no coincide con el entorno de `pipeline` y lo ignoró.

`HfApi.dataset_info(..., files_metadata=True, token=...)` consultó
`sat-dengue/data_raw` en `main` solo para descubrir la revisión y en el SHA
configurado. Ambos informaron `private=true`:

| Referencia consultada | SHA resuelto |
|---|---|
| `main`, descubrimiento del candidato corregido | `173d5856874b89d8aeb0566accc65ce7f6759820` |
| Revisión configurada | `a1a7f237a4baa6ffa848fabeef474f811f3b3f33` |

No se adquirió desde una referencia mutable. El SHA del candidato proviene de
los metadatos; no se hizo una segunda consulta fijada a ese SHA, ni se certificó
todavía que su contenido satisfaga la aceptación del release corregido.

Los cinco nombres esperados están presentes bajo `datos-crudos/`. Comparación
de **metadatos remotos**, sin descarga ni cálculo local de SHA-256:

| Archivo | Bytes del candidato | SHA-256 remoto LFS | Comparación con contrato vigente |
|---|---:|---|---|
| `Divipola-municipios.md` | 209.867 | No disponible en estos metadatos | Nombre/tamaño coinciden; hash NOT_VERIFIED |
| `divipola-provenance.json` | 925 | No disponible en estos metadatos | Nombre/tamaño coinciden; hash NOT_VERIFIED |
| `dengue.csv` | 875.694.283 | `58d277cfef7a60c28d488eefe4e7a1a7bf0f7b0df3dd88245971cd7b3d32c84b` | Coincide en metadatos |
| `dengue_grave.csv` | 24.537.734 | `3d60e96ccbedc35a19a8f5f54be8d786aa599813259c914f131522bf17dd1d70` | Coincide en metadatos |
| `google_earth_engine.csv` | 1.721.511.337 | `a92fd7c7e013136280ba3766b870a303c22ad6196b5411a3fefb81b46670ec8e` | Difiere en tamaño y SHA-256 |

El contrato vigente exige para clima **1.714.544.311 bytes** y
`dfe20fa02b6d6068c04744b5c86f44112048400a7fde637368c0d4effc88cb3f`.
La consulta del SHA configurado devolvió esos valores históricos. El candidato
contiene 6.967.026 bytes adicionales; esto no demuestra por sí solo cobertura
nacional ni explica el contenido añadido.

La identidad antigua está fijada tanto en
[`approved-raw.json`](../../pipeline/conf/releases/approved-raw.json) como en
`INVENTORY` de [`raw/contract.py`](../../pipeline/src/sat_dengue_pipeline/raw/contract.py).
`raw_contract_validation` exige igualdad exacta del inventario aprobado y rechaza
su sustitución. Cambiar solo la revisión no permitiría aceptar los nuevos bytes;
cambiar solo el manifiesto tampoco permitiría superar el contrato del constructor.

Se activa la condición explícita del usuario: **si el release corregido exige
modificar contratos, detenerse y solicitar aprobación**. No se modificaron el
manifiesto, el validador, la ciencia, las ventanas ni los predictores. La siguiente
decisión requiere aprobar expresamente la nueva revisión y la identidad climática
indicadas arriba, con un alcance que preserve el contrato y evidencia cerrados de
T16. No se ha implementado ni elegido una migración de contratos.

| Gate de aceptación | Resultado de esta reanudación |
|---|---|
| Credencial de entorno y `whoami` | PASS |
| Descubrimiento de revisión y privacidad | PASS de metadatos; candidato identificado, contenido no aceptado |
| Cinco archivos por nombre/tamaño/SHA-256 local | NOT_VERIFIED; discrepancia climática confirmada por metadatos |
| Enero 2020: 1.122 municipios, 31 días, 34.782 claves únicas | NOT_VERIFIED; sin lectura de microdatos |
| Clon temporal limpio e instalación bloqueada | NOT_EXECUTED por condición de parada |
| `uv run --locked --directory pipeline python tools/build_approved_canonical.py` | NOT_EXECUTED por condición de parada; sin duración, RSS ni identidad nueva |
| `pipeline/.venv/bin/python pipeline/tools/check_experiment_preservation.py` | PASS, código 0: 49 archivos, 22 JSON, 16 recibos T16 |
| `pipeline/.venv/bin/python -m sat_dengue_pipeline.experiment_management validate` | VALID, código 0 |
| `git diff --check origin/main...HEAD` | PASS, código 0, sobre 8202571 |
| Diff documental local | PASS: `git diff --check`, UTF-8/LF, 43 enlaces locales existentes; solo dos documentos modificados y ningún archivo nuevo no versionado |

La identidad N=3 sigue siendo
`899ba8b2c48b69dbf2e9094a6efedfa838cbfe4c800bed25fa1823503d06d52f`.
Los cambios de esta reanudación se limitan a `plan.md` y esta auditoría; EXP001,
EXP002, los JSON publicados y toda evidencia cerrada conservan sus bytes frente
al HEAD probado. No se repitieron suites completas ni las 292 pruebas artificiales
del intento previo: no hubo cambio de código y esas pruebas no resuelven la
discrepancia del contrato. No se creó clon, descargaron crudos ni ejecutaron
construcción, N=3, entrenamiento o experimentos. No se hizo commit, push, merge,
force push ni cambio del ruleset; no se atribuye CI remota a este diff documental.

**Resultado: BLOCKED; auditoría NOT_READY; T27 BLOQUEADA, 26/27.** Pendientes:
aprobación del cambio de contrato antes de continuar; después, verificación fijada
al SHA, integridad local de cinco archivos, cobertura de enero 2020 y comando real
desde clon limpio. Los gates externos de gobernanza/aprobación del HEAD final
siguen pendientes y no se volvieron a consultar.

## Intento previo: aceptación operacional incorporada a T27

El registro siguiente describe el intento anterior sobre `c729f19`, conservado
como historia. Su bloqueo por ausencia de credencial quedó resuelto en esta
reanudación; no es el diagnóstico vigente.

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
