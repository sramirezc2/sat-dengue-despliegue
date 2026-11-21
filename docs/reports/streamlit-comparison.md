# Comparación descriptiva de prioridades Streamlit

Base: `ed5694ab9b4a179f396852335f9d9e8b840fbe7e`, árbol limpio y rama
`feature/streamlit-configurable-prioritization`, coincidente con el HEAD remoto
del [PR #18](https://github.com/sramirezc2/sat-dengue-despliegue/pull/18).
La base contiene `origin/main` y ocho commits adicionales. El SHA final corresponde
al commit que incorpora este informe; la descripción del PR registra su CI terminal.

## Aplicabilidad y fidelidad

Los doce contextos locales verificados contienen `p75_h5_t2` para los 76
municipios. No fue necesario descargar, reconstruir contexto ni modificar el
modelo. Se implementa la regla documentada de T+2: dengue **210** en T
estrictamente mayor que `0.95 * p75_h5_t2` del mismo origen. La constante
`CHANNEL_FRACTION` tiene una sola definición en el código; una prueba la reconcilia
con `log_conclima / horizonte 2 / presupuesto 0.1` de la fuente científica
[reserva.csv](../evidence/reserva-2023-2024-t2/reserva.csv), SHA-256
`35d2c8d0c3082374272fa17c6ff32ce727427f8a5f10c8c2661547c9eff2172f`.

La cohorte es la del ranking existente. El canal ordena márgenes positivos
descendentes y desempata por DIVIPOLA ascendente; aplica el máximo de cupos sin
rellenar. El modelo conserva sus posiciones y selección. La función pura copia
sus entradas, no ejecuta scoring y devuelve solo la unión y las cinco columnas
solicitadas. El índice DIVIPOLA permite identificar y desempatar municipios.

La validación exige cobertura municipal completa y única. Dentro de la cohorte
elegible, valores faltantes, negativos o no finitos generan un error aislado;
no se imputan ni excluyen filas adicionales. Los municipios que el modelo ya
excluyó por predictores incompletos permanecen fuera de ambas listas.

Esta revisión comprueba fidelidad de una regla congelada, sin aprobar una receta
nueva ni aceptar conclusiones científicas. La capacidad simulada es un límite;
no reproduce la equiparación histórica mensual del número de alertas. Las listas
actuales y las métricas históricas se muestran en acordeones distintos. No se
consultan desenlaces de T+2 ni se calculan aciertos, sensibilidad o precisión de
la carga. Los fixtures artificiales acreditan software, no evidencia científica.

## Archivos y comportamiento

- `demo/inferencia.py`: constante congelada y comparación pura de listas.
- `demo/app.py`: acordeón nativo cerrado, tres tarjetas, cupos efectivos,
  tabla y advertencias exactas; errores confinados.
- `demo/tests/test_comparacion_prioridades.py`: 14 casos focalizados.
- `demo/tests/test_app.py`: reconciliación de tarjetas y listas, cambios de
  capacidad sin scoring y errores aislados; adaptación de las expectativas
  existentes al nuevo acordeón.
- [Guía de operación](../operations/streamlit-demo.md), este informe y capturas.

No se agregan dependencias, CSS, componentes, servicios ni gráficas. Mapas,
tabla principal, descargas, aviso de 2025 y respaldo con dos gráficas/cuatro
métricas históricas conservan su comportamiento.

## Verificación

Durante la implementación: 14 pruebas puras y después **22 passed, 8 deselected**
con `-k "comparison or channel or capacity or expander"`. Ruff solo sobre los
cuatro archivos Python modificados: PASS. No se ejecutó la suite completa en
cada ajuste. Una advertencia inicial de pandas sobre `verify_integrity` se
resolvió mediante comprobación explícita de unicidad; la ejecución focalizada
final no emitió advertencias.

Gates finales, ejecutados una sola vez al terminar la implementación:

- `demo/.venv/bin/python -m pytest demo/tests -q`: **116 passed en 29.87 s**,
  sin advertencias.
- Ruff explícito de los módulos y pruebas de demo y `streamlit_app.py`: **PASS**.
- Preservación normal y con `python -O`: **PASSED** en ambos casos; 49 archivos
  originales, 127 extendidos, 22 JSON históricos e identidad N=3 conservados.
- `git diff --check`: **PASS**, incluyendo archivos nuevos mediante intent-to-add.
- Enlaces documentales, tamaños de archivos nuevos y búsqueda de patrones de
  secretos limitada a texto agregado: **PASS**, sin mostrar posibles valores.

Las pruebas cubren desigualdad estricta, P75 cero, separación 210/220, cohorte,
5/10/100 %, déficit de candidatos, empates, orden por margen, tres categorías,
unión, posiciones, ausencia de puntuaciones y reconciliación con la evidencia.
La integración prohíbe un segundo scoring al cambiar capacidades y verifica
errores de P75 sin perder mapas, ranking ni respaldo científico.

Por el alcance exclusivo de demo, no se repiten localmente las suites de pipeline,
API ni dashboard. Los checks remotos del nuevo SHA deben verificarse después del
push autorizado; una CI anterior no valida este cambio. No se realiza merge.

## Preservación

El inventario SHA-256 inicial de los **662 archivos versionados** se conserva
localmente fuera de Git. El cotejo confirma diferencias únicamente en los cuatro
archivos existentes declarados arriba. Las **nueve funciones preexistentes** de
`demo/inferencia.py` conservan su AST, incluido ranking, carga y selección de cupos.
Los comprobadores normal y optimizado pasan. No se modifica evidencia científica, contexto,
modelo, publicaciones, receta, presupuesto histórico de ocho ni `plan.md`.
No se entrena ni se ejecuta la fábrica experimental.

## Recorrido en Chrome

Instancia nueva loopback `127.0.0.1:8522`, con el modelo congelado y contexto
local previamente verificado. Un proceso antiguo retenía el módulo anterior en
memoria; iniciar la instancia nueva permitió probar el código actualizado sin
cambios adicionales. No se configura un destino público.

Ventana de 960 px y viewport de unos 405 px obtenido acoplando DevTools a la
derecha. Se prueba un ancho estrecho, no hardware móvil. Las tarjetas se apilan;
la tabla nativa permite recorrer columnas con teclado y desplazamiento horizontal.
Temas claro y oscuro: tarjetas, texto y categorías legibles. Ambos acordeones
inician cerrados y pueden coexistir abiertos; el respaldo conserva sus dos
gráficas y cuatro métricas.

| Entrada artificial | Capacidad | Cupos | Modelo | Canal | Ambos / Solo modelo / Solo canal |
| --- | ---: | ---: | ---: | ---: | --- |
| Integrada: 24 notificaciones | 5 % | 4 | 4 | 0 | 0 / 4 / 0 |
| Integrada | 10 % | 8 | 8 | 0 | 0 / 8 / 0 |
| Integrada | 100 % | 76 | 74 | 0 | 0 / 74 / 0 |
| Contraste: 8 notificaciones | 5 % | 4 | 4 | 4 | 3 / 1 / 1 |
| Contraste | 10 % | 8 | 8 | 5 | 4 / 4 / 1 |
| Contraste | 100 % | 76 | 76 | 5 | 5 / 71 / 0 |

El contraste contiene cinco notificaciones 210 inventadas y tres 220 en otro
municipio; estas últimas no generan alerta del canal. El archivo permanece
ignorado y no se incorpora a Git. Su SHA-256 es
`234964f9397282da0b173ec468bad68aa909ad56a68c32cef713c378c6f0bb2b`.
Las capturas muestran resultados derivados de estas cargas artificiales;
no incluyen filas privadas, predictores, scores ni márgenes.

- [960 px, acordeones cerrados](streamlit-comparison/960-dark-closed.png).
- [960 px, muestra integrada al 10 %](streamlit-comparison/960-dark-sample-10.png).
- [960 px, contraste oscuro al 10 %](streamlit-comparison/960-dark-contrast-10.png).
- [960 px, contraste claro al 10 %](streamlit-comparison/960-light-contrast-10.png).
- [960 px, cuatro cupos y convivencia científica](streamlit-comparison/960-dark-contrast-5.png).
- [960 px, canal sin rellenar al 100 %](streamlit-comparison/960-dark-contrast-100.png).
- [405 px, tarjetas claras](streamlit-comparison/405-light-contrast-cards.png).
- [405 px, tabla clara](streamlit-comparison/405-light-contrast-table.png).
- [405 px, tarjetas oscuras](streamlit-comparison/405-dark-contrast-cards.png).
- [405 px, categorías y teclado en tabla oscura](streamlit-comparison/405-dark-contrast-table.png).

La autorización remota explícita previa de la sesión permite publicar únicamente
en la rama del PR #18 y actualizar su descripción. El informe no acredita
despliegue externo ni autorización operativa del sistema.
