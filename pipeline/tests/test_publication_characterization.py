"""Congelar el comportamiento del publicador antes de migrar su implementación."""

import hashlib
import json
from pathlib import Path

from fixtures.legacy_publication import legacy_outputs
from fixtures.publication_fixture import write_inputs


def test_legacy_frozen_documents_and_bytes(tmp_path, monkeypatch):
    """Contenido, nombres, cantidad, estados y SHA coinciden con la referencia inicial."""
    paths = write_inputs(tmp_path / "inputs")
    outputs, source_sha = legacy_outputs(paths, tmp_path / "output", monkeypatch)
    fixture = Path(__file__).parent / "fixtures"
    expected = json.loads((fixture / "publication_expected.json").read_text())
    receipt = json.loads((fixture / "publication_receipt.json").read_text())
    assert len(outputs) == 2
    assert {name: json.loads(data) for name, data in outputs.items()} == expected
    assert {name: hashlib.sha256(data).hexdigest() for name, data in outputs.items()} == receipt[
        "files"
    ]
    assert source_sha == receipt["legacy_sha256"]


def test_legacy_ineligible_is_not_calculated():
    """Caracterizar que el legado nunca emite INELIGIBLE, sin cambiar esa decisión."""
    from fixtures.legacy_publication import legacy_module

    module = legacy_module()
    result = module.construir_resultado(
        horizonte="1",
        municipio="50000",
        periodo="2024-02",
        fila_panel={"y_status_t1": "ineligible"},
        prediccion=None,
        umbral=module.Umbral(0.8, 0.7),
        candidato="lightgbm",
        procedimiento="test",
        version_modelo="test",
    )
    assert result["availability_status"] == "NOT_CALCULATED"


def test_legacy_tie_depends_on_input_order():
    """Demostrar el defecto de desempate antes de introducir orden determinista."""
    import csv
    import tempfile

    from fixtures.legacy_publication import legacy_module

    module = legacy_module()
    with tempfile.TemporaryDirectory() as temp:
        path = Path(temp) / "comparison.csv"
        selected = []
        for candidates in (("gam", "lightgbm"), ("lightgbm", "gam")):
            with path.open("w", newline="") as stream:
                writer = csv.DictWriter(
                    stream, fieldnames=["candidate", "horizon", "detected_onsets", "false_alerts"]
                )
                writer.writeheader()
                writer.writerows(
                    {"candidate": c, "horizon": "1", "detected_onsets": "2", "false_alerts": "3"}
                    for c in candidates
                )
            selected.append(module.elegir_candidato(path)[0])
        assert selected == ["gam", "lightgbm"]
