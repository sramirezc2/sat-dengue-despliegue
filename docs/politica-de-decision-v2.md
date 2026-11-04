# Propuesta de revisión de la política de decisión de la etapa 5

**Estado:** propuesta, no vigente. Requiere decisión de la autoridad declarada
en el artefacto, que es Mauricio.
**Fecha:** 4 de noviembre de 2026.
**Política que revisa:** `docs/product/stage-5/champion_decision_policy_v1.json`,
versión 1.0.0, SHA-256 `29b5d6d7924c74d0c0b1f3cd2e588d1ab587a22c3f59b64d385469246f7a4ec8`.
**Efecto sobre decisiones ya registradas:** ninguno. El `NOT_APPROVED` del 21 de
octubre de 2026 se conserva tal como está, con su autoridad y su motivo.
**Archivo legible por máquina:** `politica-de-decision-v2.json`, en esta misma
carpeta.

---

## 0. Advertencia que va primero

Quien redacta esta propuesta **ya observó los resultados de los candidatos**
antes de redactarla. Esa es exactamente la situación en que una revisión de
criterios se vuelve un mecanismo para ganar en vez de un mecanismo para medir.

Tres decisiones se tomaron para contener ese riesgo, y conviene juzgar la
propuesta por ellas antes que por su contenido:

1. **Los dos umbrales numéricos no se tocan.** Siguen siendo 10,0 y 5,0, los de
   v1. Cualquier número elegido ahora estaría contaminado por el conocimiento
   de los resultados.
2. **Se exigen controles negativos obligatorios.** Si un ranking aleatorio,
   alertar sobre todo, o el canal inflado con alertas al azar obtienen veredicto
   favorable, la aplicación de la política es nula. Esto es verificable por
   terceros y no depende de la buena fe de quien redacta.
3. **Cada cambio se midió por separado.** No se presenta v2 como un paquete que
   hay que aceptar entero: la sección 4 muestra qué pasa aplicando un cambio a
   la vez, y **dos de los tres cambios, aislados, producen una compuerta
   inservible.** Eso es la evidencia de que v2 no es una colección de ajustes
   convenientes sino el conjunto mínimo coherente.

La primera aplicación de v2 es por tanto **exploratoria, no confirmatoria**. Un
veredicto confirmatorio exige una cohorte que no haya participado en la
revisión: los datos de la línea E cuando lleguen, o meses futuros. El bloque
reservado de 2025 es evidencia consumida y no se reutiliza.

---

## 1. Los tres defectos

Cada uno con su evidencia en los artefactos registrados, no de memoria.

### D1 · La línea base no detecta el evento que la política persigue

v1 compara contra **persistencia**. La persistencia alerta cuando el mes en
curso ya está en exceso, y un inicio exige por definición que no lo esté. En
T+1 la persistencia detecta por tanto **cero inicios por construcción**.

Evidencia, de `comparison.csv` de la corrida registrada, horizonte 1:

| Candidato | Alertas emitidas | Inicios detectados | Inicios reales |
| --- | --- | --- | --- |
| persistence | 253 | **0** | 86 |

Consecuencias, las dos malas en direcciones opuestas:

- El criterio de detección se vuelve **vacío**: ganar 10 puntos sobre cero lo
  logra cualquier cosa.
- El criterio de falsas se vuelve **casi insatisfacible**: la razón de falsas de
  la persistencia es baja precisamente porque predecir "ya está en exceso, seguirá
  en exceso" es fácil y acertado. Cualquier detector de inicios tiene que alertar
  donde el exceso **todavía no está**, y eso eleva mecánicamente su razón de
  falsas.

La persistencia sería la línea base correcta si el objetivo fuera predecir
exceso. El defecto es un desajuste entre el objetivo declarado y la línea base
elegida.

### D2 · El denominador de la carga de falsas lo elige el candidato

v1 mide `false_alarm_ratio = falsas / alertas emitidas`. Si una regla emite la
mitad de las alertas con las mismas falsas absolutas, su razón se duplica,
mientras la carga real sobre la vigilancia es idéntica.

Evidencia, corte 2018-12, T+1:

