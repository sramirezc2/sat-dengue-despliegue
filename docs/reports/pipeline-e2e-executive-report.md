# Reporte ejecutivo — fábrica E2E SAT DENGUE V3

Fecha de elaboración: 2026-11-09. Alcance: capacidades integradas al cierre local
T24 (`e1db85d`) y síntesis documental de T25, sin cambios científicos.
[plan.md](../../plan.md) es la única autoridad de tareas, estados y progreso;
este reporte no mantiene un registro paralelo ni certifica disponibilidad remota.

Lectura recomendada: equipo y jurados, secciones de resumen, límites y decisiones;
mantenedores y agentes, arquitectura, operación y verificación del PR.

## 1. Resumen ejecutivo

**La fábrica está técnicamente reproducible dentro del alcance de las recetas y
entornos acreditados.** T16 conserva una certificación canónica y una reproducción
E2E N=3 con identidades iguales; es evidencia de ingeniería, no de superioridad
científica ni equivalencia universal entre plataformas. La
[comparación E2E histórica](../evidence/task16/factory-experiment/n3-comparison.json)
y la [reproducción documentada](../decisions/task16-reproduction.md) fijan ese alcance.

V3 reúne construcción desde crudos, controles temporales, preparación, evaluación,
registro experimental y publicación compatible con el producto. Las correcciones
operativas conservan esa ciencia y su evidencia. La
[validación local T24](../evidence/task24/operational-validation.json) identifica el
código probado, los resultados y las comprobaciones desde checkout limpio.

**El contrato científico permanece `PROPUESTA_PARA_APROBACION`, no existe campeón
seleccionado y G5 permanece `NOT_APPROVED`.** Los estados están documentados en el
[contrato propuesto](../experiments/contrato.md) y en la
[especificación histórica T16](../decisions/task16-experiment-specification.md).
Este reporte no autoriza operación sanitaria ni afirma que la fábrica respondió
la pregunta de grado. Publicación de código, revisión y autorización operativa
son decisiones diferentes.

## 2. Problema que resuelve la fábrica

El equipo necesita ejecutar recetas trazables sin depender de notebooks personales,
derivados entregados manualmente o un entorno de otro integrante. La fábrica
vincula fuentes, código, dependencias, configuración, protocolo y evidencia;
rechaza entradas incompatibles y conserva intentos y conclusiones. V3 es la fuente
activa; V2 queda como antecedente, sin dependencia de ejecución.
[Diseño y procedencia](../../PLAN_pipeline_e2e_experimentos_sat_dengue.md).

## 3. Arquitectura y fronteras

```text
pipeline/ -> datos/resultados/ -> app/api/ -> app/dashboard/
```

`pipeline/` contiene Kedro y dependencias científicas propias. La API sirve JSON
persistidos, sin importar Kedro ni ejecutar inferencia; el tablero consume la API.
El pipeline no importa ni escribe en `app/`. La frontera de entrega al producto
es `datos/resultados/`; cachés y derivados privados viven en `pipeline/data/`.
[Autoridad arquitectónica](../architecture/pipeline-e2e.md).

## 4. Flujo desde fuentes crudas hasta publicación

El flujo implementado distingue las siguientes responsabilidades:

1. Adquirir un release inmutable y verificar sus archivos locales.
2. Validar contrato crudo y proyectar claves temporales.
3. Aplicar cuarentena antes de normalizar, agregar o unir valores.
4. Construir, validar y serializar el canónico local.
5. En una ejecución experimental aprobada, preparar roles, ajustar, congelar,
   predecir y evaluar sin realimentar decisiones con evaluación.
6. Conservar evidencia agregada y someter conclusiones a revisión humana.
7. Publicar únicamente entradas locales aprobadas mediante el publicador separado.

