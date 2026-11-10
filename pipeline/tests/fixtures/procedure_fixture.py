"""Cinco ventanas artificiales, separadas por disponibilidad y sin datos reales."""

from sat_dengue_pipeline.domain.calendar import add_months
from sat_dengue_pipeline.experiments.decisions import ThresholdPolicy
from sat_dengue_pipeline.experiments.roles import RoleBatch, RoleWindow, TemporalPlan, split_roles

from .experiment_fixture import make_experiment


def make_procedure(horizon: int = 1) -> tuple[TemporalPlan, dict[str, RoleBatch]]:
    """Crear historia completa artificial y roles con huecos de embargo implícitos.

    Args:
        horizon: Uno o dos meses calendario.

    Returns:
        Plan y batches; todas las etiquetas siguen separadas y diferidas.
    """
    plan = TemporalPlan(
        horizon,
        (
            RoleWindow("train", add_months("2018-01", horizon), "2018-12"),
            RoleWindow("calibration_fit", "2019-04", "2019-09"),
            RoleWindow("calibration_selection", "2020-01", "2020-03"),
            RoleWindow("threshold_selection", "2020-06", "2020-09"),
            RoleWindow("evaluation", "2021-01", "2021-04"),
        ),
    )
    return plan, split_roles(make_experiment(horizon, include_missing=False), plan)


def threshold_policy() -> ThresholdPolicy:
    """Declarar un ejemplo de ingeniería, sin aprobación de utilidad científica.

    Returns:
        Grilla fija por décimas y cota FAR 1 solo para tests artificiales.
    """
    return ThresholdPolicy(tuple(i / 10 for i in range(11)), max_false_alarm_ratio=1.0)
