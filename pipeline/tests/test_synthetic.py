"""Verificar orquestación, determinismo y aislamiento del smoke test."""

import importlib.abc
import os
import socket
import sys
from pathlib import Path
from typing import Any

import pytest
from kedro.framework.project import find_pipelines
from kedro.framework.session import KedroSession
from kedro.framework.startup import bootstrap_project

from sat_dengue_pipeline.pipeline_registry import register_pipelines
from sat_dengue_pipeline.pipelines.synthetic.nodes import (
    generate_synthetic_data,
    prepare_synthetic_data,
)

PROJECT = Path(__file__).resolve().parents[1]
EXPECTED = {"synthetic_check_rows": 1, "synthetic_mae": 5.0, "synthetic_mse": 25.0}


def test_registry_and_discovery() -> None:
    """Kedro descubre y registra las cinco etapas del smoke test."""
    bootstrap_project(PROJECT)
    registered = register_pipelines()
    assert "synthetic" in find_pipelines()
    assert set(registered) == {
        "synthetic", "__default__", "canonical_build", "canonical_reproducibility"
    }
    assert len(registered["synthetic"].nodes) == 5
    assert registered["synthetic"].inputs() == {"params:synthetic_smoke.years"}
    assert registered["synthetic"].outputs() == {"synthetic_metrics"}


def test_synthetic_fixture_is_deterministic_and_ends_in_2024() -> None:
    """El fixture es artificial, determinista y no contiene años posteriores."""
    years = [2020, 2021, 2022, 2023, 2024]
    observations = generate_synthetic_data(years)
    assert observations == generate_synthetic_data(years)
    assert [row.year for row in observations] == years
    assert [row.value for row in observations] == [2.0, 4.0, 6.0, 8.0, 10.0]
    training, checking = prepare_synthetic_data(observations)
    assert len(training) == 4
    assert checking[0].year == 2024


@pytest.mark.parametrize("years", [[], [2024], [2023, 2023], [2024, 2023]])
def test_preparation_rejects_malformed_synthetic_fixture(years: list[int]) -> None:
    """La preparación rechaza un fixture vacío, corto o desordenado."""
    with pytest.raises(ValueError, match="fixture sintético"):
        prepare_synthetic_data(generate_synthetic_data(years))


def test_e2e_is_deterministic_without_product_imports_network_or_publication(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Ejecutar dos sesiones completas con límites de producto vigilados."""
    bootstrap_project(PROJECT)

    class RejectProductImports(importlib.abc.MetaPathFinder):
        """Impedir que el smoke test dependa del producto desplegado."""

        def find_spec(self, fullname: str, *args: Any, **kwargs: Any) -> None:
            """Fallar al intentar cargar un módulo de app o de la API."""
            assert fullname.split(".")[0] not in {"app", "sat_api"}, fullname

    def reject_network(*args: Any, **kwargs: Any) -> None:
        """Fallar si una etapa intenta establecer una conexión de red."""
        pytest.fail("El smoke test no debe acceder a red")

    monkeypatch.setattr(sys, "meta_path", [RejectProductImports(), *sys.meta_path])
    monkeypatch.setattr(socket.socket, "connect", reject_network)
    monkeypatch.setattr(socket, "create_connection", reject_network)
    monkeypatch.setenv("DO_NOT_TRACK", "1")
    product_data = PROJECT.parent / "datos" / "resultados"
    active = True

    def audit(event: str, args: tuple[Any, ...]) -> None:
        """Impedir lectura o publicación de datos reales durante el E2E."""
        if active and event == "open" and isinstance(args[0], (str, bytes)):
            path = Path(os.fsdecode(args[0])).resolve()
            assert not path.is_relative_to(product_data), path

    sys.addaudithook(audit)
    try:
        outputs = []
        for _ in range(2):
            with KedroSession.create(project_path=PROJECT, save_on_close=False) as session:
                results = session.run(pipeline_name="synthetic")
                outputs.append(results["synthetic_metrics"].load())
        assert outputs == [EXPECTED, EXPECTED]
    finally:
        active = False
