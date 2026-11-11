# Tanda 37, línea AS — Anticipación con los dos horizontes juntos

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **cerrada** el 10 de noviembre de 2026. Se corre sobre la base común del
> retroanálisis: `canonical.mode=approved`, calendario y departamentos de
> `parameters_retroanalisis.yml` sin tocar, `conjunto.csv` reportado.

## Hipótesis

Operativamente, a la secretaría le sirve saber de un brote con uno **o** dos
meses de anticipación. Si los dos horizontes se complementan, el modelo debería
cubrir más inicios con las dos listas juntas que el canal con las suyas.

## Qué se corre

Ningún modelo nuevo. Al 10 % de la sección 0 en cada horizonte, para la logística
sin clima y con clima: sobre los inicios de T+1 (mismo municipio y mes objetivo),
cuántos quedan avisados por la alerta a un mes, por la alerta a dos meses (emitida
un mes antes), por cualquiera de las dos y por ninguna; lo mismo para el canal
condicionado.

## Qué no decide

Es una lectura para el informe; no cambia veredictos.

## Resultado

Sobre los 641 inicios de T+1, al 10 % de la sección 0 en cada horizonte:

| Receta | Método | A un mes | A dos meses | Cualquiera de los dos | Solo a dos meses |
| --- | --- | --- | --- | --- | --- |
| logistica_sin_clima | canal | 279 | 152 | 327 | 48 |
| logistica_sin_clima | modelo | 286 | 179 | 337 | 51 |
| log_conclima | canal | 279 | 152 | 327 | 48 |
| log_conclima | modelo | 299 | 185 | 353 | 54 |

- Con las dos listas juntas, el canal avisa **327** de los 641 inicios (51 %); la
  logística sin clima **337** (+10) y la logística con clima **353 (+26, 4,1
  puntos)**.
- Los dos horizontes se complementan poco: solo 48 a 54 inicios quedan avisados
  únicamente a dos meses.
- La ventaja del modelo con las dos listas juntas (+26 con clima) es la suma de
  su ventaja en T+1 (+20) y la que T+2 agrega sobre lo que T+1 ya avisó.

Para el informe: con 8 alertas por mes en cada horizonte, la logística con clima
avisa con uno o dos meses de anticipación algo más de la mitad de los inicios
(55 %), frente al 51 % del canal condicionado.
