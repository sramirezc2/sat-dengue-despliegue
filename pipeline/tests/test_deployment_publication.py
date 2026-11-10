"""Publicación pura y transaccional sobre entradas exclusivamente artificiales."""

import hashlib
import json
from pathlib import Path

import pytest
from fixtures.publication_fixture import GENERATED, PROCEDURE, publication_rows

from sat_dengue_pipeline.pipelines.deployment_publication.contract import validate_package
from sat_dengue_pipeline.pipelines.deployment_publication.io import (
    load_schema,
    promote,
    stage_package,
    validate_staging,
)
from sat_dengue_pipeline.pipelines.deployment_publication.package import (
    PublicationConfig,
    build_package,
)


@pytest.fixture
def package():
    """Construir el paquete mínimo aceptado por ambos contratos del producto."""
    return build_package(
        *publication_rows(), PublicationConfig(PROCEDURE, "synthetic-v1", GENERATED)
    )


def test_migrated_package_matches_legacy_exact_bytes(package):
    """Congelar equivalencia de los JSON; el manifiesto queda fuera del contrato HTTP."""
    fixtures = Path(__file__).parent / "fixtures"
    expected = json.loads((fixtures / "publication_expected.json").read_text(encoding="utf-8"))
    receipt = json.loads((fixtures / "publication_receipt.json").read_text(encoding="utf-8"))
    assert {file.name: json.loads(file.content) for file in package.files} == expected
    assert {
        file.name: hashlib.sha256(file.content).hexdigest() for file in package.files
    } == receipt["files"]
    validate_package(package, load_schema())


def test_transaction_and_manifest(package, tmp_path):
    """Publicar solo tras validar el conjunto y registrar tamaños/huellas exactas."""
    schema = load_schema()
    staged = stage_package(package, tmp_path / "results", schema)
    assert not staged.destination.exists()
    receipt = promote(validate_staging(staged, schema), schema)
    assert receipt["status"] == "COMMITTED"
    assert not staged.root.exists()
    assert len(list((tmp_path / "results").glob("*.json"))) == 2
    manifest = json.loads((tmp_path / "results/.publication/manifest.json").read_bytes())
    assert manifest["files"] == receipt["files"]
    for row in manifest["files"]:
        data = (tmp_path / "results" / row["name"]).read_bytes()
        assert len(data) == row["size_bytes"]
        assert hashlib.sha256(data).hexdigest() == row["sha256"]
    assert manifest["selection"]["forced"] is False


def test_repeat_publication_exact_bytes(package, tmp_path):
    """Fecha/configuración fijas producen los mismos bytes, incluidos manifiesto y UUID."""
    schema = load_schema()
    out = tmp_path / "results"
    outputs = []
    for _ in range(2):
        promote(validate_staging(stage_package(package, out, schema), schema), schema)
        outputs.append(
            {p.relative_to(out).as_posix(): p.read_bytes() for p in out.rglob("*") if p.is_file()}
        )
    assert outputs[0] == outputs[1]
