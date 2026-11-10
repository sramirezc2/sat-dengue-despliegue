"""Proceso limpio que ejecuta el mismo grafo Kedro interno, sin red ni credencial."""

import json
import os
import sys
import time
from pathlib import Path


def main() -> int:
    """Cargar solo request local, ejecutar etapas y emitir recibo seguro."""
    os.environ.pop("HF_TOKEN", None)
    path = Path(sys.argv[1])
    request = json.loads(path.read_bytes())
    from sat_dengue_pipeline.raw.worker import enforce_boundaries

    enforce_boundaries(False)
    from kedro.io import DataCatalog, MemoryDataset
    from kedro.runner import SequentialRunner

    from sat_dengue_pipeline.acquisition.contracts import ResolvedBundle, ResolvedFile
    from sat_dengue_pipeline.factory.configuration import validate_configuration
    from sat_dengue_pipeline.factory.engine import FactoryGateError, FactoryRun, source_lineage
    from sat_dengue_pipeline.pipelines.factory_validation.pipeline import create_run_pipeline
    from sat_dengue_pipeline.raw.serialization import canonical_bytes

    config = validate_configuration(request["configuration"])
    data = request["bundle"]
    files = tuple(ResolvedFile(**{**f, "path": Path(f["path"])}) for f in data.pop("files"))
    bundle = ResolvedBundle(**data, files=files)
    run = FactoryRun(bundle, config, path.parent, source_lineage(bundle, config))
    started = time.perf_counter()
    outputs = (
        "factory_context",
        "factory_canonical",
        "factory_roles",
        "factory_checked",
        "factory_fitted",
        "factory_predictions",
        "factory_evaluated",
        "factory_receipt",
    )
    datasets = {name: MemoryDataset(copy_mode="assign") for name in outputs}
    datasets["factory_context"] = MemoryDataset(data=run, copy_mode="assign")
    try:
        result = SequentialRunner().run(create_run_pipeline(), DataCatalog(datasets))
        record = result["factory_receipt"].load()
    except Exception as error:
        record = {
            "status": "FAILED",
            "specification": config["specification"],
            "gate": run.stage,
            "error_type": type(error).__name__,
            "reason": str(error) if isinstance(error, FactoryGateError) else "typed_gate_failure",
            "support": run.support,
            "temporal": run.temporal,
            "quarantine": run.audit.get("quarantine", {}),
            "label_reads": run.label_reads,
            "models_fitted": sum(
                getattr(value.model.adapter, "fit_calls", 0) for value in run.fitted.values()
            ),
            "lineage": run.lineage,
        }
    try:
        import resource

        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        peak = int(rss if sys.platform == "darwin" else rss * 1024)
    except ImportError:
        peak = None
    record["operation"] = {
        "pid": os.getpid(),
        "wall_seconds": time.perf_counter() - started,
        "peak_rss_bytes": peak,
        "canonical_stages_seconds": run.measurements,
        "tracking": "isolated_local_aggregate_receipt",
    }
    tracking = path.parent / "tracking"
    tracking.mkdir()
    data = canonical_bytes(record)
    (tracking / "factory.json").write_bytes(data)
    (path.parent / "receipt.json").write_bytes(data)
    return 0 if record["status"] == "PASSED" else 1


if __name__ == "__main__":
    sys.exit(main())
