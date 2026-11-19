"""Compatibility imports for the canonical endemic channel contract."""

from sat_dengue_runtime.endemic_channel import (
    CHANNEL,
    classify_endemic_zone,
    compute_current_endemic_channel,
    history_periods_for_target,
    percentile_type7,
)

__all__ = [
    "CHANNEL",
    "classify_endemic_zone",
    "compute_current_endemic_channel",
    "history_periods_for_target",
    "percentile_type7",
]
