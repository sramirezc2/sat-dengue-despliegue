"""Recoger salidas sintéticas reales reutilizando los productores y gates existentes."""

import hashlib
import json
from importlib.metadata import version
from pathlib import Path

from sat_dengue_pipeline.raw.worker import enforce_boundaries


def collect() -> dict:
    """Certificar nuevamente N=3 y comparar artefactos con los goldens de tareas 13/14."""
    enforce_boundaries(synthetic=True)
    from kedro.framework.session import KedroSession
    from kedro.framework.startup import bootstrap_project

    from sat_dengue_pipeline.raw.fixture import fixture_config, synthetic_bundle
    from sat_dengue_pipeline.raw.reproducibility import canonical_reproducibility

    project = Path(__file__).resolve().parents[1]
    bootstrap_project(project)
    with KedroSession.create(project_path=project, save_on_close=False) as session:
        metrics = session.run(pipeline_name="synthetic")["synthetic_metrics"].load()
    assert metrics == {"synthetic_check_rows": 1, "synthetic_mae": 5.0, "synthetic_mse": 25.0}
    bundle, inventory = synthetic_bundle(project / "data/portability/raw")
    certificate = canonical_reproducibility(
        bundle, fixture_config(), project / "data/portability/n3", inventory
    )
    assert (
        certificate.hashes
        == ("4ca14c3c07079130606a91274a516e083b513c6a1a7afe41d8df92be9b3bb046",) * 3
    )
    assert (
        certificate.semantic_digests
        == ("26cc689566b05ffaf46a42aaa8311cca0ffc3137e31af6f64cfb1e9834f6b957",) * 3
    )
    expected = json.loads((project / "tests/fixtures/publication_receipt.json").read_bytes())[
        "files"
    ]
    actual = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (project / "data/deployment-publication/results").glob("*.json")
    }
    assert actual == expected
    metrics_bytes = json.dumps(metrics, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {
        "synthetic_metrics": metrics,
        "synthetic_metrics_sha256": hashlib.sha256(metrics_bytes).hexdigest(),
        "canonical_n3_sha256": certificate.hashes,
        "canonical_n3_semantic_digest": certificate.semantic_digests,
        "publication_sha256": actual,
        "packages": {
            name: version(name)
            for name in (
                "kedro",
                "numpy",
                "pandas",
                "scipy",
                "scikit-learn",
                "mlflow-skinny",
                "jsonschema",
            )
        },
    }


if __name__ == "__main__":
    target = Path(__file__).resolve().parents[1] / "data/portability/outputs.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(json.dumps(collect(), indent=2, sort_keys=True).encode("utf-8"))
