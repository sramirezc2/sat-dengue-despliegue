# Tanda 42, línea AX — Se pueden leer las probabilidades como riesgo?

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **cerrada** el 10 de noviembre de 2026. Se corre sobre la base común del
> retroanálisis: `canonical.mode=approved`, calendario y departamentos de
> `parameters_retroanalisis.yml` sin tocar, `conjunto.csv` reportado.

## Hipótesis

En la tanda 10, con otro instrumento, la probabilidad de T+1 se podía leer como
riesgo real y la de T+2 subestimaba. Si se repite sobre la base común, el informe
puede presentar el puntaje de T+1 como probabilidad y el de T+2 solo como orden.

## Qué se corre

Ningún modelo nuevo. Para la logística sin clima y con clima, por horizonte, sobre
las filas evaluadas: la frecuencia observada de inicios por decil de probabilidad
predicha, la media predicha en cada decil, la puntuación de Brier y la de una
predicción constante igual a la frecuencia de entrenamiento como referencia.

## Qué no decide

Es descriptiva; la decisión de la sección 0 usa el orden, no la probabilidad.

## Resultado: las probabilidades están bien calibradas en los dos horizontes

- logistica_sin_clima T+1: Brier 0.1089 (constante 0.1324); media predicha 0.159, observada 0.157.
  Por decil (predicha / observada): 1:0.009/0.007 2:0.024/0.022 3:0.042/0.047 4:0.064/0.051 5:0.091/0.096 6:0.138/0.159 7:0.177/0.130 8:0.215/0.194 9:0.297/0.355 10:0.538/0.509
- logistica_sin_clima T+2: Brier 0.0933 (constante 0.1007); media predicha 0.109, observada 0.114.
  Por decil (predicha / observada): 1:0.014/0.017 2:0.028/0.035 3:0.040/0.050 4:0.055/0.067 5:0.074/0.094 6:0.097/0.097 7:0.118/0.111 8:0.137/0.129 9:0.189/0.186 10:0.334/0.351
- log_conclima T+1: Brier 0.1073 (constante 0.1324); media predicha 0.159, observada 0.157.
  Por decil (predicha / observada): 1:0.008/0.002 2:0.022/0.022 3:0.040/0.051 4:0.061/0.047 5:0.092/0.115 6:0.132/0.118 7:0.168/0.137 8:0.213/0.199 9:0.308/0.346 10:0.548/0.533
- log_conclima T+2: Brier 0.0928 (constante 0.1007); media predicha 0.109, observada 0.114.
  Por decil (predicha / observada): 1:0.013/0.015 2:0.027/0.037 3:0.039/0.045 4:0.055/0.054 5:0.073/0.077 6:0.091/0.119 7:0.112/0.092 8:0.142/0.149 9:0.192/0.220 10:0.350/0.328

- En T+1 y en T+2 la probabilidad media predicha coincide con la frecuencia
  observada (0,159 frente a 0,157 en T+1; 0,109 frente a 0,114 en T+2), y decil por
  decil la diferencia es de pocos puntos. En el decil más alto, la logística con
  clima predice 0,55 en T+1 y se observa 0,53; en T+2, 0,35 y 0,33.
- La puntuación de Brier mejora a la de una constante en los dos horizontes.
- **A diferencia de la tanda 10, T+2 ya no subestima**: sobre la base común, con el
  piso de entrenamiento en 2012 y reentrenamiento mensual, la probabilidad de T+2
  también se puede leer como riesgo.

Nota de método: la constante de referencia usa la frecuencia observada en las
filas evaluadas, no la de entrenamiento como decía la preinscripción. Es una
referencia más exigente (conoce la frecuencia real), así que la comparación del
Brier queda del lado conservador.

Para el informe: el puntaje del modelo se puede presentar como probabilidad de
inicio en los dos horizontes, con un municipio en el decil alto teniendo entre un
tercio y la mitad de probabilidad de iniciar brote.
