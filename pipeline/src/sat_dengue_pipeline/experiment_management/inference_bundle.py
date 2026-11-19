"""Assemble a private retrospective T+2 bundle from a completed export and local release."""

import argparse
import json
import shutil
from collections import Counter
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from sat_dengue_pipeline.acquisition import ReleaseManifest
from sat_dengue_pipeline.acquisition.raw_manifest import validate_raw_manifest
from sat_dengue_pipeline.domain.canonical import KEYS
from sat_dengue_pipeline.factory.configuration import project_root
from sat_dengue_pipeline.inference import (
    CLIMATE_COLUMNS,
    HISTORY_COLUMNS,
    InferenceEngine,
    Manifest,
    catalogue,
    coverage,
    history_periods,
)
from sat_dengue_pipeline.raw.contract import sha256
from sat_dengue_pipeline.raw.producers import (
    CLIMATE_INPUT,
    _code,
    climate_monthly_aggregation,
    normalize_climate_window,
)
from sat_dengue_pipeline.raw.temporal import parse_date

from .evidence import verify_execution
from .inference_export import validate_export_configuration
from .registry import confined, identifier


def _read_json(path: Path) -> dict:
    return json.loads(path.read_bytes())


def _fit(root: Path, experiment: str, execution: str) -> tuple[dict, Path, ReleaseManifest]:
    relative = f"docs/evidence/experiments/{identifier(experiment)}/{identifier(execution)}"
    receipt = verify_execution(root, f"{relative}/inventory.json")
    if receipt["status"] != "COMPLETED" or receipt["experiment_type"] != "scientific":
        raise ValueError("Se requiere una ejecución real completada")
    evidence = root / relative
    config = _read_json(evidence / "configuration.json")
    validate_export_configuration(config)
    if config.get("population") != {"department_codes": ["50", "73"]}:
        raise ValueError("El modelo debe estar ajustado para Meta y Tolima")
    lineage = _read_json(evidence / "lineage.json")
    validation = _read_json(evidence / "validation.json")
    folder = f"pipeline/data/experiments/{execution}/inference-fit"
    fit = _read_json(confined(root, f"{folder}/fit.json", "pipeline/data"))
    model_path = confined(root, f"{folder}/model.json", "pipeline/data")
    manifest_path = confined(root, config["data"]["manifest"], "pipeline/conf/releases")
    manifest_hash = sha256(manifest_path)
    expected = {
        "experiment_id": experiment,
        "execution_id": execution,
        "horizon": 2,
        "execution_signature": receipt["execution_signature"],
        "configuration_sha256": receipt["configuration_sha256"],
        "protocol_sha256": receipt["protocol_sha256"],
        "model_sha256": lineage["inference_model_sha256"],
        "training_release_sha256": manifest_hash,
        "training_available_through": validation["temporal"]["2"]["support"]["train"]["available"],
        "evaluated_model_sha256": validation["artifact_sha256"]["2"]["model_json"],
    }
    if (
        fit != expected
        or manifest_hash != lineage["dataset_manifest_file_sha256"]
        or model_path.stat().st_size > 128 * 1024
        or sha256(model_path) != fit["model_sha256"]
    ):
        raise ValueError("El ajuste no coincide con el inventario firmado")
    manifest = ReleaseManifest.from_json(manifest_path.read_text(encoding="utf-8"))
    validate_raw_manifest(manifest)
    if manifest.manifest_sha256 != lineage["dataset_manifest_digest"]:
        raise ValueError("El release local no coincide con el registrado")
    return fit, model_path, manifest


def _notifications(
    path: Path, event: str, municipalities: dict[str, str], months: set[str]
) -> Counter[tuple[str, str]]:
    """Apply the canonical event, residence and symptom-date counting rules."""
    columns = ["COD_DPTO_R", "COD_MUN_R", "COD_EVE", "INI_SIN"]
    counts: Counter[tuple[str, str]] = Counter()
    for frame in pd.read_csv(
        path, usecols=columns, dtype=str, keep_default_na=False, chunksize=50_000
    ):
        frame = frame.loc[frame.COD_DPTO_R.str.strip().isin({"50", "73"}), columns]
        for department, municipality, observed, value in frame.itertuples(index=False, name=None):
            code = department.strip() + (_code(municipality, 3) or "")
            if code not in municipalities or observed.strip() != event:
                continue
            onset = parse_date(value)
            if onset is not None and (month := onset.isoformat()[:7]) in months:
                counts[code, month] += 1
    return counts


