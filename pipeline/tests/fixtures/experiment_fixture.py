"""Muestra mensual enteramente artificial para contratos de experimentación."""

import pandas as pd

from sat_dengue_pipeline.domain.calendar import add_months
from sat_dengue_pipeline.domain.canonical import PREDICTORS
from sat_dengue_pipeline.experiments.rolling import KEY_COLUMNS, ExperimentData


def make_experiment(horizon: int = 1) -> ExperimentData:
    """Construir dos municipios ficticios 2018–2024, sin usar filas de V2.

    Args:
        horizon: Uno o dos meses calendario.

    Returns:
        Claves/X/y/controles separados, con una ausencia de X y otra de y.
    """
    rows, features, labels = [], [], []
    for code in ("50998", "73998"):
        for i, month in enumerate(
            pd.period_range("2018-01", add_months("2024-12", -horizon), freq="M")
        ):
            origin, target = str(month), str(month + horizon)
            rows.append(
                {
                    "municipality_code": code,
                    "origin_period": origin,
                    "target_period": target,
                    "horizon": horizon,
                    "label_available_period": target,
                }
            )
            feature = {name: float((i % 7) + 1) for name in PREDICTORS}
            feature["month_of_year"] = month.month
            feature["zona_canal_t"] = "SEGURIDAD"
            if code == "50998" and origin == "2018-08":
                feature["rain_mm_month_sum"] = float("nan")
            features.append(feature)
            labels.append(pd.NA if code == "50998" and origin == "2018-06" else int(i % 3 == 0))
    keys = pd.DataFrame(rows, columns=KEY_COLUMNS)
    return ExperimentData(
        keys,
        pd.DataFrame(features, columns=PREDICTORS),
        pd.Series(labels, dtype="Int64", name=f"y_t{horizon}"),
        pd.DataFrame({"eligible_at_t": [True] * len(keys)}),
    )


class DeterministicDouble:
    """Doble sin valor científico: media de y_train más señal artificial acotada."""

    def __init__(self) -> None:
        """Crear un estado independiente sin ajustar."""
        self.fitted = False
        self.mean = 0.0

    def fit(self, X: pd.DataFrame, y: pd.Series) -> None:
        """Guardar solo la media de las etiquetas autorizadas del fold."""
        assert X.index.equals(y.index) and y.notna().all()
        self.mean = float(y.mean())
        self.fitted = True

    def predict_positive(self, X: pd.DataFrame) -> pd.Series:
        """Inferir sin etiqueta usando una señal presente al origen."""
        assert self.fitted
        return (X.month_of_year.astype(float) / 24 + self.mean / 2).clip(0, 1)
