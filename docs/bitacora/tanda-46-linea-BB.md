# Tanda 46, línea BB — Los inicios que nadie anticipa

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **cerrada** el 10 de noviembre de 2026. Se corre sobre la base común del
> retroanálisis: `canonical.mode=approved`, calendario y departamentos de
> `parameters_retroanalisis.yml` sin tocar, `conjunto.csv` reportado.

## Hipótesis

Una parte de los inicios no la anticipa ni el canal ni el modelo. Si son sobre todo
inicios que arrancan sin casos en el mes de origen, el límite es de información
(no hay señal que leer), no de método, y el informe debe decirlo.

## Qué se corre

Ningún modelo nuevo. Al 10 % de la sección 0, con la logística con clima: los
inicios detectados por ambos, solo por el canal, solo por el modelo y por ninguno,
y para cada grupo la proporción con cero casos en el mes de origen y la mediana de
casos / P75.

## Qué no decide

Es una lectura.

## Resultado: la mitad de los inicios no los anticipa nadie, y la mitad de esos arranca sin casos

Logística con clima al 10 % de la sección 0:

| Horizonte | Grupo | Inicios | % del total | Con cero casos en el origen | Mediana de casos / P75 |
| --- | --- | --- | --- | --- | --- |
| T+1 | ambos | 236 | 37 % | 0 % | 1.00 |
| T+1 | solo canal | 43 | 7 % | 0 % | 0.78 |
| T+1 | solo modelo | 63 | 10 % | 46 % | 0.33 |
| T+1 | ninguno | 299 | 47 % | 52 % | 0.00 |
| T+2 | ambos | 110 | 24 % | 0 % | 1.00 |
| T+2 | solo canal | 42 | 9 % | 0 % | 0.75 |
| T+2 | solo modelo | 75 | 16 % | 60 % | 0.00 |
| T+2 | ninguno | 232 | 51 % | 47 % | 0.17 |

- **El 47 % de los inicios de T+1 y el 51 % de los de T+2 no los anticipa ninguno
  de los dos métodos**, y en cerca de la mitad de esos el municipio tenía **cero
  casos** en el mes de origen. Sin un solo caso que leer, ni el canal ni un modelo
  basado en casos tienen señal: es un límite de información, no de método.
- El canal solo detecta inicios donde ya hay casos cerca del umbral (mediana
  casos/P75 de 0,75 a 1,00, nunca desde cero).
- **Lo que el modelo detecta y el canal no son, en buena parte, inicios desde cero
  casos** (46 % en T+1 y 60 % en T+2): el modelo usa el resto de la información
  (umbral bajo, municipio poco endémico, estación, clima) para alertar donde el
  canal no puede.

Para el informe: el techo de cualquier sistema basado en casos notificados está
cerca de la mitad de los inicios; para pasar de ahí haría falta información que no
sea el conteo de casos.
