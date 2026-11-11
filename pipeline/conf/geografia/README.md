# Coordenadas de municipios (DIVIPOLA)

`divipola_coordenadas.csv`: código DANE, nombre y centroide (longitud y latitud, con
coma decimal, como lo publica la fuente) de los 1 122 municipios y áreas no
municipalizadas de Colombia. Fuente: DIVIPOLA del DANE, publicada en datos.gov.co
(conjunto «DIVIPOLA - Códigos municipios»), descargada el 8 de noviembre de 2026.

Lo usa el bloque de vecinos del retroanálisis (`domain/vecinos.py`) para elegir los
municipios más cercanos de cada uno. No entra a la tabla canónica ni a su digest.
