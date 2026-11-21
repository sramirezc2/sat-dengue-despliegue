"""Importación explícita de la demo sin depender del directorio de ejecución."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@pytest.fixture(autouse=True)
def isolate_demo_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    """Evitar que una configuración privada del host afecte las pruebas artificiales."""
    monkeypatch.delenv("SATD_DEMO_MODEL_DIR", raising=False)
    monkeypatch.delenv("SATD_DEMO_CONTEXT_DIR", raising=False)
    monkeypatch.delenv("SATD_DEMO_CONTEXT_BUNDLE_URL", raising=False)
    monkeypatch.delenv("SATD_DEMO_CONTEXT_BUNDLE_SHA256", raising=False)
    monkeypatch.delenv("SATD_DEMO_CONTEXT_TOKEN", raising=False)
    monkeypatch.delenv("SATD_DEMO_CONTEXT_CACHE_DIR", raising=False)
