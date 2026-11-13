"""Contrato y transporte de prioridades con una edición completamente artificial."""

import ast
import copy
import hashlib
import json
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sat_api.risk_contract import RiskRanking
from sat_api.risk_repository import RiskRepository, create_risk_router

ROOT = Path(__file__).resolve().parents[3]


def fixture() -> dict:
    """Leer el mismo fixture público que JSON Schema y Zod."""
    return json.loads((ROOT / "contracts/fixtures/risk-ranking.json").read_bytes())


@pytest.mark.parametrize(
    "value,valid", [(1.0, True), ("1", False), (True, False), (1.5, False)]
)
def test_json_numeric_integer_parity(value, valid):
    """Igualar la semántica de número integral de JSON Schema y Zod."""
    d = fixture()
    d["municipalities"][0]["risk_rank"] = value
    if valid:
        RiskRanking.model_validate(d)
    else:
        with pytest.raises(ValueError):
            RiskRanking.model_validate(d)


def test_json_schema_snapshot_matches_pydantic():
    """No permitir deriva entre el esquema publicado y su definición Pydantic."""
    expected = RiskRanking.model_json_schema()
    expected.update(
        {
            "$id": "satd-risk-ranking-v1",
            "$schema": "https://json-schema.org/draft/2020-12/schema",
        }
    )
    actual = json.loads(
        (
            ROOT / "pipeline/src/sat_dengue_pipeline/risk/ranking.schema.json"
        ).read_bytes()
    )
    assert actual == expected


@pytest.fixture
def edition(tmp_path) -> Path:
    """Crear doce documentos persistidos y su manifiesto sin importar pipeline/."""
    files = []
    for m in range(1, 13):
        d = fixture()
        index = 2025 * 12 + m - 3
        d.update(
            target_period=f"2025-{m:02d}",
            reference_period=f"{index // 12}-{index % 12 + 1:02d}",
        )
        d["data_cutoff"] = d["reference_period"]
        name = f"prioridades_T2_2025-{m:02d}.json"
        raw = json.dumps(d, sort_keys=True).encode()
        (tmp_path / name).write_bytes(raw)
        files.append(
            {
                "name": name,
                "size_bytes": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
            }
        )
    (tmp_path / ".publication").mkdir()
    (tmp_path / ".publication/manifest.json").write_text(
        json.dumps(
            {
                "schema": "satd-risk-ranking-v1",
                "candidate": "logistic_onset",
                "procedure": "SATD-RISK-2025-LOG-CLIMATE-v1",
                "artifact_sha256": "a" * 64,
                "files": files,
            }
        )
    )
    return tmp_path


def client(root: Path | None, *, synthetic: bool = True) -> TestClient:
    """Montar solo el transporte de lectura, sin iniciar un servicio."""
    app = FastAPI()
    app.include_router(
        create_risk_router(RiskRepository(root, allow_synthetic=synthetic))
    )
    return TestClient(app)


def test_global_budget_and_department_filter_keep_positions(edition):
    """Tolima no recibe ocho plazas nuevas al filtrar un ranking global."""
    api = client(edition)
    assert api.get("/api/prioridades/v1/periodos").json() == [
        f"2025-{m:02d}" for m in range(1, 13)
    ]
    params = {"target_period": "2025-01", "horizon": "T2"}
    all_rows = api.get("/api/prioridades/v1", params=params).json()["ranking"]
    filtered = api.get(
        "/api/prioridades/v1", params={**params, "department_code": "73"}
    ).json()
    assert filtered["ranking"] == all_rows
    assert len(filtered["visible_municipality_codes"]) == 47
    assert sum(t["selected_for_attention"] for t in all_rows["municipalities"]) == 8
    assert (
        min(
            t["risk_rank"]
            for t in all_rows["municipalities"]
            if t["department_code"] == "73"
        )
        == 30
    )
    assert api.post("/api/prioridades/v1").status_code == 405


def test_missing_corrupt_incomplete_or_synthetic_publication_fails(edition):
    """Ningún fallback al histórico ni publicación artificial accidental."""
    assert client(None).get("/api/prioridades/v1/periodos").json() == []
    assert (
        client(None).get("/api/prioridades/v1?target_period=2025-01").status_code == 404
    )
    assert (
        client(edition, synthetic=False).get("/api/prioridades/v1/periodos").status_code
        == 500
    )
    path = edition / "prioridades_T2_2025-01.json"
    path.write_bytes(path.read_bytes() + b" ")
    assert (
        client(edition).get("/api/prioridades/v1?target_period=2025-01").status_code
        == 500
    )
    assert client(edition).get("/api/prioridades/v1/periodos").status_code == 500


@pytest.mark.parametrize(
    "field", ["probability", "threshold", "y_true", "TP", "false_alerts"]
)
def test_forbidden_fields(field):
    """Rechazar las mismas extensiones prohibidas que publicador y cliente."""
    d = fixture()
    d["municipalities"][0][field] = 0
    with pytest.raises(ValueError):
        RiskRanking.model_validate(d)


@pytest.mark.parametrize(
    "change", ["calendar", "rank", "selection", "department", "version"]
)
def test_cross_field_invariants(change):
    """Fallar ante calendarios y relaciones incompatibles aunque cada campo tenga tipo válido."""
    d = copy.deepcopy(fixture())
    if change == "calendar":
        d["reference_period"] = "2025-12"
    elif change == "rank":
        d["municipalities"][1]["risk_rank"] = 1
    elif change == "selection":
        d["municipalities"][0]["selected_for_attention"] = False
    elif change == "department":
        d["municipalities"][0]["department_code"] = "73"
    else:
        d["schema_version"] = "unknown"
    with pytest.raises(ValueError):
        RiskRanking.model_validate(d)


def test_api_has_no_scientific_imports():
    """La nueva API depende únicamente de contratos y almacenamiento de lectura."""
    for name in ("risk_contract.py", "risk_repository.py"):
        tree = ast.parse((ROOT / "app/api/sat_api" / name).read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                assert not (node.module or "").startswith(
                    ("sat_dengue_pipeline", "sklearn", "kedro")
                )
