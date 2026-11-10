"""Familias dobles: ninguna implementación científica ni dependencia de framework."""

import json

import pandas as pd

from sat_dengue_pipeline.models.adapters import AdapterSpec, ModelRegistry

from .experiment_fixture import DeterministicDouble


class SignalAdapter(DeterministicDouble):
    """Adaptador de prueba que consume configuración y semilla explícitas."""

    def __init__(self, spec: AdapterSpec) -> None:
        """Crear estado sin ajustar, con identidad inmutable.

        Args:
            spec: Contrato de familia de prueba.
        """
        super().__init__()
        self.spec = spec

    def predict_positive(self, X: pd.DataFrame) -> pd.Series:
        """Devolver probabilidad artificial reproducible, sin recibir y."""
        scale = float(json.loads(self.spec.config_json).get("scale", 1.0))
        return (super().predict_positive(X) * scale + (self.spec.seed % 11) / 1000).clip(0, 1)


class ConstantAdapter(SignalAdapter):
    """Segunda familia artificial para comprobar independencia del arnés."""

    def predict_positive(self, X: pd.DataFrame) -> pd.Series:
        """Emitir solo la constante ajustada en entrenamiento."""
        assert self.fitted
        return pd.Series(self.mean, index=X.index, dtype=float)


def make_registry() -> ModelRegistry:
    """Registrar únicamente dos dobles de prueba explícitos.

    Returns:
        Registro independiente, sin estimadores reales.
    """
    registry = ModelRegistry()
    registry.register("signal_double", "1", SignalAdapter)
    registry.register("constant_double", "1", ConstantAdapter)
    return registry
