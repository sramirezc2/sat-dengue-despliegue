# Tanda 43, línea AY — Transferir el modelo de un departamento al otro

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **cerrada** el 11 de noviembre de 2026. Se corre sobre la base común del
> retroanálisis: `canonical.mode=approved`, calendario y departamentos de
> `parameters_retroanalisis.yml` sin tocar, `conjunto.csv` reportado.

## Hipótesis

Para llevar el sistema a otros departamentos hay que saber si un modelo entrenado
en un lugar sirve en otro. Si un modelo entrenado solo con Meta predice bien
Tolima, y al revés, la relación entre casos, umbral e inicio es general; si no, el
modelo hay que entrenarlo donde se va a usar.

## Qué se corre

La logística sin clima y con clima, con `entrenar_departamentos`: entrenadas solo
con Meta y solo con Tolima, y evaluadas en los dos (el departamento que no entrenó
se predice sin haber visto sus etiquetas). Las filas evaluadas son las mismas de
siempre.

Se reporta, por departamento evaluado, al presupuesto del canal condicionado:

- el modelo **transferido** (entrenado solo con el otro departamento);
- el modelo **propio** (entrenado solo con el mismo departamento);
- el modelo **conjunto** (los dos departamentos), que es la referencia;
- el canal.

Requiere la opción `entrenar_departamentos`, que va al PR #6.

## Qué decide

La transferencia **funciona** si el modelo transferido queda a menos de 5 puntos
del propio en el departamento evaluado. Si queda por debajo del canal, no
transfiere.

## Resultado: sin clima transfiere; con clima, lo aprendido en Meta no sirve en Tolima

Inicios detectados al presupuesto del canal condicionado, por departamento
evaluado. «Propio» es el modelo entrenado solo con ese departamento, «transferido»
el entrenado solo con el otro y «conjunto» el de siempre, con los dos. En los tres
casos el presupuesto mensual se reparte entre los dos departamentos con el mismo
puntaje, así que un modelo que puntúa más bajo a un departamento le deja menos
alertas.

| Clima | Horizonte | Departamento evaluado | Canal | Propio | Transferido | Conjunto | Transferido − propio |
| --- | --- | --- | --- | --- | --- | --- | --- |
| sin | T+1 | Meta | 152 | 154 | 155 | 154 | +1 (+0.4 pp) |
| sin | T+1 | Tolima | 171 | 190 | 188 | 193 | -2 (-0.5 pp) |
| sin | T+2 | Meta | 92 | 96 | 99 | 102 | +3 (+1.6 pp) |
| sin | T+2 | Tolima | 115 | 142 | 147 | 146 | +5 (+1.8 pp) |
| con | T+1 | Meta | 152 | 172 | 168 | 168 | -4 (-1.5 pp) |
| con | T+1 | Tolima | 171 | 183 | 150 | 191 | -33 (-8.8 pp) |
| con | T+2 | Meta | 92 | 113 | 104 | 106 | -9 (-4.9 pp) |
| con | T+2 | Tolima | 115 | 140 | 132 | 147 | -8 (-2.9 pp) |

- **Sin clima, el modelo transfiere** en los dos sentidos y en los dos horizontes:
  el transferido queda a menos de 2 puntos del propio (entre −2 y +5 inicios).
  La relación entre casos, umbral e inicio es la misma en Meta y en Tolima.
- **Con clima, no**: el modelo entrenado solo con Meta, aplicado en Tolima, **pierde
  33 inicios en T+1 frente al propio** (−8,8 pp; 150 frente a 183, por debajo del
  canal) y 8 en T+2. Al revés, el entrenado en Tolima funciona en Meta (−4 en T+1,
  −9 en T+2, dentro de 5 puntos).
- Junto con las tandas 18, 25 y 26: el efecto del clima es propio de cada región. Lo
  que el modelo aprende del clima en Meta lo lleva a ordenar mal a Tolima.

Para llevar el sistema a otros departamentos: **la versión sin clima se puede
transferir; la versión con clima hay que entrenarla con datos de la región donde se
va a usar.**