| Regla | Alertas | Falsas (absolutas) | Razón |
| --- | --- | --- | --- |
| canal endémico | 208 | 27 | 13,0 % |
| candidato de la tanda 5 | 69 | **27** | **39,1 %** |

Las mismas 27 falsas. La misma cantidad de investigaciones desperdiciadas. Una
razón tres veces peor, solo porque el denominador es una decisión del candidato.

Y hay un agravante: en ese corte el canal alerta sobre **208 de 380**
municipio-mes, el 55 %. Una regla que alerta sobre más de la mitad de la
población obtiene una razón de falsas baja y pasa la compuerta. Una que alerta
sobre el 18 % y detecta dos veces y media más inicios, no.

### D3 · Una alerta se juzga contra un evento distinto del que la política persigue

Este es el más profundo y el más difícil de ver. v1 mide la **sensibilidad sobre
inicios** y la **falsa alarma sobre excesos**. Es decir, una alerta sobre un
municipio que ya está en exceso cuenta como **correcta**, aunque no pueda
detectar ningún inicio.

Evidencia, de la misma corrida, horizonte 1:

| Candidato | Emitidas | Falsas | "Verdaderas" | Inicios detectados |
| --- | --- | --- | --- | --- |
| persistence | 253 | 102 | **151** | **0** |
| xgboost | 350 | 177 | 173 | 22 |
| gam | 321 | 151 | 170 | 20 |

La persistencia acumula 151 alertas contadas como verdaderas y detecta cero
inicios. La política pide detección de inicios en un eje y premia predicción de
excesos en el otro. Es una inconsistencia interna de v1, visible en el papel,
sin necesidad de ningún dato.

---

## 2. Los tres cambios

| Defecto | Cambio | Razón |
| --- | --- | --- |
| D1 | Línea base pasa de **persistencia** a **canal endémico**. La persistencia se conserva como referencia descriptiva obligatoria. | El canal es la regla que la vigilancia usa hoy, así que "mejor que el canal" es la decisión que importa; y detecta inicios, así que la comparación es sobre el mismo evento. La persistencia sigue reportándose porque muestra cuánto se logra prediciendo la pura continuación. |
| D2 | Carga de falsas pasa de **falsas / alertas emitidas** a **alertas que no son inicio por cada 100 municipio-mes**. | El denominador lo fija la cohorte y no el candidato. Mide la carga real sobre la vigilancia: investigaciones desperdiciadas por unidad de capacidad. |
| D3 | Una alerta se juzga **verdadera si coincide con un inicio**, no si el municipio está en exceso. | Los dos ejes de la decisión pasan a medirse sobre el mismo evento que la política declara perseguir. |

Y dos cambios de procedimiento, no de criterio:

| Añadido | Razón |
| --- | --- |
| **Veredictos de tres valores**: `cumple`, `no cumple por efecto` (la estimación puntual ya falla) y `precisión insuficiente` (la puntual cumple, la cota no). v1 reportaba un solo `does_not_meet`. | Un rechazo por ancho de intervalo y un rechazo por mal desempeño piden acciones opuestas: conseguir más datos, o descartar el candidato. v1 no permitía distinguirlos. |
| **Controles negativos obligatorios** junto a cada aplicación. | Es la única protección verificable contra una política revisada por quienes evalúa. Ver sección 0. |

**Lo que no se cambia:** los umbrales de 10,0 y 5,0; la regla de las dos cotas
del intervalo; la precisión promedio como métrica de ranking con AUROC
complementario; la separación por horizonte; la cohorte reservada anual; y todo
el bloque `mvp_boundary`, de modo que el tablero desplegado sigue publicando
resultados de evaluación con su estado declarado en pantalla.

---

## 3. Qué dice v2 sobre los candidatos actuales

Horizonte T+1, los tres cortes evaluables, intervalos por remuestreo de mes
objetivo con 2000 réplicas y semilla 42. Cortes de validación propios: **no** el
bloque reservado de 2025, que es evidencia consumida.

