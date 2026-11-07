"""Inventario crudo cerrado y perfiles explícitos; nunca admite derivados."""

import csv
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd

from sat_dengue_pipeline.acquisition.contracts import ResolvedBundle
from sat_dengue_pipeline.domain.calendar import validate_period
from sat_dengue_pipeline.domain.temporal import TemporalPolicy

INVENTORY = {
    "divipola_catalog": (
        "Divipola-municipios.md",
        209867,
        "72eabcea0ff26370d23b9688e8d8f2246946cc815c040ccf1a6966b37a1de9f3",
    ),
    "divipola_provenance": (
        "divipola-provenance.json",
        925,
        "92091306f0130910f27de999776b5cf4ed36b7dd7c89bd724d58caeb74f8c158",
    ),
    "dengue_notifications": (
        "dengue.csv",
        875694283,
        "58d277cfef7a60c28d488eefe4e7a1a7bf0f7b0df3dd88245971cd7b3d32c84b",
    ),
    "severe_dengue_notifications": (
        "dengue_grave.csv",
        24537734,
        "3d60e96ccbedc35a19a8f5f54be8d786aa599813259c914f131522bf17dd1d70",
    ),
    "daily_climate": (
        "google_earth_engine.csv",
        1714544311,
        "dfe20fa02b6d6068c04744b5c86f44112048400a7fde637368c0d4effc88cb3f",
    ),
}
EPI_HEADER = (
    "CONSECUTIVE COD_EVE FEC_NOT SEMANA ANO COD_PRE COD_SUB EDAD UNI_MED SEXO COD_PAIS_O "
    "COD_DPTO_O COD_MUN_O AREA OCUPACION TIP_SS COD_ASE PER_ETN GRU_POB nom_grupo estrato "
    "GP_DISCAPA GP_DESPLAZ GP_MIGRANT GP_CARCELA GP_GESTAN sem_ges GP_INDIGEN GP_POBICFB "
    "GP_MAD_COM GP_DESMOVI GP_PSIQUIA GP_VIC_VIO GP_OTROS fuente COD_PAIS_R COD_DPTO_R "
    "COD_MUN_R COD_DPTO_N COD_MUN_N FEC_CON INI_SIN TIP_CAS PAC_HOS FEC_HOS CON_FIN FEC_DEF "
    "AJUSTE FECHA_NTO CBMTE FEC_ARC_XL FEC_AJU FM_FUERZA FM_UNIDAD FM_GRADO confirmados "
    "va_sispro Estado_final_de_caso nom_est_f_caso Nombre_upgd Pais_ocurrencia Nombre_evento "
    "Departamento_ocurrencia Municipio_ocurrencia Pais_residencia Departamento_residencia "
    "Municipio_residencia Departamento_Notificacion Municipio_notificacion"
).split()
CLIMATE_HEADER = (
    "date year month day_of_year dpto_ccdgo dpto_cnmbr mpio_ccdgo mpio_cdpmp mpio_cnmbr "
    "rain_mm_day temp_mean_c dewpoint_mean_c soil_water_l1_mean surface_runoff_mm_day "
    "total_evaporation_mm_day_ecmwf wind_u_mean_ms wind_v_mean_ms solar_radiation_mj_m2_day"
).split()
HEADERS = {
    "dengue_notifications": EPI_HEADER,
    "severe_dengue_notifications": EPI_HEADER,
    "daily_climate": CLIMATE_HEADER,
}


def sha256(path: Path) -> str:
    """Calcular una huella sin cargar el archivo completo."""
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


