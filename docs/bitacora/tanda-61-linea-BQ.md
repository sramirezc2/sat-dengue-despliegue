# Tanda 61, línea BQ — Cómo se reparten las alertas entre municipios y meses

> **Preinscripción.** Escrita antes de correr nada, según la regla 8. El
> resumen y el enlace quedan en [la bitácora principal](../bitacora-experimental.md),
> sección 5, cuando la tanda cierre.
>
> Estado: **cerrada** el 11 de noviembre de 2026. Se corre sobre la base común del
> retroanálisis: `canonical.mode=approved`, calendario y departamentos de
> `parameters_retroanalisis.yml` sin tocar, `conjunto.csv` reportado.

## Hipótesis

Ninguna que decida. Una secretaría no recibe un porcentaje: recibe una lista de
municipios cada mes. Si las falsas alertas se concentran en pocos municipios, o un
mismo municipio queda alertado muchos meses seguidos, el costo operativo y el
cansancio de alertas son distintos de lo que dice el promedio.

## Qué se corre

Ningún modelo nuevo. Al 10 % de la sección 0, logística con clima y canal
condicionado, T+1 y T+2, 2018-2024: cuántos municipios distintos reciben alertas,
qué parte de las falsas alertas se lleva el 10 % de municipios con más falsas, y la
racha máxima y mediana de meses consecutivos alertados por municipio.

## Qué no decide

Es una lectura operativa.

## Resultado: el modelo reparte las alertas igual que el canal

- T+1 canal: municipios alertados 73 de 76; falsas 342; top 10% (8 mpios) se lleva 26% de las falsas; racha máx 4 meses, mediana 2
- T+1 modelo: municipios alertados 74 de 76; falsas 322; top 10% (8 mpios) se lleva 25% de las falsas; racha máx 5 meses, mediana 2
- T+2 canal: municipios alertados 73 de 76; falsas 480; top 10% (8 mpios) se lleva 22% de las falsas; racha máx 4 meses, mediana 2
- T+2 modelo: municipios alertados 74 de 76; falsas 447; top 10% (8 mpios) se lleva 20% de las falsas; racha máx 4 meses, mediana 2

- Los dos alertan a casi todos los municipios (73 y 74 de 76) en los siete años.
- **Las falsas alertas no se concentran**: el 10 % de municipios con más falsas se
  lleva entre el 20 y el 26 %, igual con el canal y con el modelo.
- **Las rachas son cortas**: la mediana es de 2 meses seguidos alertados y la más
  larga de 4 o 5. El modelo no deja a un municipio alertado meses enteros.
- Para la sustentación: el modelo no cambia la forma del trabajo de la secretaría;
  emite un poco menos de falsas alertas (322 frente a 342 en T+1) repartidas igual.

Logística con clima y canal condicionado al 10 % de la sección 0, 2018-2024 salvo que se diga otra cosa; predicciones de la tanda 15, sin modelos nuevos.
