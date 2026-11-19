"""Compatibility imports for the canonical calendar contract."""

from sat_dengue_runtime.calendar import (
    add_months,
    history_periods_for_target,
    validate_period,
)

__all__ = [
    "add_months",
    "history_periods_for_target",
    "validate_period",
]
