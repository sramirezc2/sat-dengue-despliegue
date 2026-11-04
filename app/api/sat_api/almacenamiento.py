"""Recuperacion de resultados desde S3.

El disco local es una cache: la fuente durable es el bucket. Sin bucket
declarado el servicio usa solo lo que haya en el directorio.
"""

from __future__ import annotations

import logging
from pathlib import Path

from .configuracion import Configuracion

registro = logging.getLogger(__name__)


class ErrorDeSincronizacion(RuntimeError):
    """No se pudo recuperar los resultados del almacenamiento durable."""


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

    Descarga solo objetos `.json` bajo el prefijo configurado y omite los que
    ya estan en disco con el mismo tamano, para que reiniciar la instancia no
    vuelva a bajar todo.

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

    cliente = _cliente_s3(configuracion)
    origen = f"s3://{configuracion.bucket_s3}/{configuracion.prefijo_s3}"
    registro.info("Sincronizando resultados desde %s", origen)

    descargados = 0
    try:
        paginador = cliente.get_paginator("list_objects_v2")
        for pagina in paginador.paginate(
            Bucket=configuracion.bucket_s3, Prefix=configuracion.prefijo_s3
        ):
            for objeto in pagina.get("Contents", ()):
                clave = objeto["Key"]
                if not clave.endswith(".json"):
                    continue
                archivo = destino / Path(clave).name
                if archivo.is_file() and archivo.stat().st_size == objeto["Size"]:
                    continue
                cliente.download_file(configuracion.bucket_s3, clave, str(archivo))
                descargados += 1
    except Exception as error:  # boto3 expone muchas excepciones distintas
        raise ErrorDeSincronizacion(f"La sincronizacion desde {origen} fallo: {error}") from error

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
