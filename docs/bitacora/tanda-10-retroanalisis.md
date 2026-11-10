### Tanda 10 — Retroanálisis con datos reales y regresión logística

**Cómo se evaluó todo.** Se usaron los datos crudos reales (Hugging Face, verificados por sha256), solo Tolima y Meta, de 2019 a 2024. 2025 no se tocó. El modelo se reentrena cada mes con la información disponible hasta ese momento. Se compara contra el canal endémico emitiendo el mismo número de alertas cada mes, y se cuentan los inicios de brote detectados. Hay 541 inicios a un mes (T+1) y 380 a dos meses (T+2). La línea base principal es un canal mejorado: su umbral se ajusta con el año anterior y solo alerta donde no hay exceso. Ese canal detecta 280 inicios en T+1 y 179 en T+2.

**Release.** Los experimentos 1 a 21 usaron el release histórico 2011–2024 (`approved-raw.json`) y no se repitieron; el 22 y el 23 usan el release nuevo `satd-raw-173d5856` (2007-2024). Todas las cifras del contrato en esta bitácora son exploratorias: la cifra oficial saldrá de EXP003 ejecutado con la evaluación científica del PR #3 de Mauro.

#### Experimentos

1. **Correr el pipeline con datos reales.** Se construyó el panel desde los crudos y se corrió el retroanálisis. Salieron dos ajustes al pipeline: el panel es nacional y hay que filtrar Tolima y Meta, y la demora de un mes en las etiquetas cortaba diciembre de 2024. La receta de ejemplo `EXP001` es de prueba (4 rondas) y no sirve como referencia.
2. **XGBoost con una receta razonable** (300 rondas, profundidad 4). Detecta 290 inicios en T+1 y 199 en T+2, prácticamente lo mismo que el canal. Con pocas alertas pierde contra el canal tradicional (P75).
3. **Otras recetas de XGBoost** (más chicas y más grandes). La más chica rinde igual y la más grande peor. No hay ganancia por ahí.
4. **Quitar el clima.** En T+1 no cambia nada y en T+2 mejora (de 199 a 206-211). Se confirmó con otras recetas, semillas y formas de reentrenar.
5. **Quitar otros bloques de variables.** El bloque del canal es indispensable: sin él el modelo cae a 195 inicios en T+1. El mes, el rezago de 12 meses y los conteos de dengue grave o total no aportan.
6. **Regresión logística en vez de XGBoost.** Detecta 306 inicios en T+1 y 215 en T+2, más que el canal en ambos horizontes. Es estable entre años y con distintos ajustes. Es el mejor resultado de la tanda.
7. **Logística mínima de 5 variables:** distancia de los casos al umbral del mes objetivo, distancia al umbral actual, cambio del umbral entre meses, tendencia de casos y si hubo casos. Rinde casi igual que la completa (301 y 216) y es fácil de explicar.
8. **Elegir el modelo con 2019-2022 y probarlo en 2023-2024.** La logística mantiene su ventaja en los años nuevos. La de XGBoost en T+2 casi desaparece: era ruido de selección.
9. **Umbral operativo fijado con el año anterior,** el criterio 3 de la propuesta. En T+1 la logística detecta 280 inicios contra 233 del canal y cumple el criterio en 4 de 5 años. Si cada mes se emiten tantas alertas como el canal, cumple los 6 años en ambos horizontes.
10. **Qué inicios detecta.** Gana en brotes pequeños y en municipios poco endémicos, que el canal no ve porque arrancan con pocos casos. En brotes grandes el canal es igual o un poco mejor.
11. **Brotes sostenidos frente a picos de un mes.** En T+1 casi toda la ventaja de la logística viene de picos de un solo mes; en los brotes que duran 2 meses o más empata con el canal. En T+2 sí gana algo también en los sostenidos (104 contra 93).
12. **Dar más peso a los brotes grandes al entrenar.** La logística empata con el canal en brotes grandes y mantiene el total (301 contra 280).
13. **Entrenar solo para brotes sostenidos.** Empeora (148 contra 159 en T+1). El canal ya está en el techo para esos brotes.
14. **Probabilidades (calibración).** En T+1 se pueden leer como probabilidades reales. En T+2 subestiman el riesgo, porque la frecuencia de inicios cambia mucho entre años (de 7 % a 42 %), y recalibrar con años anteriores no lo arregla.
15. **Dos horizontes juntos.** Si un inicio cuenta cuando se alertó a 1 o a 2 meses, la logística anticipa 355 de 541 contra 329 del canal.
16. **La logística dentro del pipeline.** Se agregó como familia de modelo (`logistic_onset`) y es la receta por defecto del retroanálisis. Reproduce los resultados: 301 y 217.
17. **La logística en la fábrica de experimentos.** Se amplió `experiment_run` para aceptar la familia `logistic_onset` sin afectar a XGBoost; EXP001 y EXP002 validan igual.
18. **El contrato científico de Mauro en la fábrica (versión exploratoria, retirada).** Se implementó en `experiment_run` lo que el §16 del contrato marcaba como faltante:
    - el canal condicionado como comparador primario, con su fracción del P75 elegida en el rol de desarrollo;
    - el presupuesto de alertas fijado antes de evaluar (cada mes, las mismas alertas que el canal);
    - la sensibilidad de inicio y la carga de falsas alertas por 100 municipio-mes;
    - el intervalo de 2.000 réplicas por bloques de mes objetivo;
    - los controles negativos (ranking aleatorio, alertar todo y canal inflado);
    - el veredicto por horizonte.

    Usa los cinco roles fijos (evaluación 2024) y filtra Tolima y Meta. EXP003, la logística sin clima según el contrato, quedó registrado como PROPOSED; lo debe aprobar otra persona del equipo.

    Después, Mauro implementó la evaluación científica oficial en el PR #3 (`evaluation/scientific/`). Se adoptó esa como la oficial: el módulo propio salió de la fábrica y quedó solo como herramienta exploratoria en `tools/contrato_exploratorio/`, y el registro de EXP003 se revirtió para volver a registrarlo en el formato del PR #3. El PR #2 quedó apilado sobre el PR #3.