@dataclass(frozen=True)
class BuildConfig:
    """Configuración científica cerrada; el perfil artificial nunca certifica el real."""

    profile: str = "approved"
    start: str = "2011-06"
    end: str = "2024-12"
    municipalities: int = 1122
    epi_start: str = "2011-06"
    reserved_start: str = "2025-01"

    def __post_init__(self) -> None:
        """Validar cobertura explícita y reutilizar la autoridad temporal."""
        for period in (self.start, self.end, self.epi_start):
            validate_period(period)
        TemporalPolicy(self.reserved_start)
        if (
            self.profile not in {"approved", "synthetic"}
            or type(self.municipalities) is not int
            or self.municipalities <= 0
            or not self.start <= self.epi_start <= self.end < self.reserved_start
        ):
            raise ValueError("Configuración canónica inválida")
        if self.profile == "approved" and (
            self.start,
            self.end,
            self.municipalities,
            self.epi_start,
        ) != ("2011-06", "2024-12", 1122, "2011-06"):
            raise ValueError("No se puede reducir el contrato aprobado")

    @property
    def periods(self) -> list[str]:
        """Enumerar el calendario exacto de desarrollo."""
        return pd.period_range(self.start, self.end, freq="M").astype(str).tolist()

    def payload(self) -> dict:
        """Devolver configuración serializable sin rutas o proveedor."""
        return asdict(self)


def raw_contract_validation(
    bundle: ResolvedBundle,
    config: BuildConfig,
    synthetic_inventory: dict | None = None,
) -> ResolvedBundle:
    """Verificar inventario completo y luego encabezados antes de proyectar claves.

    Args:
        bundle: Solo archivos locales y metadatos neutrales.
        config: Perfil aprobado o fixture explícito.
        synthetic_inventory: Contrato artificial suministrado por el generador de fixtures.

    Returns:
        El mismo bundle después de verificar todos los bytes y encabezados.
    """
    if bundle.release_kind != "raw_sources":
        raise ValueError("Solo raw_sources; tablas, features y derivados prohibidos")
    expected = INVENTORY if config.profile == "approved" else synthetic_inventory
    if expected is None or set(expected) != set(INVENTORY):
        raise ValueError("Falta contrato sintético explícito")
    if config.profile == "approved" and synthetic_inventory is not None:
        raise ValueError("No se puede sustituir el inventario aprobado")
    if len(bundle.files) != 5 or len({f.logical_name for f in bundle.files}) != 5:
        raise ValueError("Inventario faltante, adicional o duplicado")
    actual = {f.logical_name: (f.path.name, f.size_bytes, f.sha256) for f in bundle.files}
    if actual != expected or any(actual[k][0] != INVENTORY[k][0] for k in actual):
        raise ValueError("Inventario o archivo prohibido")
    # Completar la integridad de TODOS los archivos antes de interpretar encabezados.
    for file in bundle.files:
        if (
            file.path.is_symlink()
            or not file.path.is_file()
            or file.path.stat().st_size != file.size_bytes
            or sha256(file.path) != file.sha256
        ):
            raise ValueError("Tamaño, SHA-256 o archivo crudo inválido")
    for file in bundle.files:
        if file.logical_name in HEADERS:
            with file.path.open(encoding="utf-8-sig", newline="") as stream:
                header = next(csv.reader(stream), None)
            if header != HEADERS[file.logical_name]:
                raise ValueError("Encabezado crudo incompatible")
    files = {file.logical_name: file for file in bundle.files}
    try:
        catalog = json.loads(files["divipola_catalog"].path.read_text(encoding="utf-8-sig"))
        provenance = json.loads(files["divipola_provenance"].path.read_text(encoding="utf-8-sig"))
        if not isinstance(catalog["resultado"], list) or (
            provenance["files"]["Divipola-municipios.md"]["sha256"]
            != files["divipola_catalog"].sha256
        ):
            raise ValueError("Esquema/procedencia JSON crudo inválido")
        required = {
            "CODIGO_MUNICIPIO",
            "CODIGO_DEPARTAMENTO",
            "CODIGO_DPTO_MPIO",
            "NOMBRE_MUNICIPIO",
        }
        if not all(
            isinstance(row, dict) and required <= row.keys() for row in catalog["resultado"]
        ):
            raise ValueError("Esquema JSON DIVIPOLA inválido")
    except (KeyError, TypeError, json.JSONDecodeError):
        raise ValueError("Esquema/procedencia JSON crudo inválido") from None
    return bundle
