"""Aceptación sintética intensiva diferida hasta la autorización posterior a EXP006."""

import json
import os
import subprocess
from pathlib import Path

import pytest
from kedro.io import DataCatalog, MemoryDataset
from kedro.runner import SequentialRunner

from sat_dengue_pipeline.models.logistic import LogisticOnsetAdapter, canonical_json
from sat_dengue_pipeline.pipelines.risk_2025_publication.pipeline import create_pipeline
from sat_dengue_pipeline.risk import nodes
from sat_dengue_pipeline.risk.configuration import ROOT, sha


@pytest.mark.intensive
def test_five_sources_to_http_and_dashboard_three_isolated_runs(tmp_path, monkeypatch):
    """Ejercitar el grafo completo N=3 artificial sin publicar datos científicos.

    Usa reservas independientes y fuente artificial del mismo grafo Kedro. La
    respuesta HTTP real de TestClient alimenta la prueba React. No abre servicios.
    """
    original = nodes.local_path

    def isolated(value, *, published=False):
        """Validar primero el confinamiento normal y reservar solo en este fixture."""
        original(value, published=published)
        return tmp_path / Path(value).name

    monkeypatch.setattr(nodes, "local_path", isolated)
    base = {
        "mode": "materialize",
        "source": "synthetic",
        "artifact_directory": "",
        "artifact_sha256": "",
        "certificate": "",
        "certificate_sha256": "",
        "edition": "synthetic-only",
    }
    runs = []
    original_fit = LogisticOnsetAdapter.fit
    calls = []

    def spy(self, X, y):
        """Contar ajustes del grafo completo."""
        calls.append(1)
        return original_fit(self, X, y)

    monkeypatch.setattr(LogisticOnsetAdapter, "fit", spy)

    def run(settings):
        """Consumir parámetros por catálogo, igual que la entrada Kedro."""
        catalog = DataCatalog(
            {
                "params:risk_2025": MemoryDataset(data=settings),
                "risk_context": MemoryDataset(copy_mode="assign"),
                "risk_receipt": MemoryDataset(),
            }
        )
        SequentialRunner().run(create_pipeline(), catalog)
        return catalog.load("risk_receipt")

    for index in range(1, 4):
        settings = {
            **base,
            "artifact_directory": f"data/model-{index}",
            "run_directory": f"data/run-{index}",
        }
        result = run(settings)
        assert result["status"] == "MATERIALIZED_NOT_PUBLISHED"
        assert not (tmp_path / f"run-{index}/results").exists()
        runs.append({k: result[k] for k in ("execution_id", "artifact_sha256", "package_sha256")})
    assert len(calls) == 3
    assert len({r["artifact_sha256"] for r in runs}) == 1
    assert len({r["package_sha256"] for r in runs}) == 1
    proof = {
        "status": "CERTIFIED_N3",
        "artifact_sha256": runs[0]["artifact_sha256"],
        "package_sha256": runs[0]["package_sha256"],
        "runs": runs,
    }
    certificate = tmp_path / "certificate.json"
    certificate.write_bytes(canonical_json(proof))

    def forbidden(*args, **kwargs):
        """El pipeline ordinario no puede entrenar ni construir etiquetas."""
        pytest.fail("Aprendizaje o etiquetas durante publicación")

    import sat_dengue_pipeline.preparation as preparation

    monkeypatch.setattr(LogisticOnsetAdapter, "fit", forbidden)
    monkeypatch.setattr(preparation, "build_labels", forbidden)
    frozen = {
        **base,
        "mode": "frozen",
        "artifact_directory": "data/model-1",
        "artifact_sha256": proof["artifact_sha256"],
        "certificate": "data/certificate.json",
        "certificate_sha256": sha(certificate.read_bytes()),
        "run_directory": "data/publication",
    }
    run(frozen)
    edition = tmp_path / "publication/results"
    assert len(list(edition.glob("prioridades_*.json"))) == 12
    for file in sorted(edition.glob("prioridades_*.json")):
        d = json.loads(file.read_bytes())
        selected = [
            r["municipality_code"] for r in d["municipalities"] if r["selected_for_attention"]
        ]
        assert selected == [f"50{i}" for i in range(900, 908)]
        assert d["target_period"].startswith("2025-")
    api_check = """
import json, sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sat_api.risk_repository import RiskRepository, create_risk_router
app = FastAPI()
app.include_router(create_risk_router(RiskRepository(Path(sys.argv[1]), allow_synthetic=True)))
client = TestClient(app)
assert len(client.get('/api/prioridades/v1/periodos').json()) == 12
response = client.get('/api/prioridades/v1?target_period=2025-01')
assert response.status_code == 200
Path(sys.argv[2]).write_text(json.dumps(response.json()))
"""
    response_file = tmp_path / "api-response.json"
    env = {k: v for k, v in os.environ.items() if k != "HF_TOKEN"}
    env["PYTHONPATH"] = str(ROOT / "app/api")
    api_python = (
        ROOT / "app/api/.venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    )
    subprocess.run(
        [str(api_python), "-c", api_check, str(edition), str(response_file)],
        check=True,
        env=env,
        capture_output=True,
    )
    env["SATD_RISK_E2E_RESPONSE"] = str(response_file)
    subprocess.run(
        ["bun", "run", "test", "src/test/risk-ranking.test.tsx", "-t", "respuesta E2E"],
        cwd=ROOT / "app/dashboard",
        env=env,
        check=True,
        capture_output=True,
    )
