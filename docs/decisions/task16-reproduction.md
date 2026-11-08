# Reproducción desde el release privado — tarea 16

Estado vigente: EN CURSO — validación de fábrica T16-FACTORY-XGB-S53-v1 autorizada.
Los estados BLOQUEADA de las secciones históricas describen sus respectivas reanudaciones.
Adquisición privada, construcción real/Kedro, N=3, formato, cobertura y controles
temporales aprobados. Los HTTP 401/404 anteriores se conservan como historia.
Reanudación: 2026-11-07, desde DEC-020. Progreso conservado: 15/21.

## Identidad y credencial

El usuario autorizó el dataset privado `sat-dengue/data_raw`, revisión inmutable
`a1a7f237a4baa6ffa848fabeef474f811f3b3f33`. No se permiten ramas, etiquetas ni
el release derivado anterior. Se comprobó únicamente que `HF_TOKEN` no está vacío
en el entorno del agente; su valor no se imprime ni se persiste. No se recuperan
credenciales cacheadas.

## Historial de preflight remoto

La primera consulta autenticada `HfApi.dataset_info(files_metadata=True)` resolvió el
SHA aprobado exactamente y devolvió `private=false`. El requisito de release
privado estaba incumplido en ese momento. La autenticación no acredita privacidad y no se
realizaron descargas ni lecturas de microdatos, ni pruebas de acceso anónimo.
No se cambió la visibilidad del repositorio remoto. Se solicitó al usuario
establecerlo como privado y avisar para repetir la verificación.

El usuario informó después que el dataset ya estaba privado y exigió confirmar
`private=true` antes de descargar o procesar. La segunda consulta autenticada al
mismo dataset y revisión devolvió HTTP 404 (`RepositoryNotFoundError`). No se
obtuvo un campo de privacidad: el valor anterior es histórico y no describe la
visibilidad actual. Un 404 puede deberse a acceso insuficiente; no se declara
que el dataset o la revisión hayan desaparecido. Se solicitó comprobar la cuenta
y el permiso de lectura de `HF_TOKEN`, sin compartir el valor. No se consultó la
identidad del token ni se modificaron sus permisos. Recibo de este intento en
[hf-private-access-preflight.json](../evidence/task16/hf-private-access-preflight.json).

En la reanudación solicitada el 2026-11-07 se repitió el preflight con el
`HF_TOKEN` no vacío del entorno y la misma revisión aprobada. El sandbox produjo
un `ConnectError`; tras autorizar la consulta fuera del sandbox, Hugging Face
devolvió nuevamente HTTP 404 (`RepositoryNotFoundError`) a las
2026-11-08 00:03:23 UTC (2026-11-07 en Bogotá). No se resolvió el SHA ni se
obtuvo el campo `private`; ambos gates siguen pendientes. No se descargaron
archivos, probaron credenciales cacheadas ni consultó acceso anónimo. El recibo
de este nuevo intento se conserva separado de los anteriores en
[hf-private-access-preflight-retry.json](../evidence/task16/hf-private-access-preflight-retry.json).
La tarea 16 permanece BLOQUEADA; se requiere verificar el permiso de lectura
del token del entorno sobre el dataset privado y el commit aprobado antes de
repetir el preflight. No se modificó código ni configuración ni se repitieron las
suites científicas o de producto durante este intento; `git diff --check` se
ejecutó para el registro documental.

En la siguiente reanudación, el usuario informó que `whoami` ya había validado
la cuenta `mauro114` y la organización `sat-dengue`. Se conserva esa evidencia
declarada sin repetir `whoami` ni asumir que acredita acceso al dataset desde
este proceso. `HF_TOKEN` está disponible en el entorno; no se imprime ni guarda.
Tras un `ConnectError` dentro del sandbox, se autorizaron dos consultas de
metadatos fuera del sandbox: al dataset sin revisión a las 00:13:22 UTC y al
commit aprobado a las 00:13:42 UTC del 2026-11-08 (2026-11-07 en Bogotá).
**Ambas devolvieron HTTP 401 (`RepositoryNotFoundError`)**. No se obtuvo
`private` ni SHA resuelto, por lo que no se confirma privacidad, acceso o
inexistencia del repositorio/revisión. No se cambió ni sustituyó la credencial,
ni se probaron credenciales cacheadas, acceso anónimo o descargas. El recibo
[hf-private-access-preflight-after-whoami.json](../evidence/task16/hf-private-access-preflight-after-whoami.json)
contiene solo metadatos permitidos y distingue el antecedente declarado de las
consultas observadas. La tarea 16 sigue BLOQUEADA, con 15/21 completas y tarea
17 PENDIENTE. Para continuar, el proceso del agente debe recibir una credencial
que permita consultar este dataset privado y su SHA aprobado; no debe
compartirse su valor en el chat. Sin cambios de código/configuración ni
ejecución científica. La comprobación de lock no llegó a ejecutarse porque uv
no pudo abrir su caché fuera de las rutas permitidas; no se repitieron suites.
El registro documental se valida con JSON y `git diff --check`.

