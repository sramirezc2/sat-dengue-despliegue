"""Aprobación normativa prospectiva con evidencia previa intacta."""

from pathlib import Path

import pytest
from fixtures.scientific_fixture import repository

from sat_dengue_pipeline.experiment_management.configuration import load_configuration
from sat_dengue_pipeline.experiment_management.registry import Registry
from sat_dengue_pipeline.raw.contract import sha256

ROOT = Path(__file__).resolve().parents[2]


def test_current_contract_is_approved_and_loadable(tmp_path: Path) -> None:
    """Una receta nueva valida el hash y el estado del contrato aprobado."""
    _, entry = repository(tmp_path)
    entry = Registry(tmp_path).get(entry["experiment_id"])
    document = (tmp_path / "docs/experiments/contrato.md").read_text(encoding="utf-8")
    assert "- **Versión:** 1.0.0" in document
    assert "- **Estado:** `APROBADO`" in document
    assert "- **Autoridad:** equipo SAT DENGUE" in document
    config = load_configuration(tmp_path, entry)
    assert config["governance"]["champion_status"] == "NOT_SELECTED"
    assert config["governance"]["operational_authorization"] is False


def test_historical_proposal_does_not_authorize_new_execution(tmp_path: Path) -> None:
    """La aparición de APROBADO en otra parte del texto no sustituye su estado."""
    import yaml

    config, entry = repository(tmp_path)
    entry = Registry(tmp_path).get(entry["experiment_id"])
    contract = tmp_path / "docs/experiments/contrato.md"
    contract.write_text(
        contract.read_text(encoding="utf-8").replace(
            "- **Estado:** `APROBADO`", "- **Estado:** `PROPUESTA_PARA_APROBACION`"
        ),
        encoding="utf-8",
    )
    config["scientific_evaluation"]["contract"]["sha256"] = sha256(contract)
    path = tmp_path / entry["configuration"]
    path.write_text(yaml.safe_dump(config), encoding="utf-8")
    entry["configuration_sha256"] = sha256(path)
    with pytest.raises(ValueError, match="Contrato aprobado"):
        load_configuration(tmp_path, entry)


@pytest.mark.parametrize(
    "name,digest",
    [
        ("scientific-evaluation-validation.json",
         "978946e66e558dee88e06544ea7f3af5c9ed89292b637d21a44d467bd6d791a7"),
        ("seed-aggregation-validation.json",
         "74fcd322d917197575b454ffff86338caba23cb8cc9ff4a7347b07ae913ac875"),
    ],
)
def test_historical_contract_receipts_remain_unchanged(name: str, digest: str) -> None:
    """Los recibos previos conservan los bytes y la norma que tenían al producirse."""
    assert sha256(ROOT / "docs/evidence/pr3" / name) == digest
