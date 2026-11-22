# Auditoría del hash del registro para el cierre local de Streamlit

Fecha: 2026-11-21. Base y HEAD inicial:
`2debfb4e3297755bd62fcff1b0ae2bbef3e62172`, rama
`feature/streamlit-configurable-prioritization`. `git fetch origin main` confirmó
la misma base sin mezclar ni sobrescribir los cambios locales existentes.

## Reproducción independiente: caso A

El fallo no es un caso de pytest: es el gate CLI
`pipeline/tools/check_experiment_preservation.py`, función `verify`, al comparar
el inventario extendido. Se ejecutó el comando exacto, tanto en la rama como
en un worktree temporal detached y limpio creado desde `origin/main`:

```sh
uv run --locked --directory pipeline python tools/check_experiment_preservation.py
```

En ambos devolvió **código 1** con
`Archivo protegido alterado: docs/experiments/registry.yml`.
La expectativa reside en `docs/decisions/risk-2025-preservation.json`, entrada
`sha256["docs/experiments/registry.yml"]`.

| Comparación anterior a corregir | Rama | Worktree limpio de main |
| --- | --- | --- |
| HEAD | `2debfb4e3297755bd62fcff1b0ae2bbef3e62172` | El mismo SHA, detached |
| Bytes del registro | Idénticos a main | Idénticos a la rama |
| SHA observado | `7421fe9f914883b8be9ec2a777a9e2418a580a52b50bc732be838cba15fee1a0` | El mismo |
| SHA esperado | `8f0740dc4657519746384d44ce47f93bf1f2dcc0e9d595469254281333416e37` | El mismo |
| Script y snapshot | Idénticos a main | Idénticos a la rama |
| Estado Git | Diff local de Streamlit, sin cambiar registro/script/snapshot | Limpio antes y después del gate |
| Resultado | FAIL | FAIL |

El worktree se creó bajo el espacio temporal ignorado de este repositorio, se
instaló con su propio lock y se retiró con `git worktree remove` tras el diagnóstico.
No se tocaron los otros worktrees ni ramas del usuario. Los logs anteriores y
posteriores quedan en `pipeline/data/demo-validation/`, ignorado por Git.

## Procedencia del cambio legítimo de bytes

1. El snapshot se introdujo en
   `00fd0e89fac773c49d9a8f090834b9ba7427fb47`, con base científica
   `a9c2c1abac386053b2e78f072bdb44e0141f4045`. El registro de ambas revisiones
   tiene el hash antiguo `8f0740dc…`.
2. El registro inmediatamente anterior a
   `c1d364de7280b303d9d975689899f6a391cfda75` conserva ese mismo hash.
3. El commit `c1d364de7280b303d9d975689899f6a391cfda75`, **PR #15** incorporado
   a main, añade la entrada `EXP315`. El cambio se originó en
   `a75542dbf9cf9a5d54d94a7c841ce219aa359a41`. El diff del registro es aditivo:
   las dos entradas históricas EXP001/EXP002 permanecen iguales, sin cambiar
   resultados ni evidencia. Este commit no actualizó el snapshot.
4. En el mismo commit están `docs/experiments/EXP315/registration.yml`,
   `SPECIFICATION.md` y `pipeline/conf/experiments/EXP315.yml`. El SHA-256 del
   protocolo es `61bea551be9d84452abddc520409a413e8e9c9940532cf8a170791ec79927b14`
   y el de configuración
   `ddff69f46a735a7e4f12e3e38b00c876844c558c7c7ac05ed60a4e20c28f0846`;
   ambos coinciden con las referencias del registro.
5. El registro de `c1d364d` y del `origin/main` actual es idéntico byte a byte,
   con hash `7421fe9f…`. Por tanto, esa identidad tiene procedencia Git concreta
   anterior a esta tarea; no deriva de un resultado modificado para pasar el gate.

Esta auditoría acredita identidad y procedencia del registro integrado. **No
aprueba EXP315**: se conserva su estado RUNNING existente, aunque su especificación
y propuesta señalan falta de aprobación. No se corrige esa semántica, se crean
conclusiones ni se ejecuta el experimento dentro de este alcance de software.

## Corrección mínima y controles conservados

Se reemplazó **únicamente el valor literal** del hash del registro en el snapshot
extendido por `7421fe9f914883b8be9ec2a777a9e2418a580a52b50bc732be838cba15fee1a0`.
Se conservaron el registro, las 127 claves del inventario, los otros 126 hashes,
el snapshot original de 49 protecciones y el digest de las 22 publicaciones.
El `base_commit` sigue identificando el origen histórico del inventario; esta
excepción documentada actualiza solo el pin del registro ampliado posteriormente.

El gate sigue comparando bytes contra una expectativa literal e independiente.
No calcula la expectativa a partir del archivo bajo prueba ni permite múltiples
hashes. Cualquier modificación futura del registro vuelve a fallar hasta una
revisión explícita con procedencia. El script no cambió ni se omitió su ejecución.

Preservación antes: FAIL idéntico en la rama y en main limpio. Después:

```sh
uv run --locked --directory pipeline python tools/check_experiment_preservation.py
uv run --locked --directory pipeline python -O tools/check_experiment_preservation.py
```

Ambos **PASS**: 49 protecciones originales, 127 extendidas, 22 JSON, 16 recibos
previos e identidad N=3 de T16 intactos. Digest de publicaciones:
`4d3ddd3890a6a622b658fc2b1ef0159d0da6bc855cacc2c5b62854290623e16e`.
Las regresiones de la CLI siguen exigiendo rechazo de alteraciones tanto en
Python normal como optimizado. No se reescribió ninguna evidencia científica.
