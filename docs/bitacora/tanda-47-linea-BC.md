# Tanda 47, línea BC — En qué meses del año gana el modelo

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **cerrada** el 10 de noviembre de 2026. Se corre sobre la base común del
> retroanálisis: `canonical.mode=approved`, calendario y departamentos de
> `parameters_retroanalisis.yml` sin tocar, `conjunto.csv` reportado.

## Hipótesis

El canal endémico se construye mes a mes con los cinco años anteriores, así que su
umbral ya trae la estación. Si el modelo gana sobre todo en ciertos meses (por
ejemplo, al inicio de la temporada de lluvias), eso orienta cuándo usarlo.

## Qué se corre

Ningún modelo nuevo. Al 10 % de la sección 0, logística con clima, T+1 y T+2: los
inicios detectados por el canal y por el modelo según el mes objetivo, agrupado por
trimestre para tener celdas de 30 inicios o más.

## Qué no decide

Es una lectura.

## Resultado

Logística con clima al 10 % de la sección 0, por trimestre del mes objetivo:

| Horizonte | Trimestre del mes objetivo | Inicios | Canal | Modelo | Diferencia |
| --- | --- | --- | --- | --- | --- |
| T+1 | ene-mar | 165 | 72 | 72 | +0 |
| T+1 | abr-jun | 155 | 62 | 67 | +5 |
| T+1 | jul-sep | 159 | 80 | 86 | +6 |
| T+1 | oct-dic | 162 | 65 | 74 | +9 |
| T+2 | ene-mar | 118 | 37 | 49 | +12 |
| T+2 | abr-jun | 127 | 33 | 43 | +10 |
| T+2 | jul-sep | 113 | 53 | 56 | +3 |
| T+2 | oct-dic | 101 | 29 | 37 | +8 |

- **T+1:** el modelo empata en enero-marzo y gana algo el resto del año, más en
  octubre-diciembre (+9).
- **T+2:** gana en todos los trimestres, más en el primer semestre (+12 en
  enero-marzo y +10 en abril-junio) que en julio-septiembre (+3), que es cuando el
  canal detecta más.
- Ningún trimestre concentra la ventaja: no hay una época del año en la que el
  modelo sobre y otra en la que sea indispensable.

Nota de método: el primer cálculo de esta tabla desplazó el mes objetivo en uno
(la codificación del origen es año × 12 + mes, con el mes de 1 a 12). Se corrigió
antes de publicar; la tabla de arriba es la correcta.