| Corte | Candidato | Alertas | Inicios | Sens. | Carga /100 mm | Ganancia pp [IC] | Δ carga [IC] | Veredicto |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2018-12 | canal (base) | 208 | 17 | 28 % | 50,3 | — | — | — |
| | · persistencia | 207 | 0 | 0 % | 54,5 | −28,3 [−40,7; −16,1] | +4,2 [1,1; 6,8] | no cumple |
| | vigente (tanda 4) | 69 | 33 | 55 % | 9,5 | +26,7 [9,3; 45,2] | −40,8 [−52,4; −28,2] | precisión insuf. |
| | **G (tanda 5)** | 69 | 42 | 70 % | 7,1 | +41,7 [28,6; 53,3] | −43,2 [−52,9; −31,3] | **cumple** |
| | B degradado | 69 | 21 | 35 % | 12,6 | +6,7 [−16,1; 35,0] | −37,6 | no cumple |
| | · aleatorio | 69 | 9 | 15 % | 15,8 | −13,3 [−31,2; 1,6] | −34,5 | no cumple |
| | · alertar todo | 380 | 60 | 100 % | 84,2 | +71,7 | +33,9 [25,0; 44,2] | no cumple |
| | · canal inflado | 258 | 27 | 45 % | 60,8 | +16,7 | +10,5 [6,8; 14,7] | no cumple |
| 2022-12 | canal (base) | 204 | 14 | 25 % | 50,0 | — | — | — |
| | vigente (tanda 4) | 96 | 38 | 67 % | 15,3 | +42,1 [29,8; 49,2] | −34,7 | cumple |
| | **G (tanda 5)** | 96 | 49 | 86 % | 12,4 | +61,4 [46,8; 70,8] | −37,6 | **cumple** |
| | B degradado | 96 | 25 | 44 % | 18,7 | +19,3 [2,1; 32,3] | −31,3 | precisión insuf. |
| | · aleatorio | 96 | 17 | 30 % | 20,8 | +5,3 [−15,6; 20,0] | −29,2 | no cumple |
| 2024-06 | canal (base) | 203 | 21 | 44 % | 47,9 | — | — | — |
| | vigente (tanda 4) | 203 | 48 | 100 % | 40,8 | +56,2 [39,4; 73,7] | −7,1 [−15,5; 3,9] | cumple |
| | **G (tanda 5)** | 203 | 48 | 100 % | 40,8 | +56,2 [39,4; 73,7] | −7,1 [−14,5; 2,1] | **cumple** |
| | · alertar todo | 380 | 48 | 100 % | 87,4 | +56,2 | +39,5 [33,4; 47,6] | no cumple |

(· marca un control negativo. Tabla completa en `experimentos/tanda_05/compuerta_salida.txt`.)

**Conteo por candidato en T+1, cortes con veredicto `cumple`:**

| Candidato | v1 | v2 |
| --- | --- | --- |
| G (tanda 5) | 0 de 3 | **3 de 3** |
| vigente (tanda 4) | 0 de 3 | 2 de 3 |
| B degradado | 0 de 3 | **0 de 3** |
| · persistencia | 0 de 3 | **0 de 3** |
| · aleatorio | 0 de 3 | **0 de 3** |
| · alertar todo | 0 de 3 | **0 de 3** |
| · canal inflado | 0 de 3 | **0 de 3** |
| canal endémico | 3 de 3 | 0 de 3 (es la línea base) |

v2 pasa al modelo bueno, rechaza al modelo deliberadamente degradado, y rechaza
los cuatro controles negativos. Eso es una compuerta que discrimina.

**En T+2, v2 no aprueba a nadie**, y el veredicto de tres valores dice por qué:
G obtiene `precisión insuficiente` en dos de los tres cortes, no `no cumple`. Su
estimación puntual cumple los criterios y el intervalo es demasiado ancho con 37
a 48 inicios sobre 4 meses objetivo. El problema a dos meses es de tamaño de
muestra, no de desempeño, y eso en v1 era indistinguible.

---

## 4. Por qué los tres cambios van juntos y no por separado

Esta es la sección que hay que leer para juzgar si la propuesta es honesta.
Cada cambio se aplicó **aislado**, con los mismos controles negativos.
Veredictos `cumple` en T+1, sobre 3 cortes:

