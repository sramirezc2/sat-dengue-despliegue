# Publicación de despliegue — tarea 14

Referencia de caracterización: `scripts/construir_resultados.py` en `32b6d06`.
Las pruebas ejecutan ese blob local de V3 con reloj fijo y entradas artificiales;
no leen V2, crudos o resultados reales. La salida congelada contiene dos JSON,
76 municipios ficticios, comparación y retroanálisis opcional. El recibo registra
el hash del código original, fecha fija y SHA-256 por archivo. Ningún JSON
versionado de `datos/resultados/` se regenera.

## Adaptaciones y defectos caracterizados

El legado desempata candidatos por orden físico cuando coinciden cobertura y
coste. Una prueba demuestra resultados diferentes al invertir dos filas. La
corrección de determinismo se separó de la migración en `37de562`: solo ante
igualdad exacta de ambos criterios se usa el identificador del candidato; las
comparaciones y listas del retroanálisis tienen orden estable sin modificar valores.

El legado no produce `INELIGIBLE`: un `y_status_t1=ineligible` termina en
`NOT_CALCULATED`. Se caracteriza y preserva ese comportamiento. El validador sí
admite `INELIGIBLE` como estado del contrato; no se inventa una nueva regla de
elegibilidad durante esta migración.

La validación productiva es autónoma: snapshot JSON Schema exportado del
contrato API inicial, más invariantes entre campos. Se comprueban el snapshot y
la salida contra los consumidores Pydantic y Zod en procesos externos de pruebas.
No se copia código ejecutable de API ni se introduce un import inverso. El
validador JSON Schema es dependencia fijada solo de `pipeline/` (4.23.0).

La fecha se inyecta; únicamente la frontera CLI consulta el reloj. El manifiesto
registra también candidato solicitado, selección automática/forzada y motivo,
sin añadir campos al JSON del producto ni promover champion. Su ubicación será
`.publication/manifest.json`, fuera del glob de resultados que consume la API.
Describe los archivos de esta transacción; los periodos ajenos ya publicados se
conservan. El recibo `COMMITTED` se devuelve solo después de promover todo el
conjunto. El manifiesto se reemplaza al final; errores de confirmación posteriores
a un reemplazo efectivo también activan rollback, probado en las tres posiciones.

La promoción prepara y valida el conjunto completo antes de tocar el destino;
usa reemplazos atómicos por archivo, backups y rollback ante excepciones. No
proporciona aislamiento de lectura de múltiples archivos ni garantías frente a
interrupción eléctrica o fallo del propio filesystem durante recuperación. No
se modifica el consumidor para simular esas garantías; se documentarán los
límites operacionales y la recuperación en `pipeline/README.md`. Si falla la
recuperación se conservan backups y se informa su ruta; no se oculta un fallo
de filesystem ni se afirma consistencia recuperada.

## Evidencia y operación

El wrapper conserva argumentos/defaults, ayuda y códigos 0/1/2, aviso de override,
recuperación T+1/T+2 y omisión de retroanálisis ausente. La equivalencia es **byte
a byte** en los cuatro casos caracterizados: auto/forzado y retro presente/ausente,
con fecha fija. El recibo `publication_receipt.json` congela los dos SHA originales.

El comando del wrapper usa `uv run --project pipeline` desde la raíz para
conservar su cwd histórico; Kedro y herramientas siguen usando `--directory`
(DEC-007). No se agrega entorno o manifiesto Python en la raíz. Los fixtures y
todos los ensayos de promoción usan `tmp_path`; el smoke explícito usa solo
`pipeline/data/deployment-publication/`, ignorado por Git. Los 22 resultados
históricos se leen únicamente como contrato del producto, según DEC-009.

La validación externa acepta los dos documentos generados y los 22 históricos
con los contratos Pydantic y Zod reales. El índice API requiere recarga/reinicio
para nuevos periodos, y los reemplazos respetan el TTL HTTP existente. No se
ejecuta esa operación sobre un despliegue ni se cambia API/tablero/Docker/S3.
La descarga/verificación remota del manifiesto no se implementa aquí.

La matriz de sistemas operativos (incluido comportamiento de locks/rename) queda
para tarea 15. Autenticación, reproducción real, candidatos reales e integración
desde fuentes crudas certificadas quedan para tarea 16. No hay promoción de
champion ni nueva evidencia científica sobre 2025.
