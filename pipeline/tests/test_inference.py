"""Exercise the retrospective coverage, missing data and artifact integrity contracts."""

from pathlib import Path

import pandas as pd
import pytest
import yaml

from sat_dengue_pipeline.domain.canonical import CLIMATE, PREDICTORS
from sat_dengue_pipeline.factory.configuration import adapter_spec
from sat_dengue_pipeline.inference import (
    CLIMATE_COLUMNS,
    CONFIG_DIR,
    HISTORY_COLUMNS,
    InferenceEngine,
    Manifest,
    Upload,
    history_periods,
)
from sat_dengue_pipeline.models.logistic import LogisticOnsetAdapter, canonical_json
from sat_dengue_pipeline.raw.contract import sha256

CITIES = {"50001": "Villavicencio", "73001": "Ibagué"}
ORIGIN = "2025-10"


def test_retrospective_bundle_scores_zero_and_reports_missing_climate(tmp_path: Path) -> None:
    """Verify a complete municipality, a partial one and successful private artifact loading."""
    configuration = yaml.safe_load(
        (CONFIG_DIR / "retroanalisis/noche/log_conclima.yml").read_bytes()
    )
    model = LogisticOnsetAdapter(adapter_spec(configuration))
    data = pd.DataFrame({name: [0.0, 1.0, 2.0, 3.0] for name in PREDICTORS})
    data["zona_canal_t"] = ["EXITO", "ALERTA", "SEGURIDAD", "EXCESO"]
    model.fit(data, pd.Series([0, 0, 1, 1]))
    (tmp_path / "model.json").write_bytes(canonical_json(model.inference_state()))

    months = history_periods(ORIGIN) | {ORIGIN}
    history = pd.DataFrame(
        [(code, month, 1, 0) for code in CITIES for month in sorted(months)],
        columns=HISTORY_COLUMNS,
    )
    history.to_csv(tmp_path / "history.csv", index=False)
    climate = pd.DataFrame(
        [
            (code, ORIGIN, 31, 31, *([1.0] * len(CLIMATE)), *([31] * len(CLIMATE)))
            for code in CITIES
        ],
        columns=[*HISTORY_COLUMNS[:2], *CLIMATE_COLUMNS],
    )
    climate.loc[1, CLIMATE[0]] = None
    climate.loc[1, f"{CLIMATE[0]}_valid_days"] = 30
    climate.to_csv(tmp_path / "climate.csv", index=False)
    manifest = Manifest(
        experiment_id="EXP314",
        execution_id="fixture",
        training_available_through="2021-01",
        source_release_sha256="a" * 64,
        model_sha256=sha256(tmp_path / "model.json"),
        history_sha256=sha256(tmp_path / "history.csv"),
        climate_sha256=sha256(tmp_path / "climate.csv"),
        periods=[ORIGIN],
    )
    path = tmp_path / "manifest.json"
    path.write_text(manifest.model_dump_json(), encoding="utf-8")
    digest = sha256(path)
    engine = InferenceEngine(tmp_path, digest, CITIES)
    assert engine.coverage == {ORIGIN: {"50001"}}
    rows = engine.predict(
        Upload(
            period=ORIGIN,
            rows=[
                {"code": "50001", "dengue": 0, "grave": None},
                {"code": "73001", "dengue": 0, "grave": 0},
            ],
        )
    )
    assert rows[0]["code"] == "50001" and rows[0]["cases"] == 0
    assert rows[0]["probability"] is not None
    assert rows[1]["reason"] == "missing_climate" and rows[1]["probability"] is None
    (tmp_path / "climate.csv").write_text("alterado", encoding="utf-8")
    with pytest.raises(ValueError, match="huella"):
        InferenceEngine(tmp_path, digest, CITIES)
