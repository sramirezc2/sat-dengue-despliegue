"""Generador optativo de paridad sintética desde blobs fijados, nunca desde datos V2."""

import argparse
import ast
import hashlib
import json
import runpy
import subprocess
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

COMMIT = "916a69f3bb73f2ffbb0ec038b8bef887ee91adf1"
SOURCE_PATHS = (
    "src/sat_dengue/canonical/table.py",
    "src/sat_dengue/data/consolidation.py",
    "src/sat_dengue/experiments/onset.py",
    "src/sat_dengue/training_preparation/contract.py",
    "src/sat_dengue/training_preparation/validation.py",
    "tests/unit/test_canonical_model_table.py",
    "tests/unit/test_training_preparation.py",
    "tests/unit/test_training_temporal.py",
    "pyproject.toml",
)
PROJECT = Path(__file__).resolve().parents[1]


def selected_namespace(source: bytes, names: set[str], namespace: dict[str, Any]) -> None:
    """Ejecutar solo definiciones puras seleccionadas, excluyendo imports e I/O.

    Args:
        source: Blob obtenido con git show, no desde el working tree V2.
        names: Símbolos usados directamente por el productor de referencia.
        namespace: Entorno aislado con pandas y NumPy de versiones fijadas.
    """
    nodes = []
    for node in ast.parse(source).body:
        assigned = (
            {t.id for t in node.targets if isinstance(t, ast.Name)}
            if isinstance(node, ast.Assign)
            else {getattr(node, "name", "")}
        )
        if assigned & names:
            nodes.append(node)
    exec(compile(ast.Module(nodes, type_ignores=[]), "pinned-v2-definitions", "exec"), namespace)


def main() -> None:
    """Generar o verificar exclusivamente la referencia sintética versionada."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--v2", required=True, type=Path)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    sources = {
        path: subprocess.check_output(["git", "-C", str(args.v2), "show", f"{COMMIT}:{path}"])
        for path in SOURCE_PATHS
    }
    fixture = runpy.run_path(str(PROJECT / "tests/fixtures/canonical_fixture.py"))
    namespace: dict[str, Any] = {"pd": pd, "np": np, "Any": Any}
    selected_namespace(
        sources[SOURCE_PATHS[1]],
        {
            "CLIMATE_MONTHLY_SUM_MAP",
            "CLIMATE_MONTHLY_MEAN_MAP",
            "Y_REFERENCE_YEARS",
            "Y_PERCENTILE_METHOD",
            "CANAL_PERCENTILES",
            "CANAL_ZONE_VALUES",
            "PipelineValidationError",
            "add_months",
            "percentile_type7",
            "history_periods_for_target",
            "classify_endemic_zone",
            "compute_current_endemic_channel",
        },
        namespace,
    )
    selected_namespace(
        sources[SOURCE_PATHS[0]],
        {
            "KEYS",
            "COUNTS",
            "CLIMATE",
            "CHANNEL",
            "LAGS",
            "PREDICTORS",
            "validate_source",
            "build_table",
            "predictor_matrix",
            "coverage_report",
        },
        namespace,
    )
    panel = fixture["make_panel"]()
    table, schema = namespace["build_table"](panel)
    payload = {
        "table": fixture["frame_payload"](table),
        "schema": schema,
        "predictors": fixture["frame_payload"](namespace["predictor_matrix"](table, schema)),
        "coverage": namespace["coverage_report"](table, schema),
    }
    encode = fixture["canonical_bytes"]
    output = encode(payload)
    receipt = encode(
        {
            "repository": "j-mauro-r/SAT-Dengue-V2",
            "commit": COMMIT,
            "source_sha256": {p: hashlib.sha256(b).hexdigest() for p, b in sources.items()},
            "input_sha256": hashlib.sha256(encode(fixture["frame_payload"](panel))).hexdigest(),
            "output_sha256": hashlib.sha256(output).hexdigest(),
            "method": "git show + AST de definiciones puras; fixture artificial 2018–2024",
            "pandas": pd.__version__,
            "numpy": np.__version__,
        }
    )
    for filename, content in (
        ("canonical_expected.json", output),
        ("canonical_receipt.json", receipt),
    ):
        path = PROJECT / "tests/fixtures" / filename
        if args.verify:
            if path.read_bytes() != content:
                raise ValueError(f"Referencia sintética diferente: {filename}")
        else:
            path.write_bytes(content)
    print(json.loads(receipt))


if __name__ == "__main__":
    main()
