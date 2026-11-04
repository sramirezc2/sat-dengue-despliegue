"""Repositorio de resultados indexado sobre un directorio configurable.

Publicar un periodo nuevo es dejar un archivo en el directorio, sin editar
codigo. Convencion de nombre: `resultado_<departamento>_<AAAA-MM>.json`.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Mapping
from pathlib import Path

from .contrato.errors import InvalidPersistedResultError
from .contrato.loader import FixtureValidationError, load_dashboard_fixture
from .contrato.schemas import DashboardResponse

registro = logging.getLogger(__name__)

PATRON_NOMBRE = re.compile(r"^resultado_(?P<departamento>\d{2})_(?P<periodo>\d{4}-\d{2})\.json$")

ClaveResultado = tuple[str, str]


def construir_indice(directorio: Path) -> dict[ClaveResultado, Path]:
    """Mapear cada archivo con nombre valido a su clave departamento-periodo.

    Los archivos que no siguen la convencion se ignoran y se registran, para
    que un archivo suelto en el volumen nunca tumbe el arranque.
    """
    indice: dict[ClaveResultado, Path] = {}
    if not directorio.is_dir():
        registro.warning("El directorio de resultados no existe todavia: %s", directorio)
        return indice

    for ruta in sorted(directorio.glob("*.json")):
        coincidencia = PATRON_NOMBRE.match(ruta.name)
        if coincidencia is None:
            registro.warning("Archivo ignorado, no sigue la convencion de nombre: %s", ruta.name)
            continue
        clave = (coincidencia["departamento"], coincidencia["periodo"])
        indice[clave] = ruta
    return indice


class RepositorioDirectorio:
    """Leer y validar respuestas del tablero desde un directorio."""

    def __init__(self, directorio: Path, departamentos: tuple[str, ...]) -> None:
        self._directorio = directorio
        self._departamentos = frozenset(departamentos)
        self._indice: Mapping[ClaveResultado, Path] = {}
        self.recargar()

    def recargar(self) -> int:
        """Releer el directorio y devolver cuantos resultados quedaron indexados."""
        completo = construir_indice(self._directorio)
        self._indice = {
            clave: ruta for clave, ruta in completo.items() if clave[0] in self._departamentos
        }
        descartados = len(completo) - len(self._indice)
        if descartados:
            registro.warning(
                "%d resultado(s) fuera de los departamentos servidos quedaron sin indexar",
                descartados,
            )
        registro.info("Resultados indexados: %d", len(self._indice))
        return len(self._indice)

    @property
    def periodos_disponibles(self) -> dict[str, list[str]]:
        """Periodos indexados por departamento, para diagnostico y para la interfaz."""
        disponibles: dict[str, list[str]] = {}
        for departamento, periodo in sorted(self._indice):
            disponibles.setdefault(departamento, []).append(periodo)
        return disponibles

    def get(self, department_code: str, period: str) -> DashboardResponse | None:
        """Devolver el resultado exacto de una consulta, o None si no existe.

        Raises:
            InvalidPersistedResultError: si el archivo indexado no se puede leer,
                viola el esquema o contradice su propia clave.
        """
        ruta = self._indice.get((department_code, period))
        if ruta is None:
            return None

        try:
            respuesta = load_dashboard_fixture(ruta)
        except FixtureValidationError as error:
            raise InvalidPersistedResultError(
                f"El resultado persistido es invalido: {ruta.name}"
            ) from error

        if (
            respuesta.department.department_code != department_code
            or respuesta.department.requested_period != period
            or respuesta.metadata.reference_period != period
        ):
            raise InvalidPersistedResultError(
                f"El contenido de {ruta.name} no corresponde a su clave de indice"
            )
        return respuesta
