"""Load a private retrospective bundle and rank prepared municipal T+2 inputs."""

import csv
import hashlib
import io
import math
from collections.abc import Iterable
from pathlib import Path
from typing import Literal

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, StrictInt

from .calendar import add_months, history_periods_for_target
from .canonical import (
    CLIMATE,
    COUNTS,
    KEYS,
    LAGS,
    PREDICTORS,
    build_table,
)
from .logistic import load_inference_state, predict_exported

PERIOD = r"^[0-9]{4}-(0[1-9]|1[0-2])$"
CODE = r"^(50|73)[0-9]{3}$"
SHA = r"^[0-9a-f]{64}$"
CLIMATE_COLUMNS = [
    "expected_days_in_month",
    "climate_days_observed",
    *CLIMATE,
    *(f"{name}_valid_days" for name in CLIMATE),
]
HISTORY_COLUMNS = [*KEYS, *COUNTS[:2]]


class Manifest(BaseModel):
    """Pin the fitted model, source release and both aggregated inputs."""

    model_config = ConfigDict(extra="forbid")
    schema_version: Literal[1] = 1
    history_mode: Literal["retrospective"] = "retrospective"
    experiment_id: str = Field(pattern=r"^EXP[0-9]+$")
    execution_id: str = Field(pattern=r"^[a-zA-Z0-9_-]{1,80}$")
    model_sha256: str = Field(pattern=SHA)
    history_sha256: str = Field(pattern=SHA)
    climate_sha256: str = Field(pattern=SHA)
    source_release_sha256: str = Field(pattern=SHA)
    training_available_through: str = Field(pattern=PERIOD)
    periods: list[str] = Field(min_length=1)


class Observation(BaseModel):
    """Accept only bounded municipal counts, with explicit missingness."""

    model_config = ConfigDict(extra="forbid")
    code: str = Field(pattern=CODE)
    dengue: StrictInt | None = Field(ge=0, le=100_000)
    grave: StrictInt | None = Field(ge=0, le=100_000)


class Upload(BaseModel):
    """Aggregates from one user-selected reference month."""

    model_config = ConfigDict(extra="forbid")
    period: str = Field(pattern=PERIOD)
    rows: list[Observation] = Field(min_length=1, max_length=76)
    sample: bool = False


def catalogue(path: Path) -> dict[str, str]:
    """Read the municipal catalogue for the two served departments."""
    with path.open(encoding="utf-8", newline="") as stream:
        return {
            row["cod_mpio"]: row["nom_mpio"]
            for row in csv.DictReader(stream)
            if row["cod_dpto"] in {"50", "73"}
        }


def history_periods(period: str) -> set[str]:
    """Return the historical calendar needed by the seasonal channels and lags."""
    return {
        *(add_months(period, -lag) for lag in LAGS),
        *(
            p
            for horizon in (0, 1, 2)
            for p in history_periods_for_target(add_months(period, horizon))
        ),
    }


def coverage(
    history: pd.DataFrame, climate: pd.DataFrame, training_cutoff: str
) -> dict[str, set[str]]:
    """Find origins with complete climate and exact historical keys per municipality."""
    known = set(history.index)
    result: dict[str, set[str]] = {}
    complete = climate.dropna(subset=CLIMATE)
    needed = {
        period: history_periods(period)
        for period in complete.index.get_level_values("year_month").unique()
        if period > training_cutoff
    }
    for code, period in complete.index:
        if period in needed and all((code, month) in known for month in needed[period]):
            result.setdefault(period, set()).add(code)
    return result


def checked_bytes(path: Path, digest: str, limit: int) -> bytes:
    """Read bounded private data and verify its bytes before parsing."""
    with path.open("rb") as stream:
        data = stream.read(limit + 1)
    if len(data) > limit or hashlib.sha256(data).hexdigest() != digest:
        raise ValueError("El archivo de inferencia no coincide con su huella")
    return data


def _frame(data: bytes, columns: list[str], codes: Iterable[str]) -> pd.DataFrame:
    frame = pd.read_csv(
        io.BytesIO(data), dtype={name: str for name in KEYS}, float_precision="round_trip"
    )
    if list(frame) != columns or frame.empty or not frame[KEYS[0]].isin(codes).all():
        raise ValueError("Columnas o municipios del paquete incompatibles")
    indexed = frame.set_index(KEYS)
    if not indexed.index.is_unique:
        raise ValueError("Claves municipio-mes duplicadas en el paquete")
    return indexed


