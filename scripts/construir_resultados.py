"""Envoltura temporal del publicador, ejecutable desde la raíz con el entorno bloqueado.

uv run --project pipeline python scripts/construir_resultados.py --help
"""

try:
    from sat_dengue_pipeline.pipelines.deployment_publication.cli import main
except ModuleNotFoundError:
    raise SystemExit(
        "ERROR: usar el entorno bloqueado: uv run --project pipeline "
        "python scripts/construir_resultados.py --help"
    ) from None


if __name__ == "__main__":
    main()