El helper operacional termina en construcción provisional. `experiment_run` no
publica automáticamente resultados ni convierte métricas agregadas en predicciones
municipales. Véanse [operación](../operations/pipeline-operations.md#flujos-y-comandos)
y [publicación](../decisions/deployment-publication.md).

## 5. Adquisición desacoplada

`DataSource` y `ResolvedBundle` separan transporte de ciencia. El manifiesto exige
**cinco archivos**, con nombres, tamaños y SHA-256 fijados; el inventario está en
[approved-raw.json](../../pipeline/conf/releases/approved-raw.json). No se admite
una tabla canónica remota como fuente científica ni el Excel auxiliar como insumo.

Hugging Face es el origen privado fijado. Local, Zenodo y S3 tienen distintos
alcances: el adaptador Zenodo actual es público y S3 científico está probado con
un cliente simulado; no constituyen transportes privados operativos equivalentes.
El S3 de la API mueve resultados terminados, con responsabilidad independiente.
[Contratos](../../pipeline/src/sat_dengue_pipeline/acquisition/contracts.py),
[adaptadores](../../pipeline/src/sat_dengue_pipeline/acquisition/sources.py) y
[límites de migración](../operations/pipeline-operations.md#límites-y-migración-de-almacenamiento).

## 6. Construcción canónica y reproducibilidad

El canónico aprobado comprende **1.122 municipios, 163 meses y 182.886 claves**,
entre `2011-06` y `2024-12`, según el
[certificado histórico](../evidence/task16/certify-real.json). Reutiliza dominio
para canal, lags y predictores; verifica cardinalidad, conservación, tipos, orden
y nulos. Un mes incompleto no se completa artificialmente con clima cero.
[Contrato de construcción](../decisions/raw-canonical-build.md).

`canonical_build` produce un **provisional**. `canonical_reproducibility` es un
flujo separado que reconstruye en procesos/directorios aislados y compara las
identidades antes de certificar. La N=3 histórica no certifica un release,
productor o dependencia futuros. Tampoco debe suponerse que `experiment_run`
realiza N=3 automáticamente: su
[adquisición y construcción](../../pipeline/src/sat_dengue_pipeline/experiment_management/runner.py)
llama una vez al constructor y verifica el artefacto.

## 7. Exclusión de 2025

**2025 es evidencia retrospectiva consumida**, no un holdout intacto. La cuarentena
excluye claves desde `2025-01` antes de normalizar o agregar; el guard también
rechaza orígenes, objetivos y disponibilidades reservadas, incluidos cruces de
horizonte desde el año anterior. Las autoridades son `TemporalPolicy` y
`guard_development`, no un filtro paralelo.
[Política implementada](../../pipeline/src/sat_dengue_pipeline/domain/temporal.py)
y [tratamiento científico](../experiments/contrato.md#5-regla-de-información-disponible-y-tratamiento-temporal).

Los JSON históricos publicados pueden conservarse con su procedencia; no son
insumos para desarrollar modelos. Una confirmación requiere una cohorte que no
haya intervenido en las decisiones previas y una política aprobada para admitirla.

## 8. Fábrica de experimentos y estados

```text
PROPOSED -> APPROVED -> RUNNING -> COMPLETED | BLOCKED
```

Se verifican ID, rutas, hashes y aprobación antes de adquirir o ajustar. Cada
intento reserva evidencia exclusiva, conserva inventario verificable y tracking
MLflow local; Git conserva la historia aunque se pierda ese índice. Un cálculo
exitoso deja el registro en RUNNING hasta recibir conclusiones humanas válidas.
Una repetición requiere identidad nueva. La integridad estructural no prueba por
sí sola revisión independiente ni validez científica.
[Manual](../experiments/manual_pipeline.md) y
[administración experimental](../decisions/experiment-management.md).

**EXP001 y EXP002 son fixtures**, con resultado `NOT_APPLICABLE`; prueban la
infraestructura, no aportan resultados científicos de dengue.
[Registro versionado](../experiments/registry.yml).
**EXP003 no forma parte del HEAD local de referencia de este reporte.** Sus
menciones en manuales son ejemplos, no una receta local aprobada. Trabajo en otra
rama o PR debe revisarse e integrarse antes de atribuirle capacidades a V3.
[Configuraciones integradas](../../pipeline/conf/experiments/).

## 9. Portabilidad

Hay evidencia histórica de fixtures en macOS, Ubuntu, Windows y Colab, identificada
por commit en [portabilidad T15](../decisions/portability.md). T24 comprobó el
helper y su instalación bloqueada desde un checkout local con espacios en la
ruta, mediante dobles y archivos artificiales.
[Recibo T24](../evidence/task24/operational-validation.json).

Esto no acredita construcción real en todos esos sistemas ni valida commits
posteriores. Cada HEAD publicado debe superar su matriz remota. El lock no
sustituye runtimes nativos; los requisitos y diferencias de shell están en la
[guía desde clon limpio](../operations/pipeline-operations.md#preparación-desde-un-clon-limpio).

## 10. Seguridad y privacidad

Los microdatos epidemiológicos permanecen privados; crudos, matrices, modelos,
credenciales y predicciones por fila quedan fuera de Git. La evidencia permite
agregados minimizados y hashes, sin rutas privadas o mensajes completos de
proveedores. El secreto se proporciona explícitamente en el entorno, sin login
cacheado como fallback.

La revisión de seguridad cerrada obtuvo `APPROVED_WITH_LIMITATIONS`; conserva
riesgos residuales de dependencias, permisos externos, escritor local con iguales
privilegios y autenticidad del productor de resultados. No certifica la seguridad
actual de proveedores o despliegue ni garantiza ausencia universal de secretos.
[Informe y responsables](../security/security-review.md).

## 11. Operación desde clon limpio

Desde la raíz de un checkout de la revisión aprobada, prepare el entorno según
la [guía operativa](../operations/pipeline-operations.md#preparación-desde-un-clon-limpio):

```sh
uv sync --locked --project pipeline
```

Para una operación privada previamente autorizada, configure el secreto mediante
[lectura oculta apropiada al shell](../operations/pipeline-operations.md#autenticación-segura)
y ejecute:

```sh
uv run --locked --directory pipeline python tools/build_approved_canonical.py
```

El helper usa el intérprete actual, listas de argumentos y cwd explícito; detiene
el flujo si falla adquisición y retira el token del proceso Kedro. Su workspace
relativo es exclusivo. Los comandos internos de diagnóstico siguen disponibles:

```sh
uv run --locked --directory pipeline python tools/acquire_private_raw.py
uv run --locked --directory pipeline kedro run --pipelines canonical_build --params canonical.mode=approved,canonical.workspace=data/canonical-approved-manual,canonical.tracking=false
```

Esos comandos privados no se ejecutaron para redactar este informe. La ayuda
`uv run --locked --directory pipeline python tools/build_approved_canonical.py --help`
no adquiere ni construye. Implementación:
[helper](../../pipeline/tools/build_approved_canonical.py) y
[adquiridor](../../pipeline/tools/acquire_private_raw.py).

## 12. Validaciones acumuladas

La tabla resume **evidencia local histórica de T24**, no una nueva ejecución de
esas suites en T25 ni CI del commit que contenga este reporte. Todas las cifras y
resultados proceden del [recibo T24](../evidence/task24/operational-validation.json),
que identifica el código probado `5768331` y sus límites.

| Gate | Resultado registrado |
|---|---|
| Lock, sincronización bloqueada, Ruff y registro | PASS / VALID |
| Pipeline | 578 pruebas, 6 avisos existentes |
| API | 35 pruebas, 1 aviso existente |
| Tablero | Frozen install, lint, 55 pruebas y build; 6 avisos de lint |
| Contratos de consumidores | 22 documentos Pydantic y 22 Zod |
| Regresiones operativas nuevas | 29; checkout limpio y ayuda/error controlado PASS |
| Preservación protegida | 49 archivos, 22 JSON publicados y 16 recibos previos T16 |
| Skills, enlaces, filtros, higiene y diff | PASS dentro del alcance declarado |

T25 exige validación documental proporcional, registro y preservación. T26 exige
repetir el gate acumulado antes de publicar y consultar checks sobre el HEAD
remoto nuevo. La auditoría de merge corresponde a T27.
[Secuencia y gates](../../plan.md).

## 13. Entregables

| Entregable | Autoridad o evidencia |
|---|---|
| Arquitectura y secuencia | [Arquitectura](../architecture/pipeline-e2e.md), [plan maestro](../../PLAN_pipeline_e2e_experimentos_sat_dengue.md), [estado operativo](../../plan.md) |
| Adquisición y canónico | [Subproyecto](../../pipeline/README.md), [release](../../pipeline/conf/releases/approved-raw.json), [certificación](../evidence/task16/certify-real.json) |
| Reproducción de fábrica | [Especificación](../decisions/task16-experiment-specification.md), [comparación de identidades](../evidence/task16/factory-experiment/n3-comparison.json) |
| Registro, conclusiones y tracking | [Manual](../experiments/manual_pipeline.md), [registro](../experiments/registry.yml), [diseño](../decisions/experiment-management.md) |
| Producto preservado | [Contrato/publicador](../decisions/deployment-publication.md), [resultados](../../datos/resultados/) |
| Operación y recuperación | [Guía](../operations/pipeline-operations.md), [catálogo de skills](../agents/skills-catalog.md), [validación operacional](../evidence/task24/operational-validation.json) |
| Revisiones y límites | [Ciencia](../reviews/scientific-review.md), [seguridad](../security/security-review.md), [propuesta de contrato](../experiments/contrato.md) |

## 14. Limitaciones científicas

T16 valida ingeniería, no superioridad científica. En `experiment_run` siguen
pendientes el canal condicionado, presupuesto comparable, carga de falsas alertas
como decisión, controles negativos e incertidumbre confirmatoria propuesta. Las
referencias actuales son prevalencia de entrenamiento y persistencia de no nuevo
inicio; vencer esta última no acredita utilidad. El bootstrap municipal descriptivo
no equivale al intervalo confirmatorio propuesto ni se integra automáticamente en
la salida del motor registrado.
[Brechas del contrato](../experiments/contrato.md#16-compatibilidad-con-la-fábrica-v3-actual),
[revisión científica](../reviews/scientific-review.md) y
[configuración implementada](../../pipeline/src/sat_dengue_pipeline/experiment_management/configuration.py).

No se acredita reproducción del banco histórico, generalización prospectiva,
latencia real de fuentes o efecto causal sanitario. El filtro de entradas completas
y la elegibilidad al origen restringen cobertura. Completar infraestructura no
resuelve estas limitaciones ni convierte retrospectiva en confirmación.

## 15. Limitaciones operacionales

La certificación canónica histórica observó un máximo de **11,43 GiB RSS por
worker**, en un equipo de **32 GiB**. La ejecución con **8 GB no está acreditada**;
no se deduce un mínimo universal de RAM. RSS por proceso no equivale al consumo
total y el constructor no tiene memoria constante.
[Recibo de certificación](../evidence/task16/certify-real.json),
[entorno](../evidence/task16/resources.json) y
[mediciones y tiempos](../operations/pipeline-operations.md#recursos-medidos).

Los recibos operacionales se guardan exclusivamente bajo `pipeline/data/acquisition/`.
Un fallo del filesystem puede impedir conservarlos. El store MLflow es local y no
incluye reparación automática; las promociones del publicador son atómicas por
archivo, sin aislamiento multiarchivo frente a lectores activos. Recuperación y
nuevas publicaciones exigen revisión según el caso.
[Operación](../operations/pipeline-operations.md#recuperación-y-troubleshooting).

## 16. Riesgos aceptados o pendientes

| Riesgo | Tratamiento y responsable |
|---|---|
| Interpretar reproducibilidad como utilidad | Equipo científico: conservar las limitaciones y aprobar un protocolo nuevo antes de evaluar |
| Cambiar cohortes o decisiones tras observar resultados | Revisores: receta congelada, soporte común y evidencia exclusiva |
| Perder acceso, vulnerabilidades o perímetro inseguro | Datos/infraestructura y mantenedores: controles y seguimiento SEC-04 a SEC-09 del informe de seguridad |
| Publicar un HEAD sin protección efectiva | Administrador/revisor: ruleset, checks obligatorios, aprobación independiente y conversaciones resueltas |
| Atribuir CI antigua a cambios nuevos | Mantenedor: verificar SHA y matriz después de cada push autorizado |

Los riesgos y sus condiciones de seguimiento están en las revisiones
[científica](../reviews/scientific-review.md) y de
[seguridad](../security/security-review.md). Este reporte no actualiza su severidad
ni cierra acciones externas no verificadas.

## 17. Decisiones humanas pendientes

El equipo debe resolver la pregunta y población primaria, comparador decisivo,
presupuesto, tolerancias, incertidumbre y cohorte confirmatoria de la
[propuesta científica](../experiments/contrato.md#17-aprobación-y-cambios-al-contrato).
Debe revisar toda receta antes de ejecutarla y sus conclusiones después.

Mantenedores y propietario deben autorizar publicación de código y eventual
corrección del ruleset, asegurar revisión independiente del HEAD final y decidir
el merge. Habilitar operación sanitaria requiere una evaluación y gobernanza
adicionales; ni el merge ni este reporte conceden esa autorización.

## 18. Qué puede y qué no puede afirmarse

| Afirmación | Alcance defendible |
|---|---|
| La fábrica está técnicamente reproducible | Sí, para las recetas, identidades y entornos acreditados por evidencia enlazada |
| T16 demuestra superioridad predictiva | No; demuestra reproducción de una receta técnica |
| EXP001/EXP002 son resultados científicos de dengue | No; son fixtures de aceptación |
| EXP003 está integrado o aprobado | No en el árbol de referencia inspeccionado |
| El contrato científico ya rige por aprobación humana | No; conserva estado de propuesta |
| Existe campeón o autorización sanitaria | No; G5 sigue NOT_APPROVED y champion NOT_SELECTED |
| Una CI histórica habilita el merge actual | No; se requiere verificar el HEAD final y todos los gates externos |

Las evidencias respectivas están en los apartados de resumen, fábrica,
validaciones y limitaciones de este reporte; no se extrapolan sus conclusiones.

## 19. Trabajo científico posterior al merge

Requiere otro alcance: aprobar el contrato, reconciliar el trabajo externo que se
quiera integrar, definir población y ventanas, resolver la necesidad de ampliar
cobertura, implementar comparadores/métricas y registrar una receta nueva con
referencia y revisión previa. No reutilizar identidades cerradas ni ajustar el
protocolo para coincidir con cifras históricas. Las exploraciones ya observadas
deben declararse al evaluar independencia. La reproducción y revisión posterior
conservarán resultados desfavorables y limitaciones.
[Diseño científico pendiente](../../PLAN_pipeline_e2e_experimentos_sat_dengue.md#d10-protocolo-común-de-evaluación-de-inicios)
y [manual](../experiments/manual_pipeline.md).

## 20. Guía breve de verificación del PR

En el [PR único](https://github.com/sramirezc2/sat-dengue-despliegue/pull/1):

- cotejar rama de origen, base, SHA publicado y árbol local;
- repetir los gates locales exigidos por T26 y comprobar preservación;
- revisar los checks exactos y su SHA, incluyendo componentes de producto y matriz;
- comprobar que el ruleset exige esos checks y resolución de conversaciones;
- verificar una aprobación independiente vigente para el HEAD final;
- confirmar acceso a reporte, revisiones y limitaciones en la descripción;
- completar la auditoría final sin confundir `mergeable` con autorización.

Esta es una guía, no un veredicto `READY_TO_MERGE`. T26 y T27 permanecen sujetos a
sus gates y autorizaciones en [plan.md](../../plan.md). Ninguna CI previa valida
el commit de este reporte.

## 21. Preguntas frecuentes

**¿El comando único deja un modelo listo?** No: termina en canónico provisional.

**¿Hay que ejecutar T16 o usar credenciales para revisar este reporte?** No. Se
consulta evidencia versionada y se usan comprobaciones documentales de lectura.

**¿El tablero muestra una autorización operativa?** No. Conserva resultados
históricos con G5 `NOT_APPROVED` y campeón `NOT_SELECTED`.

**¿Puede agregarse otra familia?** El contrato neutral ofrece un punto de extensión,
pero la configuración registrada solo admite las familias integradas. Hace falta
implementación, pruebas, receta y aprobación; una propuesta no crea esa capacidad.

**¿Puede perderse la historia al perder MLflow?** El registro y los inventarios Git
conservan la evidencia agregada; no prometen recuperar microdatos o modelos ausentes.

**¿Este informe permite hacer push o merge?** No: ambos tienen gates explícitos;
el merge queda reservado al usuario tras revisar la auditoría final.

## 22. Próximos pasos

Cerrar T25 localmente y solicitar la autorización externa requerida antes de
iniciar T26. Después, publicar normalmente en la rama existente, actualizar la
descripción y verificar la CI del nuevo HEAD. T27 deberá revisar protección,
conversaciones y aprobación independiente; cualquier cambio remoto del ruleset
se mostrará y aprobará antes de aplicarse. Si falta una condición, no se declara
`READY_TO_MERGE`. El último paso es revisión humana; no se ejecuta merge automático.