| Candidato | v1 | solo base canal | solo denom. fijo | solo verdad inicio | v2 (los tres) |
| --- | --- | --- | --- | --- | --- |
| G (tanda 5) | 0 | 0 | 2 | 3 | 3 |
| vigente (tanda 4) | 0 | 0 | 0 | 3 | 2 |
| B degradado | 0 | 0 | 1 | 3 | 0 |
| · aleatorio | 0 | 0 | **1** | **2** | 0 |
| · alertar todo | 0 | 0 | 0 | **3** | 0 |
| · canal inflado | 0 | 0 | 0 | **3** | 0 |
| canal endémico | 3 | 0 | 3 | 3 | 0 |

- **Solo cambiar la verdad a inicio produce una compuerta inservible.** Alertar
  sobre todo pasa 3 de 3 y el canal inflado con alertas al azar pasa 3 de 3.
  Es el cambio que más favorecería a nuestros candidatos y **los controles
  negativos lo descartan**. Aislado no es admisible.
- **Solo cambiar el denominador también filtra**: el ranking aleatorio pasa 1 de
  3 y el modelo degradado 1 de 3.
- **Solo cambiar la línea base vuelve la compuerta imposible**: no pasa nadie,
  porque con la verdad medida sobre exceso cualquier detector de inicios sigue
  cargando con la penalización de D3.

Los tres juntos funcionan porque cada uno tapa el agujero que los otros
abrirían: una línea base que sí detecta el evento hace que la barra de ganancia
sea real; la verdad igualada al objetivo evita que alertar sobre excesos ya
instalados cuente como acierto; y el denominador fijo evita que la carga se
manipule con el volumen de alertas.

---

## 5. Defectos que v2 deja abiertos, a propósito

Se declaran en vez de resolverse, porque resolverlos exigiría elegir números
después de haber visto los resultados.

**D4 · El umbral de 5,0 está heredado, no derivado.** En v1 se aplicaba a puntos
porcentuales de una razón entre alertas; en v2 se aplica a una tasa por 100
municipio-mes. Son cantidades distintas y el número se conservó por disciplina,
no porque esté calibrado para su nuevo uso. **Es la decisión que corresponde a
la autoridad.** Un punto de partida razonable sería derivarlo de la capacidad
real de investigación de las secretarías de salud de Tolima y Meta, que es un
dato que no tenemos.

**D5 · El punto de operación heredado del canal es enorme en algunos cortes.** En
2024-06 el canal alerta sobre 203 de 380 municipio-mes, el 53 %. Con un
presupuesto así, un ranking aleatorio detecta el 58 % de los inicios y obtiene
`precisión insuficiente` en ese corte, o sea que queda a un paso de pasar. Un
sistema que alerta sobre la mitad de los municipios cada mes no es un sistema de
focalización. Lo correcto sería que la política acotara el volumen de alertas en
sí, y ese tope es otra decisión de autoridad.

**D6 · v2 no puede evaluar al canal.** Al ser la línea base, su ganancia es cero
por construcción. v2 responde "¿este candidato es mejor que el canal?" y no
"¿el canal es suficientemente bueno?". Para lo segundo hace falta otro
instrumento.

---

## 6. Qué se pide decidir

1. Si el diagnóstico de los defectos D1, D2 y D3 se acepta. Son inconsistencias
   internas de v1, verificables en los artefactos registrados.
2. Si los tres cambios se adoptan **como conjunto**. Por separado no son
   admisibles y la sección 4 lo muestra con controles.
3. Si el umbral de carga de 5,0 se recalibra para su nueva unidad, y con qué
   criterio (defecto D4).
4. Si la política debe acotar el volumen de alertas (defecto D5).
5. Qué cohorte se usa para una primera aplicación **confirmatoria**, dado que la
   presente es exploratoria por construcción.

Mientras eso no se decida, v1 sigue siendo la política vigente, el `G5` sigue en
`NOT_APPROVED`, el champion sigue en `not_selected` y el tablero desplegado
sigue publicando resultados de evaluación y no alertas autorizadas.
