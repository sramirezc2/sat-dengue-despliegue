"""Recuperacion de resultados desde S3.

El disco local es una cache: la fuente durable es el bucket. Sin bucket
declarado el servicio usa solo lo que haya en el directorio.
"""

from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path
from typing import Protocol

from .configuracion import Configuracion
from .contrato.loader import FixtureValidationError, load_dashboard_fixture

registro = logging.getLogger(__name__)


class ErrorDeSincronizacion(RuntimeError):
    """No se pudo recuperar los resultados del almacenamiento durable."""


class ClienteDeDescarga(Protocol):
    """Capacidad minima requerida del cliente remoto."""

    def download_file(self, bucket: str, clave: str, destino: str) -> None:
        """Descargar un objeto remoto en una ruta local."""


def _descargar_resultado(
    cliente: ClienteDeDescarga,
    bucket: str,
    clave: str,
    archivo: Path,
    tamano: int,
) -> None:
    """Descargar, validar y publicar un resultado mediante reemplazo atomico.

    Args:
        cliente: Cliente S3 compatible con ``download_file``.
        bucket: Nombre del bucket de origen.
        clave: Clave del objeto remoto.
        archivo: Ruta final del resultado publicado.
        tamano: Tamano remoto declarado en bytes.

    Raises:
        ErrorDeSincronizacion: Si la descarga queda incompleta o el JSON no
            satisface el contrato de resultados.
    """
    descriptor, nombre_temporal = tempfile.mkstemp(
        dir=archivo.parent,
        prefix=f".{archivo.name}.",
        suffix=".tmp",
    )
    os.close(descriptor)
    temporal = Path(nombre_temporal)
    try:
        cliente.download_file(bucket, clave, str(temporal))
        recibido = temporal.stat().st_size
        if recibido != tamano:
            raise ErrorDeSincronizacion(
                f"La descarga de {clave} quedo incompleta: {recibido} de {tamano} bytes"
            )
        try:
            load_dashboard_fixture(temporal)
        except FixtureValidationError:
            raise ErrorDeSincronizacion(
                f"El resultado remoto {clave} no cumple el contrato publicado"
            ) from None
        os.replace(temporal, archivo)
    finally:
        temporal.unlink(missing_ok=True)


def _cliente_s3(configuracion: Configuracion):
    try:
        import boto3
        from botocore.config import Config
    except ImportError as error:  # pragma: no cover - depende del entorno
        raise ErrorDeSincronizacion(
            "Hay un bucket declarado pero boto3 no esta instalado en la imagen"
        ) from error

    espera = configuracion.segundos_espera_s3
    return boto3.client(
        "s3",
        config=Config(
            connect_timeout=espera,
            read_timeout=espera,
            retries={"max_attempts": 2, "mode": "standard"},
        ),
    )


def sincronizar_desde_s3(configuracion: Configuracion) -> int:
    """Descargar al directorio local los resultados publicados en el bucket.

    Descarga todos los objetos `.json` bajo el prefijo configurado. Cada objeto
    se escribe y valida en un temporal antes de reemplazar atomicamente el
    resultado visible.

    Returns:
        Cuantos archivos de resultado quedaron en el directorio.

    Raises:
        ErrorDeSincronizacion: si la descarga falla.
    """
    destino = configuracion.directorio_resultados
    destino.mkdir(parents=True, exist_ok=True)

    if not configuracion.usa_almacenamiento_remoto:
        registro.info("Sin bucket declarado, se usa solo el directorio local %s", destino)
        return len(list(destino.glob("*.json")))

    origen = f"s3://{configuracion.bucket_s3}/{configuracion.prefijo_s3}"
    registro.info("Sincronizando resultados desde %s", origen)

    descargados = 0
    try:
        cliente = _cliente_s3(configuracion)
        paginador = cliente.get_paginator("list_objects_v2")
        for pagina in paginador.paginate(
            Bucket=configuracion.bucket_s3, Prefix=configuracion.prefijo_s3
        ):
            for objeto in pagina.get("Contents", ()):
                clave = objeto["Key"]
                if not clave.endswith(".json"):
                    continue
                archivo = destino / Path(clave).name
                _descargar_resultado(
                    cliente,
                    configuracion.bucket_s3,
                    clave,
                    archivo,
                    objeto["Size"],
                )
                descargados += 1
    except ErrorDeSincronizacion as error:
        # Solo nuestros mensajes de contrato/tamaño; sin cadenas del validador.
        raise ErrorDeSincronizacion(str(error)) from None
    except Exception:  # boto3 puede incluir cabeceras/credenciales en el texto
        raise ErrorDeSincronizacion("La sincronizacion remota fallo") from None

    archivos = list(destino.glob("*.json"))
    registro.info(
        "Sincronizacion completa: %d descargado(s), %d disponible(s)", descargados, len(archivos)
    )
    return len(archivos)


def asegurar_resultados(configuracion: Configuracion) -> int:
    """Garantizar que haya resultados en disco antes de atender trafico.

    No levanta excepcion cuando la sincronizacion falla pero ya hay resultados
    locales: es preferible servir la ultima copia conocida a no arrancar.
    """
    destino: Path = configuracion.directorio_resultados
    locales_antes = len(list(destino.glob("*.json"))) if destino.is_dir() else 0

    if not configuracion.sincronizar_al_arrancar:
        registro.info("Sincronizacion al arrancar desactivada por configuracion")
        return locales_antes

    try:
        return sincronizar_desde_s3(configuracion)
    except ErrorDeSincronizacion as error:
        if locales_antes:
            registro.warning(
                "No se pudo sincronizar (%s). Se continua con %d resultado(s) locales",
                error,
                locales_antes,
            )
            return locales_antes
        raise
