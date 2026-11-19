"""Rutas de inferencia retrospectiva con el ajuste logístico publicado."""

import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool

from sat_dengue_runtime.calendar import add_months
from sat_dengue_runtime.inference import InferenceEngine, Upload, catalogue

from .configuracion import Configuracion

RUTA_INFERENCIA = "/api/inferencia/t2"
MODELO_NO_DISPONIBLE = "Modelo T+2 no disponible."
MAX_BYTES = 16 * 1024
registro = logging.getLogger(__name__)


def _error(estado: int, codigo: str, mensaje: str) -> JSONResponse:
    """Devolver el error según el contrato de la API."""
    return JSONResponse(status_code=estado, content={"error_code": codigo, "message": mensaje})


def _catalogo() -> dict[str, str]:
    """Leer el catálogo empaquetado o el del repositorio en desarrollo."""
    archivo = Path(__file__).with_name("divipola_coordenadas.csv")
    if not archivo.is_file():
        archivo = Path(__file__).resolve().parents[3] / "pipeline/conf/geografia/divipola_coordenadas.csv"
    return catalogue(archivo)


def crear_router(configuracion: Configuracion) -> APIRouter:
    """Verificar el paquete una vez y registrar las rutas de estado y cálculo."""
    municipios = _catalogo()
    motor = None
    if configuracion.directorio_inferencia is not None and configuracion.huella_inferencia:
        try:
            motor = InferenceEngine(
                configuracion.directorio_inferencia, configuracion.huella_inferencia, municipios
            )
        except (OSError, ValueError, KeyError, TypeError):
            registro.warning("El paquete privado de inferencia no pudo verificarse")
    router = APIRouter(tags=["Inferencia retrospectiva"])

    @router.get(RUTA_INFERENCIA, summary="Modelo y meses disponibles para inferencia T+2")
    def estado() -> dict[str, Any]:
        modelo = motor.manifest if motor is not None else None
        return {
            "municipalities": sorted(municipios),
            "model": {
                "experiment_id": modelo.experiment_id,
                "version": modelo.execution_id,
                "periods": modelo.periods,
                "history_mode": modelo.history_mode,
            }
            if modelo is not None
            else None,
        }

    @router.post(RUTA_INFERENCIA, summary="Calcular el ranking municipal T+2", response_model=None)
    async def inferir(peticion: Request) -> dict[str, Any] | JSONResponse:
        if motor is None:
            return _error(503, "MODEL_UNAVAILABLE", MODELO_NO_DISPONIBLE)

        datos = bytearray()
        async for fragmento in peticion.stream():
            if len(datos) + len(fragmento) > MAX_BYTES:
                return _error(413, "UPLOAD_TOO_LARGE", "La solicitud supera el tamaño permitido.")
            datos.extend(fragmento)
        try:
            carga = Upload.model_validate_json(datos)
        except ValidationError:
            return _error(422, "INVALID_UPLOAD", "Mes o conteos municipales inválidos.")
        codigos = {fila.code for fila in carga.rows}
        if len(codigos) != len(carga.rows) or not codigos <= municipios.keys():
            return _error(422, "INVALID_DIVIPOLA", "Códigos DIVIPOLA desconocidos o repetidos.")
        if carga.period not in motor.coverage:
            return _error(422, "OUTSIDE_COVERAGE", "Mes fuera de la cobertura de inferencia.")
        try:
            filas = await run_in_threadpool(motor.predict, carga)
        except (ValueError, KeyError, ArithmeticError):
            registro.error("Falló la preparación de predictores de T+2")
            return _error(503, "MODEL_UNAVAILABLE", MODELO_NO_DISPONIBLE)
        return {
            "experiment_id": motor.manifest.experiment_id,
            "model_version": motor.manifest.execution_id,
            "history_mode": motor.manifest.history_mode,
            "reference_period": carga.period,
            "target_period": add_months(carga.period, 2),
            "sample": carga.sample,
            "rows": filas,
        }

    return router