class InferenceEngine:
    """Score an uploaded month with the exported fit and monthly source aggregates."""

    def __init__(self, directory: Path, digest: str, municipalities: dict[str, str]) -> None:
        """Load and cross-check one private package before exposing availability."""
        self.manifest = Manifest.model_validate_json(
            checked_bytes(directory / "manifest.json", digest, 32 * 1024)
        )
        manifest = self.manifest
        self.state = load_inference_state(directory / "model.json", manifest.model_sha256)
        if self.state.get("adapter", {}).get("predictors") != PREDICTORS:
            raise ValueError("El modelo requiere la matriz climática canónica")
        self.history = _frame(
            checked_bytes(directory / "history.csv", manifest.history_sha256, 4 * 1024 * 1024),
            HISTORY_COLUMNS,
            municipalities,
        )
        self.climate = _frame(
            checked_bytes(directory / "climate.csv", manifest.climate_sha256, 8 * 1024 * 1024),
            [*KEYS, *CLIMATE_COLUMNS],
            municipalities,
        )
        self.coverage = coverage(self.history, self.climate, manifest.training_available_through)
        self.complete_climate = set(self.climate.dropna(subset=CLIMATE).index)
        if manifest.periods != sorted(self.coverage):
            raise ValueError("La cobertura del manifiesto no coincide con los datos")
        self.municipalities = municipalities

    def predict(self, upload: Upload) -> list[dict[str, str | float | int | None]]:
        """Return ordered probabilities and reasons for unavailable municipalities."""
        period = upload.period
        ready = self.coverage[period]
        observations = {row.code: row for row in upload.rows}
        reasons = {}
        rows = []
        for code, row in observations.items():
            grave = row.grave
            if grave is None and (code, period) in self.history.index:
                grave = int(self.history.at[(code, period), COUNTS[1]])
            if row.dengue is None:
                reasons[code] = "missing_dengue"
            elif grave is None:
                reasons[code] = "missing_grave"
            elif (code, period) not in self.complete_climate:
                reasons[code] = "missing_climate"
            elif code not in ready:
                reasons[code] = "missing_history"
            else:
                rows.append((code, period, row.dengue, grave))
                rows.extend(
                    (code, month, *self.history.loc[(code, month)])
                    for month in history_periods(period)
                )
        features = self._features(rows, period) if rows else pd.DataFrame()
        probabilities: dict[str, float] = {}
        if not features.empty:
            eligible = features["zona_canal_t"].ne("EXCESO") & features[PREDICTORS].notna().all(
                axis=1
            )
            if eligible.any():
                probabilities = predict_exported(
                    features.loc[eligible, PREDICTORS], self.state
                ).to_dict()

        result = []
        for code, name in self.municipalities.items():
            row = observations.get(code)
            zone = features.at[code, "zona_canal_t"] if code in features.index else None
            p75 = features.at[code, "p75_h5_t2"] if code in features.index else None
            probability = probabilities.get(code)
            reason = None
            if probability is None:
                if row is None:
                    reason = "missing_upload"
                else:
                    reason = reasons.get(code) or (
                        "excess_at_origin"
                        if pd.notna(zone) and zone == "EXCESO"
                        else "missing_history"
                    )
            result.append(
                {
                    "code": code,
                    "name": name,
                    "cases": row.dengue if row else None,
                    "zone": str(zone) if pd.notna(zone) else None,
                    "p75t2": float(p75) if pd.notna(p75) and math.isfinite(p75) else None,
                    "probability": probability,
                    "reason": reason,
                }
            )
        return sorted(
            result,
            key=lambda row: (
                row["probability"] is None,
                -float(row["probability"] or 0),
                str(row["code"]),
            ),
        )

    def _features(self, rows: list[tuple], period: str) -> pd.DataFrame:
        panel = pd.DataFrame(rows, columns=HISTORY_COLUMNS)
        panel[COUNTS[:2]] = panel[COUNTS[:2]].astype("Float64")
        panel[COUNTS[2]] = panel[COUNTS[0]] + panel[COUNTS[1]]
        panel["department_code"] = panel.municipality_code.str[:2]
        panel["in_epi_coverage"] = True
        panel["epi_count_status"] = (
            panel[COUNTS[2]].gt(0).map({True: "records_present", False: "zero_in_coverage"})
        )
        panel = panel.join(self.climate, on=KEYS)
        table, _ = build_table(panel)
        return table.loc[table.year_month.eq(period)].set_index("municipality_code")
