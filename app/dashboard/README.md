# Tablero del SAT Dengue

Interfaz de solo lectura del sistema de alerta temprana de dengue para Tolima y
Meta. Presenta los resultados de evaluación que publica la API del mismo
repositorio; no calcula nada, no entrena nada y no guarda estado del usuario.

Para el sistema completo, su despliegue y su operación, ver el
[README de la raíz](../../README.md).

## Qué muestra

En orden de aparición, y ese orden es deliberado:

1. **Estado de gobernanza.** Lo primero que se ve, antes que cualquier cifra.
   Declara que el modelo no está aprobado por la compuerta G5, que no hay
   champion seleccionado y que las alertas no sirven para decisiones
   operativas. Enlaza a la bitácora experimental y a la propuesta de política
   de decisión, para que el estado no quede afirmado sin evidencia detrás.
2. **Situación observada del mes de referencia.** Casos notificados y zona del
   canal endémico, con los cortes P25, mediana y P75 del mes.
3. **Pronósticos T+1 y T+2.** Probabilidad estimada de superar el P75
   histórico del mes objetivo, el umbral aplicado y si eso constituye alerta.
   Cada tarjeta aclara que es una probabilidad de superar un umbral y no un
   número esperado de casos.
4. **Canal endémico.** Serie del municipio contra sus bandas históricas, con el
   mes de referencia marcado. Los meses posteriores al de referencia no
   muestran casos, porque en ese momento no se conocían.
5. **Representación territorial** del departamento, con alternancia T+1/T+2 y
   una tabla accesible equivalente.
6. **Contexto histórico del modelo** y detalle técnico desplegable.

## Configuración

Todo lo operativo se parametriza por variables de entorno de Vite. Copiar
`.env.example` a `.env.local` y ajustar:

| Variable | Qué hace | Por defecto |
| --- | --- | --- |
| `VITE_API_BASE_URL` | Origen absoluto de la API. Vacío usa el mismo origen que el tablero, que es lo normal en producción porque ambos van detrás del mismo proxy. Solo admite HTTP y HTTPS, sin credenciales ni parámetros. | vacío |
| `VITE_REPOSITORIO_URL` | Repositorio público de donde cuelgan los documentos enlazados en el banner de gobernanza. Solo HTTPS. | el repositorio del proyecto |
| `API_PROXY_TARGET` | Solo para desarrollo: a qué origen reenvía Vite las peticiones de `/api`. | — |

La configuración se valida al arrancar y falla con un mensaje explícito, en vez
de degradar silenciosamente a un valor cualquiera.

## Desarrollo

Desde la raíz del repositorio, levantar primero la API:

```sh
uvicorn sat_api.main:app --app-dir app/api --reload
```

Y en otra terminal el tablero, apuntando el proxy a esa API:

```sh
cd app/dashboard
bun install --frozen-lockfile
API_PROXY_TARGET=http://127.0.0.1:8000 bun run dev
```

Para levantar las dos piezas juntas tal como corren en la instancia:

```sh
docker compose -f docker/docker-compose.yml --env-file .env up -d --build
```

## Cómo habla con la API

El tablero pide `GET /api/dashboard?department_code={DANE}&period={YYYY-MM}` y
consulta `GET /api/salud` para saber qué periodos hay publicados, de modo que
nunca solicita una combinación que no existe.

La respuesta se valida contra un esquema de Zod **antes** de construir el modelo
de vista, y un único adaptador hace esa conversión. Una respuesta que no cumpla
el contrato se trata como fallo: se limpia el resultado visible y se exige un
reintento explícito. No existe un respaldo con datos de demostración, a
propósito, porque un tablero que inventa datos cuando falla la red es peor que
uno que se queda en blanco.

## Pruebas

```sh
bun run test
```

Las pruebas de integración montan la vista contra respuestas fijas y verifican
el contrato, el orden de las secciones y el comportamiento ante fallos.
