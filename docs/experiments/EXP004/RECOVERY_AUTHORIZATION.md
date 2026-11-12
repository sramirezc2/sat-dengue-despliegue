# EXP004 — autorización humana de recuperación ambiental

Fecha: 12 de noviembre de 2026. Autoridad: persona usuaria en la conversación.
Complementa la aprobación R2; no la modifica ni sustituye.

La persona autorizó materializar exclusivamente los cinco archivos ya
verificados desde la caché de la fábrica al inbox que requiere el retroanálisis,
con temporales, reemplazo atómico y validación de nombre, tamaño y SHA-256.
Se rechazan symlinks, archivos adicionales y un destino preexistente.

Autorizó exactamente una invocación adicional:

```sh
uv run --locked --directory pipeline kedro run --pipeline retroanalisis --env exp004
```

Se conservan intactos el primer intento fallido, la receta R2, los resultados
de fábrica y toda la evidencia histórica. No se autoriza repetir la fábrica,
modificar receta o parámetros, descargar datos de nuevo, borrar evidencia,
seleccionar semillas, hacer push, PR o merge.

Después de la corrida se validarán los seis CSV, los conjuntos comparados por
horizonte, lectura efectiva, semilla y fold, la exclusión de 2025 y los hashes.
Se reportará el resultado y se detendrá el trabajo. EXP004 debe conservar
RUNNING/PENDING. Esta autorización no resuelve la ausencia de la curva completa
en la evidencia de fábrica, no asigna conclusión científica ni selecciona campeón.

La materialización será solo local mediante el resolver existente: no se
invoca un proveedor remoto ni se consulta, imprime o persiste una credencial.
El código, los archivos congelados y los recibos anteriores permanecen sin cambios.
