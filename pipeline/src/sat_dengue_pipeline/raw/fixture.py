"""Generador explícito de cinco fuentes artificiales; no contiene datos científicos."""

import csv
import json
from datetime import date, timedelta
from pathlib import Path

from sat_dengue_pipeline.acquisition.contracts import ResolvedBundle, ResolvedFile
from sat_dengue_pipeline.experiments.rolling import stable_digest

from .contract import CLIMATE_HEADER, EPI_HEADER, INVENTORY, BuildConfig, sha256
from .producers import CLIMATE_INPUT


def fixture_config() -> BuildConfig:
    """Delimitar dos municipios ficticios y 84 meses; no equivale al perfil aprobado."""
    return BuildConfig(profile="synthetic", start="2018-01", epi_start="2018-01", municipalities=2)


def synthetic_bundle(root: Path) -> tuple[ResolvedBundle, dict]:
    """Generar crudos minúsculos deterministas con ausencias y claves reservadas."""
    root.mkdir(parents=True, exist_ok=True)
    catalog = {
        "estado": "synthetic",
        "conteo": 2,
        "resultado": [
            {
                "CODIGO_MUNICIPIO": "998",
                "CODIGO_DEPARTAMENTO": department,
                "CODIGO_DPTO_MPIO": department + "998",
                "NOMBRE_MUNICIPIO": "FICTICIO " + department,
            }
            for department in ("50", "73")
        ],
    }
    (root / "Divipola-municipios.md").write_text(
        json.dumps(catalog, ensure_ascii=False, sort_keys=True), encoding="utf-8"
    )
    provenance = {
        "authority": "SYNTHETIC TEST ONLY",
        "files": {"Divipola-municipios.md": {"sha256": sha256(root / "Divipola-municipios.md")}},
    }
    (root / "divipola-provenance.json").write_text(json.dumps(provenance), encoding="utf-8")
    for filename, event in (("dengue.csv", "210"), ("dengue_grave.csv", "220")):
        rows = []
        for year in range(2018, 2025):
            for department in ("50", "73"):
                for _ in range(year - 2017):
                    rows.append(
                        {
                            "CONSECUTIVE": "REPEATED",
                            "COD_EVE": event,
                            "COD_DPTO_R": department,
                            "COD_MUN_R": "998",
                            "INI_SIN": f"{year}-06-15",
                            "FEC_NOT": f"{year}-07-01",
                            "COD_DPTO_N": "11",
                            "COD_MUN_N": "001",
                        }
                    )
        rows.extend(
            [
                {
                    "COD_EVE": event,
                    "COD_DPTO_R": "50",
                    "COD_MUN_R": "998",
                    "INI_SIN": "2025-01-01",
                    "FEC_NOT": "2024-01-01",
                },
                {
                    "COD_EVE": event,
                    "COD_DPTO_R": "50",
                    "COD_MUN_R": "998",
                    "INI_SIN": "",
                    "FEC_NOT": "2024-01-01",
                },
                {"COD_EVE": event, "COD_DPTO_R": "99", "COD_MUN_R": "999", "INI_SIN": "2024-01-01"},
            ]
        )
        with (root / filename).open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=EPI_HEADER, restval="")
            writer.writeheader()
            writer.writerows(rows)
    with (root / "google_earth_engine.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=CLIMATE_HEADER)
        writer.writeheader()
        for department, days in (("50", 31), ("73", 30)):
            for offset in range(days):
                day = date(2024, 1, 1) + timedelta(days=offset)
                row = {
                    "date": day.isoformat(),
                    "year": str(day.year),
                    "month": str(day.month),
                    "day_of_year": str(day.timetuple().tm_yday),
                    "dpto_ccdgo": department,
                    "dpto_cnmbr": "FICTICIO",
                    "mpio_ccdgo": "998",
                    "mpio_cdpmp": department + "998",
                    "mpio_cnmbr": "FICTICIO",
                }
                row.update({name: str(0.1 * (i + 1)) for i, name in enumerate(CLIMATE_INPUT)})
                writer.writerow(row)
        writer.writerow(
            {name: "" for name in CLIMATE_HEADER}
            | {
                "date": "2025-01-01",
                "mpio_cdpmp": "50998",
                "rain_mm_day": "MUST NEVER NORMALIZE",
            }
        )
    return fixture_inventory(root)


def fixture_inventory(root: Path) -> tuple[ResolvedBundle, dict]:
    """Crear aprobación SOLO artificial para pruebas que alteran sus propios fixtures."""
    files = tuple(
        ResolvedFile(
            key, root / value[0], (root / value[0]).stat().st_size, sha256(root / value[0])
        )
        for key, value in INVENTORY.items()
    )
    inventory = {f.logical_name: (f.path.name, f.size_bytes, f.sha256) for f in files}
    bundle = ResolvedBundle(
        "synthetic-raw-v1",
        stable_digest(inventory),
        "2018-01-01",
        "2025-01-01",
        files,
        "raw_sources",
    )
    return bundle, inventory
