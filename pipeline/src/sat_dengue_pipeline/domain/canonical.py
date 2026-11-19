"""Import the shared canonical predictor contract for Kedro callers."""

from sat_dengue_runtime.canonical import (
    CHANNEL,
    CLIMATE,
    COUNTS,
    KEYS,
    LAGS,
    PREDICTORS,
    ROLE_ORDER,
    add_months,
    build_table,
    compute_current_endemic_channel,
    coverage_report,
    history_periods_for_target,
    percentile_type7,
    predictor_matrix,
    validate_period,
    validate_source,
)

__all__ = [
    "CHANNEL",
    "CLIMATE",
    "COUNTS",
    "KEYS",
    "LAGS",
    "PREDICTORS",
    "ROLE_ORDER",
    "add_months",
    "build_table",
    "compute_current_endemic_channel",
    "coverage_report",
    "history_periods_for_target",
    "percentile_type7",
    "predictor_matrix",
    "validate_period",
    "validate_source",
]
