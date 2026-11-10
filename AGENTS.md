# SAT DENGUE

Repositorio oficial `sramirezc2/sat-dengue-despliegue`: API y tablero desplegados,
con un subproyecto Kedro independiente para construir progresivamente el E2E.
Leer `plan.md` y `docs/architecture/pipeline-e2e.md` antes de cada tarea.

- `app/`: producto desplegado; `pipeline/`: cálculo y dependencias propias.
- `datos/resultados/`: única frontera de publicación; `docker/` y `scripts/`:
  despliegue y operación; `docs/`: arquitectura, decisiones y evidencia.
- Flujo permitido: `pipeline/ -> datos/resultados/ -> app/api/ -> app/dashboard/`.
- La API nunca importa Kedro ni `pipeline/`; el pipeline nunca importa ni escribe
  en `app/`. Las dependencias científicas quedan fuera de la imagen de API.
- Toda la implementación continúa en `feature/pipeline-e2e` y termina en un único
  PR. No publicar ni abrir PR sin autorización. CI remota, ruleset, aprobación y
  checks obligatorios deben verificarse antes del merge (DEC-006).
- 2025 es evaluación previamente utilizada: queda fuera del desarrollo científico
  y no puede presentarse como holdout intacto.
- No agregar secretos, datos nuevos, modelos ni archivos pesados a Git.
- No crear ni editar celdas Markdown en notebooks sin autorización formal.
- Python con tipado y docstrings estilo Google; cambios de comportamiento con
  pruebas proporcionales.

Skills obligatorias de la fábrica ([catálogo](docs/agents/skills-catalog.md)):

- Usar `$sat-dengue-experiment` para crear, repetir, ejecutar, concluir o comparar experimentos.
- Usar `$sat-dengue-scientific-review` antes de aprobar una receta científica o aceptar conclusiones.
- Usar `$sat-dengue-verification` antes de declarar cambios terminados o listos para push.
- Usar `$sat-dengue-recovery` ante ejecuciones fallidas, bloqueadas o incompletas.

Comandos desde la raíz:

```sh
python -m pip install -r app/api/requirements-dev.txt
(cd app/api && python -m pytest)
(cd app/dashboard && bun install --frozen-lockfile && bun run lint && bun run test)
(cd app/dashboard && NITRO_PRESET=node_server bun run build)
uv lock --check --project pipeline
uv sync --locked --project pipeline
uv run --directory pipeline ruff check .
uv run --directory pipeline pytest
uv run --directory pipeline kedro run --pipelines synthetic
git diff --check origin/main...HEAD
```
