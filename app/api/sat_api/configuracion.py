"""Configuracion del servicio, resuelta una sola vez desde el entorno.

Las variables se documentan en `.env.example`.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

PREFIJO = "SATD_"


class ErrorDeConfiguracion(ValueError):
    """Una variable de entorno tiene un valor que el servicio no puede usar."""


def _texto(nombre: str, por_defecto: str) -> str:
    return os.getenv(PREFIJO + nombre, por_defecto).strip()


def _booleano(nombre: str, por_defecto: str) -> bool:
    return _texto(nombre, por_defecto).lower() in {"1", "true", "si", "yes", "on"}


def _entero_positivo(nombre: str, por_defecto: str) -> int:
    crudo = _texto(nombre, por_defecto)
    try:
        valor = int(crudo)
    except ValueError as error:
        raise ErrorDeConfiguracion(f"{PREFIJO}{nombre} debe ser un entero") from error
    if valor <= 0:
        raise ErrorDeConfiguracion(f"{PREFIJO}{nombre} debe ser mayor que cero")
    return valor


def _lista(nombre: str, por_defecto: str) -> tuple[str, ...]:
    crudo = _texto(nombre, por_defecto)
    elementos = tuple(parte.strip() for parte in crudo.split(",") if parte.strip())
    return elementos


def _origenes(nombre: str, por_defecto: str) -> tuple[str, ...]:
    valores = _lista(nombre, por_defecto)
    if "*" in valores:
        raise ErrorDeConfiguracion(
            f"{PREFIJO}{nombre} no admite comodin: declare los origenes de forma explicita"
        )
    return valores


def _departamentos(nombre: str, por_defecto: str) -> tuple[str, ...]:
    valores = _lista(nombre, por_defecto)
    if not valores:
        raise ErrorDeConfiguracion(f"{PREFIJO}{nombre} no puede quedar vacio")
    for codigo in valores:
        if len(codigo) != 2 or not codigo.isdigit():
            raise ErrorDeConfiguracion(
                f"{PREFIJO}{nombre} admite solo codigos DANE de dos digitos, recibido {codigo!r}"
            )
    return valores


@dataclass(frozen=True, slots=True)
class Configuracion:
    """Valores de operacion del servicio."""

    nombre_servicio: str
    entorno: str
    nivel_log: str
    directorio_resultados: Path
    departamentos: tuple[str, ...]
    origenes_cors: tuple[str, ...]
    bucket_s3: str
    prefijo_s3: str
    sincronizar_al_arrancar: bool
    segundos_espera_s3: int
    exponer_docs: bool
    segundos_cache: int

    @property
    def usa_almacenamiento_remoto(self) -> bool:
        """Hay un bucket declarado del cual recuperar resultados."""
        return bool(self.bucket_s3)


@lru_cache
def obtener_configuracion() -> Configuracion:
    """Resolver la configuracion del proceso una sola vez."""
    return Configuracion(
        nombre_servicio=_texto("NOMBRE_SERVICIO", "sat-dengue-api"),
        entorno=_texto("ENTORNO", "local"),
        nivel_log=_texto("NIVEL_LOG", "info").lower(),
        directorio_resultados=Path(_texto("DIRECTORIO_RESULTADOS", "datos/resultados")).resolve(),
        departamentos=_departamentos("DEPARTAMENTOS", "50,73"),
        origenes_cors=_origenes("ORIGENES_CORS", "http://localhost:3000,http://localhost:5173"),
        bucket_s3=_texto("BUCKET_S3", ""),
        prefijo_s3=_texto("PREFIJO_S3", "resultados/"),
        sincronizar_al_arrancar=_booleano("SINCRONIZAR_AL_ARRANCAR", "true"),
        segundos_espera_s3=_entero_positivo("ESPERA_S3_SEGUNDOS", "20"),
        exponer_docs=_booleano("EXPONER_DOCS", "true"),
        segundos_cache=_entero_positivo("CACHE_SEGUNDOS", "300"),
    )
