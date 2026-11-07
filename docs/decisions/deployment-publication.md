# Publicación de despliegue — tarea 14

Referencia de caracterización: `scripts/construir_resultados.py` en `32b6d06`.
Las pruebas ejecutan ese blob local de V3 con reloj fijo y entradas artificiales;
no leen V2, crudos o resultados reales. La salida congelada contiene dos JSON,
76 municipios ficticios, comparación y retroanálisis opcional. El recibo registra
el hash del código original, fecha fija y SHA-256 por archivo. Ningún JSON
versionado de `datos/resultados/` se regenera.

## Adaptaciones previstas y defectos caracterizados

El legado desempata candidatos por orden físico cuando coinciden cobertura y
coste. Una prueba demuestra resultados diferentes al invertir dos filas. La
corrección de determinismo se separará de la migración: solo ante igualdad exacta
de ambos criterios se usará el identificador del candidato; las comparaciones y
listas del retroanálisis tendrán orden estable sin modificar valores.

El legado no produce `INELIGIBLE`: un `y_status_t1=ineligible` termina en
`NOT_CALCULATED`. Se caracteriza y preserva ese comportamiento. El validador sí
admitirá `INELIGIBLE` como estado del contrato; no se inventa una nueva regla de
elegibilidad durante esta migración.

La validación productiva será autónoma: snapshot JSON Schema exportado del
contrato API inicial, más invariantes entre campos. Se comprobará el snapshot y
la salida contra los consumidores Pydantic y Zod en procesos externos de pruebas.
No se copia código ejecutable de API ni se introduce un import inverso. El
validador JSON Schema será dependencia fijada solo de `pipeline/`.

La fecha se inyecta; únicamente la frontera CLI consulta el reloj. El manifiesto
registrará también candidato solicitado, selección automática/forzada y motivo,
sin añadir campos al JSON del producto ni promover champion. Su ubicación será
`.publication/manifest.json`, fuera del glob de resultados que consume la API.

La promoción prepara y valida el conjunto completo antes de tocar el destino;
usa reemplazos atómicos por archivo, backups y rollback ante excepciones. No
proporciona aislamiento de lectura de múltiples archivos ni garantías frente a
interrupción eléctrica o fallo del propio filesystem durante recuperación. No
se modifica el consumidor para simular esas garantías; se documentarán los
límites operacionales y la recuperación.
