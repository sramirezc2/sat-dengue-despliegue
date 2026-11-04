"""Composicion del servicio sobre el contrato read-only de V2.

El contrato se reutiliza sin modificar. Esta capa agrega configuracion por
entorno, recuperacion desde S3, CORS, salud, esquema OpenAPI y una forma de
error uniforme para las rutas que el contrato no cubre.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as ErrorHTTP

from .almacenamiento import ErrorDeSincronizacion, asegurar_resultados
from .configuracion import Configuracion, ErrorDeConfiguracion, obtener_configuracion
from .contrato.api import create_app as crear_app_contrato
from .contrato.service import _SUPPORTED_DEPARTMENTS as DEPARTAMENTOS_DEL_CONTRATO
from .repositorio import RepositorioDirectorio

registro = logging.getLogger(__name__)

VERSION = "1.0.0"

RUTA_DASHBOARD = "/api/dashboard"
RUTA_SALUD = "/api/salud"
RUTA_ESQUEMA = "/api/openapi.json"
RUTA_DOCS = "/api/docs"


def _validar_departamentos(configuracion: Configuracion) -> None:
    """Fallar al arrancar si se pide servir un departamento fuera del contrato."""
    fuera = sorted(set(configuracion.departamentos) - set(DEPARTAMENTOS_DEL_CONTRATO))
    if fuera:
        raise ErrorDeConfiguracion(
            "SATD_DEPARTAMENTOS incluye codigos que el contrato no admite: "
            f"{', '.join(fuera)}. El contrato vigente cubre "
            f"{', '.join(sorted(DEPARTAMENTOS_DEL_CONTRATO))}."
        )


def _error(estado: int, codigo: str, mensaje: str) -> JSONResponse:
    """Devolver un error con la misma forma que usa el contrato."""
    return JSONResponse(status_code=estado, content={"error_code": codigo, "message": mensaje})


def crear_app(configuracion: Configuracion | None = None) -> FastAPI:
    """Construir la aplicacion lista para desplegar."""
    actual = configuracion or obtener_configuracion()
    logging.basicConfig(level=actual.nivel_log.upper())
    _validar_departamentos(actual)

    try:
        disponibles = asegurar_resultados(actual)
    except ErrorDeSincronizacion:
        registro.exception("No hay resultados disponibles y la sincronizacion fallo")
        raise

    repositorio = RepositorioDirectorio(actual.directorio_resultados, actual.departamentos)

    aplicacion = crear_app_contrato(repositorio)
    aplicacion.title = "SAT Dengue, API del tablero"
    aplicacion.version = VERSION
    aplicacion.description = (
        "Servicio de solo lectura que entrega los resultados de evaluacion "
        "publicados para los municipios de Tolima y Meta. No ejecuta inferencia."
    )
    aplicacion.add_middleware(
        CORSMiddleware,
        allow_origins=list(actual.origenes_cors),
        allow_credentials=False,
        allow_methods=["GET"],
        allow_headers=["Accept", "Content-Type"],
    )

    @aplicacion.middleware("http")
    async def cachear_resultados(peticion: Request, siguiente: Any):
        """Un resultado publicado es inmutable; la salud nunca se cachea."""
        respuesta = await siguiente(peticion)
        if peticion.url.path == RUTA_DASHBOARD and respuesta.status_code == 200:
            respuesta.headers["Cache-Control"] = f"public, max-age={actual.segundos_cache}"
        elif peticion.url.path == RUTA_SALUD:
            respuesta.headers["Cache-Control"] = "no-store"
        return respuesta

    @aplicacion.exception_handler(ErrorHTTP)
    async def errores_http(_: Request, excepcion: ErrorHTTP) -> JSONResponse:
        """Dar a las rutas fuera del contrato la misma forma de error."""
        if excepcion.status_code == 404:
            return _error(404, "NOT_FOUND", "La ruta solicitada no existe en este servicio.")
        if excepcion.status_code == 405:
            return _error(
                405, "METHOD_NOT_ALLOWED", "Este servicio es de solo lectura y solo admite GET."
            )
        return _error(excepcion.status_code, "INTERNAL_ERROR", str(excepcion.detail))

    @aplicacion.get("/", summary="Descriptor del servicio", include_in_schema=False)
    def raiz() -> dict[str, Any]:
        """Orientar desde la raiz en vez de responder 404."""
        return {
            "servicio": actual.nombre_servicio,
            "version": VERSION,
            "descripcion": aplicacion.description,
            "rutas": {
                "resultados": f"{RUTA_DASHBOARD}?department_code=73&period=2026-09",
                "salud": RUTA_SALUD,
                **({"documentacion": RUTA_DOCS} if actual.exponer_docs else {}),
            },
        }

    @aplicacion.get(RUTA_SALUD, summary="Estado del servicio y resultados cargados")
    def salud() -> dict[str, Any]:
        """Responder sin consultar datos, para sondas de arranque y de vida."""
        periodos = repositorio.periodos_disponibles
        return {
            "servicio": actual.nombre_servicio,
            "version": VERSION,
            "entorno": actual.entorno,
            "resultados_cargados": sum(len(lista) for lista in periodos.values()),
            "periodos_por_departamento": periodos,
            "origen_durable": actual.bucket_s3 or None,
        }

    if actual.exponer_docs:

        @aplicacion.get(RUTA_ESQUEMA, include_in_schema=False)
        def esquema() -> JSONResponse:
            """Publicar el OpenAPI, que el contrato deja oculto."""
            return JSONResponse(aplicacion.openapi())

        @aplicacion.get(RUTA_DOCS, include_in_schema=False)
        def documentacion():
            """Interfaz de exploracion del contrato."""
            return get_swagger_ui_html(openapi_url=RUTA_ESQUEMA, title=aplicacion.title)

    registro.info(
        "Servicio listo: %d resultado(s) en %s",
        disponibles,
        actual.directorio_resultados,
    )
    return aplicacion


app = crear_app()
