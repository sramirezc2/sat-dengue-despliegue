"""Pruebas de la capa de despliegue.

El contrato de V2 ya trae sus propias pruebas. Aqui se verifica lo que agrega
este repositorio: la configuracion por entorno, el indice sobre el directorio
de resultados y la forma uniforme de los errores.
"""

from __future__ import annotations

import dataclasses
import json
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from sat_api.configuracion import Configuracion, ErrorDeConfiguracion, obtener_configuracion
from sat_api.main import crear_app
from sat_api.repositorio import RepositorioDirectorio, construir_indice

RAIZ = Path(__file__).resolve().parents[3]
RESULTADOS = RAIZ / "datos" / "resultados"


def _periodo(departamento: str) -> str:
    """Un periodo realmente publicado, para no fijar fechas en las pruebas."""
    periodos = sorted(p.stem.split("_")[2] for p in RESULTADOS.glob(f"resultado_{departamento}_*.json"))
    if not periodos:
        raise AssertionError(f"no hay resultados publicados para el departamento {departamento}")
    return periodos[-1]


@pytest.fixture
def configuracion(tmp_path: Path) -> Configuracion:
    destino = tmp_path / "resultados"
    destino.mkdir()
    for archivo in RESULTADOS.glob("*.json"):
        shutil.copy2(archivo, destino / archivo.name)
    return Configuracion(
        nombre_servicio="sat-dengue-api",
        entorno="prueba",
        nivel_log="warning",
        directorio_resultados=destino,
        departamentos=("50", "73"),
        origenes_cors=("http://localhost",),
        bucket_s3="",
        prefijo_s3="resultados/",
        sincronizar_al_arrancar=False,
        segundos_espera_s3=5,
        exponer_docs=True,
        segundos_cache=300,
    )


@pytest.fixture
def cliente(configuracion: Configuracion) -> TestClient:
    return TestClient(crear_app(configuracion))


# ------------------------------------------------------------------ indice


def test_el_indice_lee_la_convencion_de_nombre(tmp_path: Path) -> None:
    (tmp_path / "resultado_73_2026-09.json").write_text("{}")
    (tmp_path / "resultado_50_2026-12.json").write_text("{}")
    assert set(construir_indice(tmp_path)) == {("73", "2026-09"), ("50", "2026-12")}


def test_el_indice_ignora_archivos_que_no_siguen_la_convencion(tmp_path: Path) -> None:
    (tmp_path / "resultado_73_2026-09.json").write_text("{}")
    (tmp_path / "notas.json").write_text("{}")
    (tmp_path / "resultado_73_septiembre.json").write_text("{}")
    assert set(construir_indice(tmp_path)) == {("73", "2026-09")}


def test_un_directorio_inexistente_no_rompe_el_arranque(tmp_path: Path) -> None:
    assert construir_indice(tmp_path / "no-existe") == {}


def test_el_repositorio_descarta_departamentos_no_servidos(configuracion: Configuracion) -> None:
    repositorio = RepositorioDirectorio(configuracion.directorio_resultados, ("73",))
    assert list(repositorio.periodos_disponibles) == ["73"]


def test_publicar_un_archivo_nuevo_se_refleja_al_recargar(configuracion: Configuracion) -> None:
    repositorio = RepositorioDirectorio(configuracion.directorio_resultados, ("50", "73"))
    antes = repositorio.periodos_disponibles["73"]
    origen = configuracion.directorio_resultados / f"resultado_73_{_periodo('73')}.json"
    contenido = json.loads(origen.read_text(encoding="utf-8"))
    contenido["metadata"]["reference_period"] = "2019-08"
    contenido["department"]["requested_period"] = "2019-08"
    (configuracion.directorio_resultados / "resultado_73_2019-08.json").write_text(
        json.dumps(contenido), encoding="utf-8"
    )
    repositorio.recargar()
    assert repositorio.periodos_disponibles["73"] == sorted([*antes, "2019-08"])


# ----------------------------------------------------------- configuracion


def test_un_departamento_fuera_del_contrato_impide_arrancar(configuracion: Configuracion) -> None:
    invalida = dataclasses.replace(configuracion, departamentos=("11",))
    with pytest.raises(ErrorDeConfiguracion, match="no admite"):
        crear_app(invalida)


