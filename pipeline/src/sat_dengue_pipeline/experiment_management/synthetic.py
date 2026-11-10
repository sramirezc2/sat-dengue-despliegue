"""Cinco fuentes artificiales completas; datos efímeros para aceptación técnica."""

import csv
from dataclasses import replace
from pathlib import Path

import pandas as pd

from sat_dengue_pipeline.raw.contract import CLIMATE_HEADER, EPI_HEADER, BuildConfig
from sat_dengue_pipeline.raw.fixture import fixture_inventory, synthetic_bundle
from sat_dengue_pipeline.raw.producers import CLIMATE_INPUT


def acceptance_bundle(root: Path) -> tuple:
    """Generar dos municipios ficticios, historia H5, clima completo y centinelas 2025."""
    synthetic_bundle(root)
    config = BuildConfig(profile="synthetic", municipalities=2)
    for name, event in (("dengue.csv", "210"), ("dengue_grave.csv", "220")):
        with (root / name).open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=EPI_HEADER, restval="")
            writer.writeheader()
            for period in config.periods:
                year, month = map(int, period.split("-"))
                for department, peak in (("50", 6), ("73", 10)):
                    count = year - 2010 if month == peak else 1
                    for _ in range(count):
                        writer.writerow(
                            {
                                "COD_EVE": event,
                                "COD_DPTO_R": department,
                                "COD_MUN_R": "998",
                                "INI_SIN": period + "-15",
                            }
                        )
            writer.writerow(
                {"COD_EVE": event, "COD_DPTO_R": "50", "COD_MUN_R": "998", "INI_SIN": "2025-01-01"}
            )
    with (root / "google_earth_engine.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=CLIMATE_HEADER, restval="")
        writer.writeheader()
        for day in pd.date_range("2011-06-01", "2024-12-31"):
            for department in ("50", "73"):
                writer.writerow(
                    {
                        "date": day.strftime("%Y-%m-%d"),
                        "year": day.year,
                        "month": day.month,
                        "day_of_year": day.dayofyear,
                        "dpto_ccdgo": department,
                        "dpto_cnmbr": "FICTICIO",
                        "mpio_ccdgo": "998",
                        "mpio_cdpmp": department + "998",
                        "mpio_cnmbr": "FICTICIO",
                        **{name: (i + 1) * day.month / 10 for i, name in enumerate(CLIMATE_INPUT)},
                    }
                )
        writer.writerow(
            {"date": "2025-01-01", "mpio_cdpmp": "50998", "rain_mm_day": "MUST NEVER NORMALIZE"}
        )
    bundle, inventory = fixture_inventory(root)
    bundle = replace(bundle, release_id="t17-acceptance-raw-v1", coverage_start="2011-06-01")
    return bundle, inventory, config
