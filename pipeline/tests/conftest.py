"""Límites de todas las pruebas del subproyecto: sin red ni datos publicados."""

import builtins
import os
import socket
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture(autouse=True)
def enforce_pipeline_boundaries(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Bloquear conexiones reales, imports inversos y acceso a resultados.

    Args:
        monkeypatch: Restaurador de cambios locales al terminar cada prueba.

    Yields:
        Control a la prueba con los límites activados.
    """

    def no_network(*args: Any, **kwargs: Any) -> None:
        """Fallar antes de cualquier conexión o resolución de DNS real."""
        pytest.fail("Las pruebas del pipeline no pueden acceder a red")

    original_import = builtins.__import__

    def isolated_import(name: str, *args: Any, **kwargs: Any) -> Any:
        """Impedir dependencias inversas con el producto desplegado."""
        assert name.split(".")[0] not in {"app", "sat_api", "sat_dengue"}, name
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", isolated_import)
    monkeypatch.setattr(socket.socket, "connect", no_network)
    monkeypatch.setattr(socket.socket, "connect_ex", no_network)
    monkeypatch.setattr(socket, "create_connection", no_network)
    monkeypatch.setattr(socket, "getaddrinfo", no_network)
    monkeypatch.setenv("DO_NOT_TRACK", "1")
    monkeypatch.setenv("HF_HUB_DISABLE_TELEMETRY", "1")
    monkeypatch.setenv("MLFLOW_DISABLE_TELEMETRY", "true")
    monkeypatch.setenv("MLFLOW_DISABLE_AGENT_HINT", "1")
    protected = Path(__file__).resolve().parents[2] / "datos" / "resultados"
    v2 = Path(__file__).resolve().parents[3] / "SAT-Dengue-V2"
    active = True

    def audit(event: str, args: tuple[Any, ...]) -> None:
        """Bloquear acceso de archivos de publicación por cualquier open de Python."""
        if active and event == "open" and isinstance(args[0], (str, bytes)):
            path = Path(os.fsdecode(args[0])).resolve()
            assert not path.is_relative_to(protected)
            assert not path.is_relative_to(v2)

    sys.addaudithook(audit)
    try:
        yield
    finally:
        active = False