El inventario remoto contiene las cinco fuentes bajo `datos-crudos/`, además
del Excel, README y atributos de Git. Los cinco tamaños coinciden con el
contrato. Los tres hashes LFS de los CSV también coinciden; los dos archivos
pequeños no tienen SHA-256 LFS en estos metadatos. No se afirma integridad local
ni verificación de sus hashes sin descargarlos. Recibo pequeño con allowlist de
metadatos en [hf-preflight.json](../evidence/task16/hf-preflight.json), sin token,
cabeceras, URLs firmadas ni microdatos.

La integración deberá mapear las rutas remotas con prefijo a los cinco nombres
locales del contrato. No se modificó el validador ni se habilitó el flujo real
mientras persiste el bloqueo de privacidad.

## Reanudación autorizada y adquisición real

El 2026-11-08 a las 00:19 UTC, `HfApi.whoami` validó desde este proceso la
cuenta `mauro114` y organización `sat-dengue`. Las consultas al dataset y al
commit aprobado devolvieron `private=true` y el SHA exacto. El usuario autorizó
continuar la tarea 16 y detenerse antes de la 17.

Se descargaron exclusivamente las cinco fuentes del commit inmutable mediante el
adaptador existente, con autenticación explícita desde `HF_TOKEN`. No se ejecutó
login ni se usaron tokens cacheados; la credencial no se imprime ni se persiste.
Los workers científicos no reciben `HF_TOKEN` y bloquean red/imports de proveedor.
El prefijo remoto `datos-crudos/` se mapea de forma cerrada a los cinco nombres
locales. Excel, README y atributos no se descargan al bundle científico.

La adquisición tardó 43,63 s y verificó **los cinco tamaños y SHA-256 completos**,
además de los encabezados CSV y esquema/procedencia JSON. Recibo:
[acquisition.json](../evidence/task16/acquisition.json). Los bytes permanecen
únicamente en `pipeline/data/01_raw/inbox/`, ignorado por Git. El manifiesto
versionado vive en `pipeline/conf/releases/approved-raw.json`; su intervalo declarado no es
una medición de los extremos crudos ni de disponibilidad histórica.

Un piloto identificó coste repetido al convertir el selector completo en cada
bloque (`Index.isin`). Se interrumpió antes de producir una salida y se sustituyó
por cortes con búsqueda binaria sobre posiciones retenidas ordenadas. También
se leen solo cuatro columnas epidemiológicas y se evita materializar todos los
diccionarios de filas a la vez. Las reglas de normalización y agregación no cambian.
La construcción medida se reinició; no se atribuye certificación al piloto.

## DEC-022: formato epidemiológico observado

El parser anterior no reconocía el sufijo localizado de medianoche. El perfil
completo de claves `INI_SIN` identifica 1.705.471 fechas localizadas y 133 vacías
en dengue; 50.098 localizadas y 3 vacías en dengue grave. Hay 1.042.282 registros
con primer componente mayor que 12 y ninguno con segundo componente mayor que
12: la convención observada es día/mes/año. Recibo sin filas:
[raw-date-format-profile.json](../evidence/task16/raw-date-format-profile.json).

Se admite exclusivamente `d/m/aaaa 12:00:00 a. m.` con espacio normal o NBSP;
se conservan los formatos ISO y día/mes previos. No hay inferencia automática,
fallback a FEC_NOT ni uso del año de notificación. Las fechas imposibles, vacías
y formatos distintos siguen excluidos por cuarentena. Una fuente no vacía sin
ninguna fecha interpretable ahora falla antes de inferir ceros. Pruebas cubren
fechas ambiguas, imposibles, sufijos distintos y la frontera diciembre/enero.

El segundo piloto se interrumpió dentro de cuarentena tras detectar esta
incompatibilidad. No produjo una salida certificada ni conteos científicos.
Se reinicia desde los bytes aprobados con la adaptación registrada en DEC-022.
El parseo puro usa una caché acotada en memoria dentro de cada proceso; los
workers N=3 siempre parten de un intérprete nuevo sin compartir derivados.

## DEC-021: Excel auxiliar y contrato científico

El release remoto puede contener `Listados_DIVIPOLA.xlsx` como archivo auxiliar.
Se elige ignorarlo durante la descarga. Su presencia remota no amplía el
inventario científico aprobado ni permite usarlo como sustituto de DIVIPOLA.
No participa en construcción canónica, normalización, imputación ni aprendizaje.