19. **Corrida exploratoria con el contrato** (datos reales, motor de la fábrica fuera del registro). En los dos casos los controles negativos no cumplen, así que la evaluación es válida.

| Candidato | T+1: canal / modelo de 99 inicios | Δ sensibilidad T+1 | Veredicto T+1 | T+2: canal / modelo de 66 | Δ sensibilidad T+2 | Veredicto T+2 |
|---|---|---|---|---|---|---|
| Logística sin clima | 74 / 81 | +7,1 pp (IC 2,4 a 10,9) | NO_CUMPLE_POR_EFECTO | 51 / 59 | +12,1 pp (IC 4,6 a 19,4) | PRECISION_INSUFICIENTE |
| XGBoost | 74 / 83 | +9,1 pp (IC 3,0 a 14,9) | NO_CUMPLE_POR_EFECTO | 51 / 59 | +12,1 pp (IC −1,8 a 21,8) | PRECISION_INSUFICIENTE |

    En los dos horizontes los modelos detectan más inicios que el canal y con menos carga de falsas alertas (entre −1,7 y −2,2 por 100 municipio-mes). Pero en T+1 no llegan a los 10 puntos que pide el contrato, y en T+2 la cota inferior del intervalo queda por debajo de 10. Hay heterogeneidad: en T+1 la logística pierde en Meta (36 vs 40) y gana en Tolima (45 vs 34). La logística es determinista: dos ejecuciones aisladas dieron la misma huella del modelo (T+1 583a965f…, T+2 752dff14…) y exactamente la misma evaluación del contrato, como pide el §13.

20. **Exploración amplia bajo el contrato.** Con el motor de la fábrica y los cinco roles de Mauro se corrieron 65 configuraciones con datos reales: 13 recetas, cada una evaluada en cuatro cohortes (2024, 2023, 2022 y 2021, desplazando los roles un año a la vez). 2020 no fue factible porque el canal de 5 años deja muy pocos meses de entrenamiento. En las cohortes antiguas el entrenamiento empieza en 2016-08, el primer mes con variables completas. Se combinaron las cuatro cohortes con el mismo bootstrap por bloques de mes.

