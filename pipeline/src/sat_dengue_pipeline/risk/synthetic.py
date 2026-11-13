"""Cinco fuentes pequeñas artificiales para aceptación diferida, nunca datos reales."""

import csv
import json
from dataclasses import replace
from datetime import date, timedelta
from pathlib import Path

from sat_dengue_pipeline.raw.contract import CLIMATE_HEADER, EPI_HEADER
from sat_dengue_pipeline.raw.fixture import fixture_inventory
from sat_dengue_pipeline.raw.producers import CLIMATE_INPUT


def write_sources(root: Path) -> tuple:
    """Crear 76 municipios ficticios con clima solo en los orígenes necesarios."""
    root.mkdir(parents=True, exist_ok=False)
    codes = [
        f"{d}{i:03d}" for d, count in (("50", 29), ("73", 47)) for i in range(900, 900 + count)
    ]
    catalog = {
        "estado": "SYNTHETIC",
        "conteo": 76,
        "resultado": [
            {
                "CODIGO_DPTO_MPIO": c,
                "CODIGO_DEPARTAMENTO": c[:2],
                "CODIGO_MUNICIPIO": c[2:],
                "NOMBRE_MUNICIPIO": f"FICTICIO {c}",
            }
            for c in codes
        ],
    }
    from .configuration import sha

    catalog_bytes = json.dumps(catalog, sort_keys=True).encode()
    (root / "Divipola-municipios.md").write_bytes(catalog_bytes)
    (root / "divipola-provenance.json").write_text(
        json.dumps(
            {
                "authority": "SYNTHETIC TEST ONLY",
                "files": {"Divipola-municipios.md": {"sha256": sha(catalog_bytes)}},
            }
        )
    )
    for filename, event in (("dengue.csv", "210"), ("dengue_grave.csv", "220")):
        with (root / filename).open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, EPI_HEADER, restval="")
            writer.writeheader()
            # En septiembre hay inicios artificiales para las primeras 12 filas;
            # todos los orígenes publicados tienen cero casos y son elegibles.
            for c in codes[:12] if event == "210" else []:
                writer.writerow(
                    {
                        "COD_EVE": event,
                        "COD_DPTO_R": c[:2],
                        "COD_MUN_R": c[2:],
                        "INI_SIN": "2024-09-15",
                    }
                )
            writer.writerow(
                {
                    "COD_EVE": event,
                    "COD_DPTO_R": codes[0][:2],
                    "COD_MUN_R": codes[0][2:],
                    "INI_SIN": "2007-01-01",
                }
            )
    months = ["2024-07", "2024-11", "2024-12", *[f"2025-{m:02d}" for m in range(1, 11)]]
    with (root / "google_earth_engine.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, CLIMATE_HEADER, restval="")
        writer.writeheader()
        for month in months:
            first = date.fromisoformat(month + "-01")
            day = first
            while day.month == first.month:
                for index, c in enumerate(codes):
                    row = {
                        "date": day.isoformat(),
                        "year": str(day.year),
                        "month": str(day.month),
                        "day_of_year": str(day.timetuple().tm_yday),
                        "dpto_ccdgo": c[:2],
                        "mpio_ccdgo": c[2:],
                        "mpio_cdpmp": c,
                    }
                    row.update({n: str(index + j + 1) for j, n in enumerate(CLIMATE_INPUT)})
                    writer.writerow(row)
                day += timedelta(days=1)
    bundle, inventory = fixture_inventory(root)
    return replace(bundle, coverage_start="2007-01-01", coverage_end="2025-10-31"), inventory