El manifiesto de adquisición y el `ResolvedBundle` que consume Kedro incluyen
exclusivamente estos cinco archivos, con los tamaños y SHA-256 de la sección 4.1
de [plan.md](../../plan.md):

- `Divipola-municipios.md`.
- `divipola-provenance.json`.
- `dengue.csv`.
- `dengue_grave.csv`.
- `google_earth_engine.csv`.

La adquisición será selectiva, sin descargar un snapshot completo. La validación
del bundle sigue rechazando un sexto archivo y cualquier sustitución del
inventario. Documentación del repositorio remoto y Excel no son fuentes Kedro.

## Construcción real medida

La primera construcción completa aprobada produjo 182.886 claves únicas de
1.122 municipios × 163 meses (`2011-06`–`2024-12`). Se conservaron 1.308.130
notificaciones de dengue y 20.022 de dengue grave. Se conciliaron por causa
los rechazos: 299.235 registros fuera del periodo de desarrollo y 7.785 con
municipio de residencia no incluido en la dimensión; no hubo eventos equivocados.

La cuarentena previa excluyó 529.927 registros desde 2025 (119.138 de dengue,
1.259 de grave y 409.530 climáticos) y 136 fechas epidemiológicas vacías.
El perfil de claves observa epidemiología entre `2006-01` y `2026-01`, y
clima entre `2007-01` y `2025-12`; las fechas de 2026 también quedan bajo la
misma cuarentena `>=2025-01`. El intervalo declarado del manifiesto no coincide con los extremos observados
de los archivos completos; no se utiliza para decidir la cuarentena o ampliar
el desarrollo. BuildConfig y TemporalPolicy conservan sus límites aprobados. Véase
[raw-temporal-coverage.json](../evidence/task16/raw-temporal-coverage.json).
No se normalizaron ni agregaron valores de esos registros. Clima aceptó
5.536.060 días municipales dentro de desarrollo; 1.808.664 días anteriores al
periodo quedaron fuera. Hay 1.046 combinaciones sin observaciones climáticas y
324 adicionales incompletas: los nueve agregados mensuales conservan 1.370 nulos
cada uno. No se infiere disponibilidad operativa histórica a partir de estos
consolidados retrospectivos.

Duración completa: 258,45 s; CPU: 257,60 s. Pico RSS de proceso: 10.560.405.504
bytes (9,84 GiB), sobre 32 GiB de RAM. Clima diario: 105,23 s; agregación mensual:
95,24 s; panel: 24,80 s. La serialización JSON determinista ocupa 66.852.080 bytes.
La selección lee por bloques, pero reúne DataFrames y materializa clima diario;
no es una implementación de memoria constante. El perfil real está medido en
este equipo de 32 GiB, no acredita ejecución con 8 GiB.
Esta construcción se conserva como **provisional**; la certificación N=3
se realiza por separado, sin consumirla. Recibo completo:
[build-real.json](../evidence/task16/build-real.json). La identidad del código
sin commit se conserva con Git SHA/dirty y hashes de los archivos fuente,
configuración y lock en [implementation.json](../evidence/task16/implementation.json).

## Certificación N=3 y preparación temporal reales

N=3 **PASSED**: tres procesos distintos, nuevos inboxes y reconstrucciones desde
crudos sin derivados compartidos. Se compararon también auditorías y bytes
completos. Los tres SHA-256 serializados son
`8fc8355af11644412b1d32a41f00ab3c369bd4de980bb0acd963c3a8c64e652c`;
el digest semántico común es
`a3326015581fd81b748820e1bce3ca2f4c5c88c2be96f08f7c822e37eb7dd722`.
Solo queda un `canonical.json` bajo `certified/` y se eliminaron los directorios
transitorios de workers. Certificación completa: 757.55 s;
reconstrucciones: 248,25 / 248,30 / 248,76 s. Mayor RSS de worker:
12,270,878,720 bytes
(11,43 GiB); RSS del controlador separado: 1,273,790,464 bytes.
Tracking local canónico `FINISHED`, run `061138f41e2d48608dc36f7f1e3987e8`;
resultado `PASSED_N3`. Recibo: [certify-real.json](../evidence/task16/certify-real.json).

El roundtrip de la salida certificada restaura esquema, orden, tipos y nulos y
reproduce exactamente los bytes y ambas huellas. Son 52 columnas,
182.886 claves sin duplicados y cero observaciones reservadas. Clima completo:
181.516 filas; predictores completos: 114.316. La cuadrícula es nacional; solo
1.120 de los 1.122 municipios tienen ejemplos utilizables bajo estos controles.