| Receta (cuatro cohortes, 2021-2024) | T+1: Δ sensibilidad (IC 95 %) | T+2: Δ sensibilidad (IC 95 %) |
|---|---|---|
| Logística sin clima | +3,3 pp (−0,9 a 7,2) | +9,4 pp (4,5 a 14,3) |
| Logística sin clima, entrenada con todo el país | +0,3 pp (−3,5 a 4,3) | +9,8 pp (5,7 a 14,2) |
| Logística con clima | +4,2 pp (−0,3 a 8,5) | +9,0 pp (4,4 a 13,7) |
| Logística mínima (6 variables) | +3,6 pp (−0,5 a 7,6) | +8,2 pp (2,8 a 13,8) |
| Logística mínima con conteos totales | +4,2 pp (0,0 a 8,2) | +7,8 pp (2,3 a 13,4) |
| Logística, C = 0,1 / C = 10 | +1,5 / +3,9 pp | +7,8 / +9,0 pp |
| XGBoost con clima (300 rondas, profundidad 4) | +0,3 pp (−4,0 a 4,5) | +7,8 pp (2,9 a 12,4) |
| XGBoost sin clima (300/4, 150/3, 100/2) | −1,5 a +1,2 pp | +5,7 a +8,2 pp |

    Ninguna cumple el contrato. En T+1 la ganancia está entre −1,5 y +4,2 puntos, lejos de los 10, y no cambiaría aunque la meta bajara a 5. En T+2 todas ganan entre 6 y 10 puntos, siempre con menos carga de falsas alertas, pero ninguna llega a 10 en la estimación puntual. Con una meta de 5 puntos, la logística entrenada con todo el país sí cumpliría en T+2.

21. **Lo que muestran esas corridas:**
    - **Logística frente a XGBoost:** la logística detecta 3,0 puntos más en T+1 (IC −1,3 a 7,3), una diferencia que no es clara.
    - **Cinco semillas de XGBoost con muestreo aleatorio (2024):** T+1 entre +6 y +9 puntos y T+2 entre +7,6 y +13,6; la conclusión no depende de la semilla.
    - **Entrenar con todo el país** (logística completa, logística mínima y XGBoost chico): en T+1 no ayuda, con ganancias entre 0 y +2 puntos, y la logística completa pierde brotes sostenidos (99 frente a 107). En T+2 las dos logísticas nacionales detectan más brotes sostenidos que el canal (79 y 78 frente a 69, cuando la versión local empataba); la ganancia total es de +7,8 a +9,8 puntos. XGBoost nacional no mejora los sostenidos.
    - **Heterogeneidad:** en T+1 la logística gana en Tolima (100 frente a 88) y empata en Meta (86 frente a 87); XGBoost pierde en Meta (76 frente a 87). Por año, la ventaja desaparece en 2021-2022, que fueron de baja transmisión.
    - **Brotes sostenidos frente a picos de un mes:** en los sostenidos de T+1 todos empatan con el canal (109 frente a 107). La ganancia viene de los picos de un mes (77 frente a 68).
    - **Presupuesto de alertas:** emitir 1,2 veces las alertas del canal parecía cumplir el contrato en T+1 (+10,2 puntos con +2,4 de carga), pero ese valor se eligió mirando los resultados. Al elegir el multiplicador con 2021-2022 y evaluarlo congelado en 2023-2024, el elegido (1,5) dispara la carga (+14 a +21 por 100 municipio-mes) y no cumple. El presupuesto óptimo cambia con el nivel de transmisión del año.
    - **Un modelo que alimenta al otro (idea de Mauro):** en T+2 se combinó el puntaje del modelo de T+2 con el del modelo de T+1 emitido en el mismo mes de origen, así que no hay fuga. Empeora: el puntaje de T+1 solo detecta 78 inicios frente a 106 del canal, y al combinarlo la ganancia baja de +9,4 a entre +0,8 y +2 puntos. El modelo de T+2 ya captura lo útil.
    - **Ensamble de logística y XGBoost:** llega a 10 puntos solo en T+1 de 2024; en las demás cohortes no mejora a sus componentes.
    - **Observación sobre el contrato:** en T+2 de 2022 la fracción del canal elegida en desarrollo fue 1,5, el tope de la grilla, porque 2021 tuvo muy poca transmisión. El canal emitió apenas 27 alertas y detectó 4 de 61 inicios, y como el modelo usa el mismo presupuesto, quedó igual de limitado. Conviene que el equipo revise la grilla o la regla del presupuesto para años bajos.

22. **Ventana acordada 2018-2024 con el release nuevo.** Con el release `satd-raw-173d5856` (panel 2007-2024, idéntico al certificado por Mauro, con el clima de enero de 2020 completo) se repitieron las cuatro combinaciones principales en siete cohortes, de 2018 a 2024. Las variables están completas desde 2012-01, así que el entrenamiento empieza en 2012-03 y 2018 tiene unos 3 años de entrenamiento.

