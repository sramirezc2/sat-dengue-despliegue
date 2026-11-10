# Construcción canónica desde crudos — tarea 13

DEC-015/016 sustituyen la entrega de derivados por cinco fuentes crudas privadas.
El inventario aprobado permanece fijo en `plan.md` y `raw/contract.py`. El nuevo
campo `release_kind: raw_sources` viaja al bundle como metadato neutral; los
contratos anteriores conservan sus hashes y quedan fuera de la nueva ruta
científica. La adquisición valida revisiones, nombres remotos y destinos antes
de transferir; desde `ResolvedBundle` ninguna función científica selecciona un
proveedor. La fábrica se carga perezosamente al solicitarla.

## Alcance de la evidencia

Los cinco archivos locales coincidieron en inventario, bytes y SHA-256 con la
autorización. Solo se verificaron esos metadatos, encabezados CSV y nombres de
campos JSON. El Excel se identificó como evidencia, sin abrirlo. No se procesaron
filas científicas reales, no se leyó V2, no se descargó ningún release remoto.

Las fuentes artificiales se generan por código, sin CSV versionados: dos
municipios ficticios, 84 meses (2018–2024), 168 claves. Ese perfil exige los mismos
nombres y encabezados, pero declara sus propios hashes; no permite sobrescribir
el aprobado. Otra prueba genera una dimensión artificial de 1.122 municipios y
comprueba los 163 meses y 182.886 claves. No equivale a reconstruir la tabla
científica nacional. Esta distinción es DEC-017.

## Contratos y reglas

La verificación de todos los bytes precede a la lectura de encabezados/esquemas.
La proyección carga solo residencia/INI_SIN o municipio/fecha. La cuarentena
utiliza `TemporalPolicy.reserved_start`; fechas ausentes o inválidas se rechazan
sin fallback. Los selectores de fila son transitorios; la auditoría contiene
solo conteos y digest del multiconjunto de claves excluidas. Los valores se
cargan como texto en chunks y se filtran antes de normalizarlos. La integridad
se verifica de nuevo antes de serializar, detectando ediciones concurrentes.

DIVIPOLA exige `resultado`, `conteo`, códigos coherentes y únicos y procedencia
con autoridad y hash del catálogo coincidente. Esto verifica el vínculo de
procedencia, sin atribuir validación histórica independiente. Se admiten fechas
ISO `AAAA-MM-DD` o `DD/MM/AAAA`, opcionalmente con medianoche; otros formatos se
rechazan y cuentan. Códigos enteros ASCII reciben padding al ancho DANE. Estos
contratos conservadores se comprobarán contra filas reales en tarea 16.

Cada evento 210/220 cuenta por fila aceptada, aun repitiendo CONSECUTIVE. Solo
residencia e INI_SIN definen municipio y mes; FEC_NOT/notificación no intervienen.
Se reconcilian input, reserva, fecha inválida, aceptados y causas mutuamente
excluyentes: evento incorrecto, residencia inválida, municipio desconocido y
periodo fuera de cobertura. No se deduplican microdatos.

Clima exige 18 columnas, coherencia de código/fecha/año/mes/día del año y unicidad
municipio-día. Vacíos son ausencias; valores no numéricos o no finitos fallan.
Se ordena por fecha y usa `math.fsum`: las primeras cuatro variables de `CLIMATE`
son sumas y las cinco restantes medias. Cada agregado exige todos los días
válidos del mes por variable. No se rellena clima ni días ausentes con cero.

Los joins declaran dimensión `many_to_one` y fuentes mensuales `one_to_one`, con
rechazo previo de duplicados/huérfanos. Solo los conteos dentro de cobertura
epidemiológica explícita se completan con cero. Canal, lags, roles y predictores
se delegan a `domain/canonical.py`. Se comprueban conteos, esquema/orden/tipos/nulos
y claves completas. `guard_development` verifica ambos horizontes: diciembre de
2024 permanece como observación; los últimos orígenes admitidos son noviembre
para T+1 y octubre para T+2. No hay otro guard temporal.

## Serialización y certificación

JSON UTF-8 determinista conserva floats sin redondeo, ausencias como `null`,
esquema/tipos/orden explícitos y versión de formato. El digest semántico cubre
esquema y valores; el SHA serializado incluye además el sobre de formato. La
ruta depende del digest semántico. Temporal, fsync y reemplazo atómico publican
un archivo completo sin introducir otra dependencia.
`load_canonical` restaura los tipos y el orden de roles del contrato V3; una
prueba de ida y vuelta exige igualdad exacta del DataFrame y su esquema.

`canonical_build` produce una salida **provisional**. El pipeline separado
`canonical_reproducibility` no la consume: ejecuta tres intérpretes y directorios
nuevos, cada uno con copias de los cinco crudos verificadas de nuevo. Workers
bloquean red/DNS, proveedores y publicaciones/V2; en modo fixture también bloquean
datos reales. Cada proceso ejecuta los mismos productores sin caché canónica.
Se comparan ambos digests, bytes completos y auditorías. Los bytes incluyen
esquema, orden, tipos, claves, valores y nulos. Se eliminan los temporales y se
libera un solo `canonical.json` certificado. `certify_then_consume` invoca al
consumidor únicamente tras aprobar N=3. Estos pipelines no entrenan modelos.

El observador compartido `LocalTracker.record_canonical` opera después del
cálculo y está deshabilitado por defecto; así funciona sin MLflow instalado.
Al habilitarlo guarda un run real y JSON agregado de allowlist cerrada:
manifiesto, cinco hashes, Git SHA/dirty, configuración, lock, cuarentena, cobertura/nulos,
etapas/rechazos, digest canónico, tres hashes y `PASSED_N3`. Construcciones simples
son `UNCERTIFIED`. Comparte persistencia/lifecycle/inventario del tracking anterior,
sin filas, valores, municipios, rutas o credenciales.

Identidad congelada del fixture, sin valor científico:

- Semántica: `26cc689566b05ffaf46a42aaa8311cca0ffc3137e31af6f64cfb1e9834f6b957`.
- SHA serializado: `4ca14c3c07079130606a91274a516e083b513c6a1a7afe41d8df92be9b3bb046`.

## Diferido

Tarea 16 conectará el release privado con autenticación individual y revisión
inmutable, comprobará cobertura/formatos sobre filas reales y ejecutará N=3 real.
La autenticación privada HF aún no está conectada. No se certifican memoria ni
tiempo del volumen completo: panel y selectores se mantienen en memoria y JSON
prioriza exactitud sobre tamaño. Matriz multiplataforma y revisión científica
independiente siguen pendientes. No se seleccionan modelos, umbrales o campeón.
