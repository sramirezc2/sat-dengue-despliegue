"""Cobertura estructural de productores; no concede admisión científica."""

from typing import Protocol


class SourceCoverage(Protocol):
    """Campos consumidos por normalización y ensamblado, sin política de aprendizaje."""

    start: str
    end: str
    epi_start: str
    municipalities: int

    @property
    def periods(self) -> list[str]:
        """Calendario mensual declarado por el consumidor."""
        ...