| Combinación (siete cohortes, 2018-2024; 593 y 431 inicios) | T+1: Δ sensibilidad (IC 95 %) | T+2: Δ sensibilidad (IC 95 %) |
|---|---|---|
| Logística con clima | +3.4 pp (0.5 a 6.2) | +8.1 pp (4.2 a 11.8) |
| Logística sin clima | +2.7 pp (−0.2 a 5.9) | +7.7 pp (3.7 a 11.8) |
| Logística mínima | +1.5 pp (−1.6 a 4.7) | +6.7 pp (2.3 a 11.3) |
| XGBoost con clima | −0.5 pp (−3.6 a 2.6) | +1.9 pp (−3.2 a 6.6) |

    - Ninguna combinación cumple el contrato.
    - Con más años, la logística le gana a XGBoost de forma clara: +3.2 pp en T+1 (IC 0.3 a 6.0) y +5.8 pp en T+2 (IC 1.3 a 10.3). XGBoost rinde peor en 2018-2021.
    - Con el clima completo, la logística con clima queda apenas por encima de la versión sin clima, sin diferencia clara.
    - En T+1 los modelos pierden brotes sostenidos frente al canal (178 frente a 189); la ganancia viene de los picos de un mes (156 frente a 129).
    - El presupuesto elegido en desarrollo vuelve a disparar la carga en 2023-2024: con el multiplicador 1.5 elegido en 2021-2022, la logística sin clima detecta 168 frente a 129 inicios en T+1, pero con 14.39 falsas alertas más por 100 municipio-mes.

23. **Encadenar los modelos (idea de Mauro).** En T+2 se combinó el puntaje del modelo T+2 con el del modelo T+1 emitido en el mismo mes de origen, sin fuga, en las siete cohortes 2018-2024.

| Combinación en T+2 (431 inicios, canal 198) | Logística con clima | Logística mínima |
|---|---|---|
| Solo T+2 | 233, +8.1 pp (4.2 a 11.8) | 227, +6.7 pp (2.3 a 11.3) |
| Solo puntaje T+1 | 138, −13.9 pp | 126, −16.7 pp |
| Promedio de rangos | 205, +1.6 pp (−2.4 a 5.4) | 195, −0.7 pp (−5.5 a 4.0) |
| Máximo de rangos | 198, 0.0 pp | 190, −1.9 pp |

    Encadenar empeora: el modelo T+2 solo es la mejor opción y el puntaje T+1 diluye su señal.

#### Lo que se probó y no funcionó

- Regla que combina el canal y el modelo.
- Splines (relaciones no lineales).
- Interacciones entre variables.
- Pesos balanceados.
- Un modelo por departamento.
- Señal del departamento.
- Señal de los 5 municipios vecinos, con coordenadas oficiales de DIVIPOLA.
- Señal nacional.
- Ventanas de entrenamiento de 3 y 5 años.
- Más peso a los años recientes.
- Modelo de conteo (Poisson).

Ninguna mejora el resultado de forma relevante.

#### Conclusión

Con la evaluación exploratoria del contrato, en la ventana acordada 2018-2024 (siete cohortes), la respuesta es la siguiente. La cifra oficial saldrá de EXP003 con el módulo del PR #3.

- **T+1, el horizonte primario: no, con la evidencia evaluada.** Ningún modelo supera de forma clara a un canal condicionado bien ajustado: las ganancias están entre −0.5 y +3.4 puntos, lejos de los 10 exigidos, y en los brotes sostenidos todos empatan con el canal.
- **T+2: mejora consistente pero por debajo de la meta.** Las logísticas le ganan al canal entre 6.7 y 8.1 puntos y con menos falsas alertas, pero ninguna llega a 10 puntos; XGBoost queda en +1.9. Encadenar con el modelo T+1 no ayuda.

Lo que se aprendió:

- Los modelos simples (una logística con 6 variables) rinden igual que XGBoost.
- El clima no aporta en T+1.
- La ventaja se concentra en brotes pequeños o de un solo mes, en Tolima y en años de alta transmisión.
- Ajustar el presupuesto de alertas no generaliza entre años.

Para cerrar la pregunta hace falta que el equipo:

1. apruebe el contrato, revisando si 10 puntos es una meta alcanzable con estos datos y cómo tratar los años de baja transmisión;
2. apruebe y ejecute EXP003 con el registro;
3. defina una cohorte confirmatoria madura.