| Horizonte | Último origen | Último objetivo | Ejemplos utilizables | Positivos | Negativos |
|---|---|---|---:|---:|---:|
| T+1 | 2024-11 | 2024-12 | 89.143 | 8.536 | 80.607 |
| T+2 | 2024-10 | 2024-12 | 88.470 | 6.242 | 82.228 |

`prepare_horizon` y el guard V3 rechazaron los siguientes orígenes que cruzan
enero de 2025 antes de preparar etiquetas. No hubo componentes aprendidos.
Estos conteos describen soporte técnico retrospectivo; no acreditan latencias
operativas ni constituyen evaluación independiente o selección de modelos.
Detalle por columna/departamento/horizonte y medición de formato en
[canonical-quality.json](../evidence/task16/canonical-quality.json).

## Recursos y validación local

La ejecución real se midió en macOS arm64 con 32 GiB de RAM. El inventario de
recursos y el alcance de RSS están en
[resources.json](../evidence/task16/resources.json). RSS por proceso no equivale
al consumo físico conjunto de la máquina. Las cifras de presión de memoria de
las reanudaciones anteriores son históricas, no se reutilizan como pico medido.

Validación local del árbol actual: lock/sync y Ruff verdes; **469 pruebas** de
pipeline sin errores, fallos ni omisiones (cuatro avisos de OmegaConf); API:
28 pruebas (un aviso existente); tablero: instalación congelada, lint sin errores
(seis advertencias), 33 pruebas y build `node_server` verdes. Los cuatro CLI
sintéticos están verdes después de los cambios. Pydantic y Zod aceptan 24
documentos; los 22 JSON publicados conservan exactamente sus bytes frente a HEAD.
Recibo: [validation.json](../evidence/task16/validation.json).

No hay dependencias nuevas ni cambios en API/tablero/Docker/publicaciones.
Los cinco crudos, derivados canónicos, logs y store local están ignorados por Git.
Solo se versionan código, manifiesto sin credenciales y recibos agregados pequeños.
No se imprimió ni persistió HF_TOKEN. Los cambios documentales previos se conservan;
no se hizo commit, push, PR ni merge. La CI remota del árbol actual no se ejecutó;
se mantiene DEC-006 antes de cualquier merge.

## Gates previos y bloqueo histórico

El grafo Kedro `canonical_build` en modo `approved` completó los 14 nodos en
258,17 s, pico RSS reportado de 12.259.475.456 bytes (11,42 GiB), y produjo
exactamente el SHA-256 certificado. Se retiró HF_TOKEN del entorno antes de
arrancarlo. Recibo: [kedro-real.json](../evidence/task16/kedro-real.json).
La construcción real, integridad, cuarentena, N=3, formato, cobertura, memoria,
rendimiento y preparación temporal están verificados.

El experimento aprendido sigue **PENDIENTE DE ESPECIFICACIÓN CIENTÍFICA**. El
registro V3 de modelos permanece vacío por defecto y no hay un candidato real
predeclarado con hiperparámetros ni un calendario aprobado de los cinco roles,
embargo/disponibilidad y mínimos de soporte, ni grilla/cota FAR para el release
real. Las configuraciones de tests son artificiales y no son políticas
científicas aprobadas. Véase
[temporal-experiments.md](temporal-experiments.md). No se ejecuta una selección,
calibración, entrenamiento o evaluación real con parámetros inventados.
Los ejemplos utilizables y sus clases no sustituyen esta especificación.

Se solicitó aclaración de esa especificación mientras se completaban los gates
independientes. La tarea 16 queda BLOQUEADA por ese único pendiente y no se
marca COMPLETA; el avance continúa en 15/21. La tarea 17 permanece PENDIENTE
y no comenzó. El próximo paso exige la especificación suficiente del experimento,
no repetir la descarga ni sustituir los cinco crudos aprobados.

## Propuesta histórica y autorización de fábrica vigente

Permanecen aprobados los gates técnicos de adquisición privada de cinco fuentes,
integridad, construcción real/Kedro, cuarentena temporal, N=3, formato, cobertura,
memoria/rendimiento y validaciones locales documentadas arriba. Los recibos de
`docs/evidence/task16/` permanecen inmutables.

El bloqueo anterior por aprobación fue resuelto por la autorización explícita del
equipo para **T16-FACTORY-XGB-S53-v1**. La autoridad normativa vigente es
[task16-experiment-specification.md](task16-experiment-specification.md), aprobada
exclusivamente para validar reproducibilidad de fábrica V3. No autoriza un campeón,
uso operativo ni tarea 17. El experimento de fábrica se implementa por configuración
y sus nuevos recibos se crearán en `docs/evidence/task16/factory-experiment/`;
los recibos anteriores conservan sus bytes. El resultado de fábrica se documentará
a continuación. Las métricas históricas anteriores no se atribuyen a esta ejecución.
