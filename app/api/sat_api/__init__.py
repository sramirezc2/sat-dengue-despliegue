"""Servicio desplegable del SAT Dengue para Tolima y Meta."""

from .configuracion import Configuracion, obtener_configuracion
from .main import crear_app

__all__ = ["Configuracion", "obtener_configuracion", "crear_app"]
