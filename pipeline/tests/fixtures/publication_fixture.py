"""Entradas de publicación artificiales, sin V2, crudos o publicaciones reales."""

import csv
import json
from pathlib import Path

GENERATED = "2024-07-01T12:00:00+00:00"
PROCEDURE = "synthetic-publication-v1"


def publication_rows() -> tuple[list[dict], list[dict], list[dict], dict]:
    """Crear los 76 municipios artificiales exigidos por los contratos del producto."""
    panel, predictions, comparison = [], [], []
    for department, count in (("50", 29), ("73", 47)):
        for i in range(count):
            code = f"{department}{i:03d}"
            for month in ("2024-01", "2024-02", "2024-03"):
                if i == 2 and month == "2024-02":
                    continue
                panel.append(
                    {
                        "municipality_code": code,
                        "year_month": month,
                        "municipality_name": "SAN JUAN DE LA SIERRA"
                        if i == 0
                        else "FICTICIO DEL RÍO",
                        "dengue_notifications_count": "20",
                        "total_notifications_count": "999",
                        "p25_canal_t": "5",
                        "p50_canal_t": "10",
                        "p75_canal_t": "15",
                        "zona_canal_t": "EXCESO",
                        "p75_t1": "15",
                        "p75_t2": "15",
                        "y_t1": "0",
                        "y_status_t1": "insufficient_history"
                        if i == 3
                        else ("target_outside_panel" if i == 4 else "other"),
                        "y_status_t2": "insufficient_history" if i == 3 else "other",
                    }
                )
            if i < 2:
                for candidate in ("lightgbm", "xgboost"):
                    for horizon in ("1", "2"):
                        predictions.append(
                            {
                                "candidate": candidate,
                                "municipality_code": code,
                                "year_month": "2024-02",
                                "horizon": horizon,
                                "prediction_probability": "0.8" if i else "0.1",
                                "prediction_label": str(i),
                                "y_true": str(i),
                            }
                        )
    # Un periodo con un solo horizonte se omite, sin eliminarlo de la referencia evaluada.
    predictions.append({**predictions[0], "year_month": "2024-03"})
    for horizon in ("1", "2"):
        for candidate, detected, false in (
            ("persistence", 0, 10),
            ("gam", 2, 10),
            ("xgboost", 4, 8),
            ("lightgbm", 6, 6),
        ):
            comparison.append(
                {
                    "candidate": candidate,
                    "horizon": horizon,
                    "result": "reference" if candidate == "persistence" else "does_not_meet",
                    "detected_onsets": str(detected),
                    "real_onsets": "10",
                    "false_alerts": str(false),
                    "emitted_alerts": "12",
                    "false_alarm_ratio": "0.5",
                    "onset_sensitivity": str(detected / 10),
                    "auroc": "0.7",
                    "average_precision": "0.6",
                    "brier": "0.2",
                }
            )
    retro = {
        "method": "expanding_window",
        "period_start": "2020-01",
        "period_end": "2023-12",
        "provenance": "experimental_harness",
        "seeds_checked": [42],
        "rows": [
            {
                "horizon": "T1",
                "year": None,
                "candidate": "lightgbm",
                "label": "LightGBM",
                "role": "PUBLISHED",
                "onsets_detected": 2,
                "actual_onsets": 4,
                "alerts_emitted": 5,
                "false_alerts": 1,
                "false_alerts_onset": 3,
            }
        ],
        "curve": [],
    }
    return panel, predictions, comparison, retro


def write_inputs(root: Path, *, reverse: bool = False) -> dict[str, Path]:
    """Materializar únicamente entradas artificiales en un directorio indicado."""
    root.mkdir(parents=True, exist_ok=True)
    panel, predictions, comparison, retro = publication_rows()
    paths = {}
    for name, rows in (
        ("panel", panel),
        ("predicciones", predictions),
        ("comparacion", comparison),
    ):
        path = root / f"{name}.csv"
        with path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows[::-1] if reverse else rows)
        paths[name] = path
    paths["retroanalisis"] = root / "retro.json"
    paths["retroanalisis"].write_text(json.dumps(retro), encoding="utf-8")
    return paths
