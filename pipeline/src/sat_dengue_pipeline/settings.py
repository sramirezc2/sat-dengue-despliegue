"""Configuración mínima para un smoke test sin persistencia ni secretos."""

# No se requiere conf/local: este smoke test solo usa configuración versionada.
CONFIG_LOADER_ARGS = {"base_env": "base", "default_run_env": "base"}
