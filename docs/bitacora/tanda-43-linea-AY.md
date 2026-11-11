# Tanda 43, línea AY — Transferir el modelo de un departamento al otro

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **preinscrita, sin correr.** Se corre sobre la base común del
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