def _climate(path: Path, municipalities: dict[str, str], origins: set[str]) -> pd.DataFrame:
    columns = [
        "date",
        "year",
        "month",
        "day_of_year",
        "dpto_ccdgo",
        "mpio_ccdgo",
        "mpio_cdpmp",
        *CLIMATE_INPUT,
    ]
    chunks = []
    for frame in pd.read_csv(
        path, usecols=columns, dtype=str, keep_default_na=False, chunksize=50_000
    ):
        selected = frame.mpio_cdpmp.str.strip().isin(municipalities) & frame.date.str[:7].isin(
            origins
        )
        if selected.any():
            chunks.append(frame.loc[selected].copy())
    if not chunks:
        raise ValueError("El release carece de clima para los meses solicitados")
    geo = pd.DataFrame({"municipality_code": list(municipalities)})
    daily, _ = normalize_climate_window(
        pd.concat(chunks, ignore_index=True), geo, start=min(origins), end=max(origins)
    )
    return climate_monthly_aggregation(daily).loc[:, [*KEYS, *CLIMATE_COLUMNS]]


def assemble(root: Path, experiment: str, execution: str) -> dict:
    """Verify local sources and atomically assemble one private serving directory."""
    fit, model, manifest = _fit(root, experiment, execution)
    target = confined(
        root, f"pipeline/data/inference/{execution}/retrospective", "pipeline/data", exists=False
    )
    if target.exists():
        raise FileExistsError("El paquete retrospectivo ya existe")
    municipalities = catalogue(root / "pipeline/conf/geografia/divipola_coordenadas.csv")
    cutoff = fit["training_available_through"]
    start, end = manifest.coverage_start[:7], manifest.coverage_end[:7]
    origins = {
        month
        for month in map(str, pd.period_range(start, end, freq="M"))
        if month > cutoff and min(history_periods(month)) >= start
    }
    months = origins | {month for origin in origins for month in history_periods(origin)}
    if not origins:
        raise ValueError("El release no cubre meses posteriores al ajuste")
    base = f"pipeline/data/01_raw/inbox/{manifest.release_id}/{manifest.manifest_sha256}"
    events = {"dengue_notifications": "210", "severe_dengue_notifications": "220"}
    counts = {}
    climate = pd.DataFrame()
    for file in manifest.files:
        kind = file.logical_name
        if kind not in events and kind != "daily_climate":
            continue
        source = confined(root, f"{base}/{file.relative_path}", "pipeline/data")
        if source.stat().st_size != file.size_bytes or sha256(source) != file.sha256:
            raise ValueError("Los datos locales no coinciden con el release registrado")
        if kind in events:
            counts[kind] = _notifications(source, events[kind], municipalities, months)
        else:
            climate = _climate(source, municipalities, origins)
        if sha256(source) != file.sha256:
            raise ValueError("Un archivo del release cambió durante la lectura")
    # A complete source release provides zero counts for uncovered keys within its declared window.
    history = pd.DataFrame(
        [
            (code, month, *(counts[name][code, month] for name in events))
            for code in sorted(municipalities)
            for month in sorted(months)
        ],
        columns=HISTORY_COLUMNS,
    )
    periods = sorted(coverage(history.set_index(KEYS), climate.set_index(KEYS), cutoff))
    target.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    with TemporaryDirectory(dir=target.parent, prefix=".staging-") as directory:
        stage = Path(directory) / target.name
        stage.mkdir(mode=0o700)
        shutil.copyfile(model, stage / "model.json")
        history.to_csv(stage / "history.csv", index=False)
        climate.to_csv(stage / "climate.csv", index=False)
        release = Manifest(
            experiment_id=experiment,
            execution_id=execution,
            model_sha256=fit["model_sha256"],
            history_sha256=sha256(stage / "history.csv"),
            climate_sha256=sha256(stage / "climate.csv"),
            source_release_sha256=manifest.manifest_sha256,
            training_available_through=cutoff,
            periods=periods,
        )
        (stage / "manifest.json").write_text(release.model_dump_json(), encoding="utf-8")
        digest = sha256(stage / "manifest.json")
        InferenceEngine(stage, digest, municipalities)
        stage.rename(target)
    return {
        "directory": target.relative_to(root).as_posix(),
        "manifest_sha256": digest,
        "periods": periods,
    }


def main() -> None:
    """Prepare a locally mounted inference bundle without retraining the model."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--execution-id", required=True)
    args = parser.parse_args()
    print(json.dumps(assemble(project_root().parent, args.experiment_id, args.execution_id)))


if __name__ == "__main__":
    main()
