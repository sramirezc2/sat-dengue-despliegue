"""Pruebas de la recuperacion segura de resultados desde S3."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from sat_api import almacenamiento
from sat_api.almacenamiento import ErrorDeSincronizacion
from sat_api.configuracion import Configuracion

RAIZ = Path(__file__).resolve().parents[3]
RESULTADO_VALIDO = RAIZ / "datos" / "resultados" / "resultado_73_2025-10.json"


def _configuracion(directorio: Path, bucket: str = "") -> Configuracion:
    """Crear una configuracion minima para las pruebas de almacenamiento.

    Args:
        directorio: Directorio local usado como cache.
        bucket: Bucket remoto; vacio desactiva S3.

    Returns:
        Configuracion aislada para la prueba.
    """
    return Configuracion(
        nombre_servicio="sat-dengue-api",
        entorno="prueba",
        nivel_log="warning",
        directorio_resultados=directorio,
        departamentos=("50", "73"),
        origenes_cors=("http://localhost",),
        bucket_s3=bucket,
        prefijo_s3="resultados/",
        sincronizar_al_arrancar=True,
        segundos_espera_s3=5,
        exponer_docs=False,
        segundos_cache=300,
    )


class ClienteS3Falso:
    """Cliente S3 pequeno que entrega un unico objeto controlado."""

    def __init__(
        self,
        contenido: bytes,
        error: Exception | None = None,
        tamano_declarado: int | None = None,
    ) -> None:
        self.contenido = contenido
        self.error = error
        self.tamano_declarado = tamano_declarado or len(contenido)
        self.destinos: list[Path] = []

    def get_paginator(self, _: str) -> "ClienteS3Falso":
        """Devolver el paginador falso."""
        return self

    def paginate(self, **_: Any) -> list[dict[str, Any]]:
        """Declarar un objeto con el tamano esperado."""
        return [
            {
                "Contents": [
                    {
                        "Key": "resultados/resultado_73_2025-10.json",
                        "Size": self.tamano_declarado,
                    }
                ]
            }
        ]

    def download_file(self, _: str, __: str, destino: str) -> None:
        """Escribir el objeto o simular una descarga interrumpida."""
        ruta = Path(destino)
        self.destinos.append(ruta)
        if self.error is not None:
            ruta.write_bytes(self.contenido[:20])
            raise self.error
        ruta.write_bytes(self.contenido)


def test_sin_bucket_conserva_los_resultados_locales(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Sin S3, contar los resultados existentes sin crear un cliente remoto."""
    (tmp_path / "resultado_73_2025-10.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(
        almacenamiento,
        "_cliente_s3",
        lambda _: pytest.fail("no se debe crear un cliente S3"),
    )

    assert almacenamiento.sincronizar_desde_s3(_configuracion(tmp_path)) == 1


def test_un_objeto_del_mismo_tamano_se_reemplaza_atomicamente(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Descargar siempre y publicar desde un temporal validado."""
    contenido = RESULTADO_VALIDO.read_bytes()
    final = tmp_path / RESULTADO_VALIDO.name
    final.write_bytes(b"x" * len(contenido))
    cliente = ClienteS3Falso(contenido)
    monkeypatch.setattr(almacenamiento, "_cliente_s3", lambda _: cliente)

    assert almacenamiento.sincronizar_desde_s3(_configuracion(tmp_path, "bucket")) == 1
    assert final.read_bytes() == contenido
    assert cliente.destinos[0] != final
    assert list(tmp_path.glob("*.tmp")) == []


def test_una_descarga_interrumpida_preserva_el_resultado_anterior(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No exponer bytes parciales cuando el cliente remoto falla."""
    contenido = RESULTADO_VALIDO.read_bytes()
    final = tmp_path / RESULTADO_VALIDO.name
    anterior = b"resultado local anterior"
    final.write_bytes(anterior)
    cliente = ClienteS3Falso(contenido, RuntimeError("conexion interrumpida"))
    monkeypatch.setattr(almacenamiento, "_cliente_s3", lambda _: cliente)

    with pytest.raises(ErrorDeSincronizacion, match="conexion interrumpida"):
        almacenamiento.sincronizar_desde_s3(_configuracion(tmp_path, "bucket"))

    assert final.read_bytes() == anterior
    assert list(tmp_path.glob("*.tmp")) == []


def test_una_descarga_incompleta_preserva_el_resultado_anterior(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Rechazar una descarga que termina con menos bytes de los declarados."""
    final = tmp_path / RESULTADO_VALIDO.name
    anterior = RESULTADO_VALIDO.read_bytes()
    final.write_bytes(anterior)
    cliente = ClienteS3Falso(b"parcial", tamano_declarado=100)
    monkeypatch.setattr(almacenamiento, "_cliente_s3", lambda _: cliente)

    with pytest.raises(ErrorDeSincronizacion, match="quedo incompleta"):
        almacenamiento.sincronizar_desde_s3(_configuracion(tmp_path, "bucket"))

    assert final.read_bytes() == anterior
    assert list(tmp_path.glob("*.tmp")) == []


def test_un_json_remoto_invalido_preserva_el_resultado_anterior(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Reutilizar el loader del contrato antes de reemplazar un resultado."""
    final = tmp_path / RESULTADO_VALIDO.name
    anterior = RESULTADO_VALIDO.read_bytes()
    final.write_bytes(anterior)
    cliente = ClienteS3Falso(b'{"invalido": true}')
    monkeypatch.setattr(almacenamiento, "_cliente_s3", lambda _: cliente)

    with pytest.raises(ErrorDeSincronizacion, match="no cumple el contrato"):
        almacenamiento.sincronizar_desde_s3(_configuracion(tmp_path, "bucket"))

    assert final.read_bytes() == anterior
    assert list(tmp_path.glob("*.tmp")) == []


def test_asegurar_resultados_continua_con_la_copia_local_si_s3_falla(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Mantener disponibilidad cuando existe una copia local previa."""
    (tmp_path / RESULTADO_VALIDO.name).write_bytes(RESULTADO_VALIDO.read_bytes())

    def fallar(_: Configuracion) -> int:
        """Simular un fallo completo de sincronizacion."""
        raise ErrorDeSincronizacion("S3 no disponible")

    monkeypatch.setattr(almacenamiento, "sincronizar_desde_s3", fallar)

    assert almacenamiento.asegurar_resultados(_configuracion(tmp_path, "bucket")) == 1
