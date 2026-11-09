"""Familias de modelo implementadas, compartidas por la fábrica y el retroanálisis."""

from sat_dengue_pipeline.models.logistic import LogisticOnsetAdapter
from sat_dengue_pipeline.models.xgboost import XGBoostOnsetAdapter

ADAPTERS = {
    ("xgboost_onset", "v1"): XGBoostOnsetAdapter,
    ("logistic_onset", "v1"): LogisticOnsetAdapter,
}
