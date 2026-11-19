"""Kedro-side imports for the shared retrospective runtime."""

from pathlib import Path

from sat_dengue_runtime.inference import (
    CLIMATE_COLUMNS,
    HISTORY_COLUMNS,
    InferenceEngine,
    Manifest,
    Upload,
    coverage,
    history_periods,
)
from sat_dengue_runtime.inference import (
    catalogue as read_catalogue,
)

__all__ = [
    "CLIMATE_COLUMNS",
    "HISTORY_COLUMNS",
    "InferenceEngine",
    "Manifest",
    "Upload",
    "coverage",
    "history_periods",
    "CONFIG_DIR",
    "catalogue",
]

CONFIG_DIR = Path(__file__).resolve().parents[2] / "conf"


def catalogue(path: Path = CONFIG_DIR / "geografia/divipola_coordenadas.csv") -> dict[str, str]:
    """Read the versioned Kedro catalogue by default."""
    return read_catalogue(path)