def test_cors_no_admite_comodin(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SATD_ORIGENES_CORS", "*")
    obtener_configuracion.cache_clear()
    with pytest.raises(ErrorDeConfiguracion, match="comodin"):
        obtener_configuracion()
    obtener_configuracion.cache_clear()


def test_un_codigo_de_departamento_mal_formado_se_rechaza(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SATD_DEPARTAMENTOS", "730")
    obtener_configuracion.cache_clear()
    with pytest.raises(ErrorDeConfiguracion, match="dos digitos"):
        obtener_configuracion()
    obtener_configuracion.cache_clear()


# ------------------------------------------------------------------- HTTP


def test_la_salud_declara_los_periodos_publicados(cliente: TestClient) -> None:
    """La salud refleja lo que hay en el directorio, sea cual sea la corrida publicada."""
    cuerpo = cliente.get("/api/salud").json()
    publicados = {
        (archivo.stem.split("_")[1], archivo.stem.split("_")[2])
        for archivo in RESULTADOS.glob("resultado_*.json")
    }
    esperado: dict[str, list[str]] = {}
    for departamento, periodo in sorted(publicados):
        esperado.setdefault(departamento, []).append(periodo)
    assert cuerpo["periodos_por_departamento"] == esperado
    assert cuerpo["resultados_cargados"] == len(publicados)
    assert cuerpo["origen_durable"] is None


def test_la_salud_nunca_se_cachea(cliente: TestClient) -> None:
    assert cliente.get("/api/salud").headers["cache-control"] == "no-store"


def test_un_resultado_publicado_se_puede_cachear(cliente: TestClient) -> None:
    respuesta = cliente.get(
        "/api/dashboard", params={"department_code": "73", "period": _periodo("73")}
    )
    assert respuesta.status_code == 200
    assert "max-age" in respuesta.headers["cache-control"]
    assert len(respuesta.json()["municipalities"]) == 47


@pytest.mark.parametrize(
    ("parametros", "estado", "codigo"),
    [
        ({"department_code": "11", "period": "2026-09"}, 400, "INVALID_DEPARTMENT_CODE"),
        ({"department_code": "73", "period": "2026-13"}, 400, "INVALID_PERIOD_FORMAT"),
        ({"department_code": "73", "period": "septiembre"}, 400, "INVALID_PERIOD_FORMAT"),
        ({"department_code": "73", "period": "2020-01"}, 404, "DASHBOARD_DATA_NOT_FOUND"),
        ({}, 400, "INVALID_DEPARTMENT_CODE"),
    ],
)
def test_las_consultas_invalidas_responden_el_codigo_del_contrato(
    cliente: TestClient, parametros: dict[str, str], estado: int, codigo: str
) -> None:
    respuesta = cliente.get("/api/dashboard", params=parametros)
    assert respuesta.status_code == estado
    assert respuesta.json()["error_code"] == codigo


def test_las_rutas_fuera_del_contrato_usan_la_misma_forma_de_error(cliente: TestClient) -> None:
    respuesta = cliente.get("/api/no-existe")
    assert respuesta.status_code == 404
    assert set(respuesta.json()) == {"error_code", "message"}
    assert respuesta.json()["error_code"] == "NOT_FOUND"


def test_el_servicio_es_de_solo_lectura(cliente: TestClient) -> None:
    respuesta = cliente.post("/api/dashboard")
    assert respuesta.status_code == 405
    assert respuesta.json()["error_code"] == "METHOD_NOT_ALLOWED"


def test_la_raiz_orienta_en_vez_de_responder_404(cliente: TestClient) -> None:
    cuerpo = cliente.get("/").json()
    assert cuerpo["rutas"]["salud"] == "/api/salud"
    assert "documentacion" in cuerpo["rutas"]


def test_el_esquema_openapi_queda_publicado(cliente: TestClient) -> None:
    esquema = cliente.get("/api/openapi.json").json()
    assert "/api/dashboard" in esquema["paths"]
    # El contrato suprime la respuesta 422 que FastAPI agrega por defecto.
    assert "422" not in esquema["paths"]["/api/dashboard"]["get"]["responses"]


def test_la_documentacion_se_puede_apagar(configuracion: Configuracion) -> None:
    sin_docs = dataclasses.replace(configuracion, exponer_docs=False)
    cliente = TestClient(crear_app(sin_docs))
    assert cliente.get("/api/docs").status_code == 404
    assert "documentacion" not in cliente.get("/").json()["rutas"]


def test_un_resultado_corrupto_no_filtra_detalles_internos(configuracion: Configuracion) -> None:
    periodo = _periodo("73")
    (configuracion.directorio_resultados / f"resultado_73_{periodo}.json").write_text(
        "{esto no es json}", encoding="utf-8"
    )
    cliente = TestClient(crear_app(configuracion))
    respuesta = cliente.get("/api/dashboard", params={"department_code": "73", "period": periodo})
    assert respuesta.status_code == 500
    assert respuesta.json()["error_code"] == "INTERNAL_ERROR"
    assert "json" not in respuesta.json()["message"].lower()
