"""Lectura de una edición inmutable de prioridades; sin inferencia ni ciencia."""

import hashlib
import json
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import Field

from .risk_contract import Code, RiskRanking, StrictContract

NAMES = {f"prioridades_T2_2025-{m:02d}.json" for m in range(1, 13)}


class RiskView(StrictContract):
    """Conservar el documento global y expresar filtros solo como claves visibles."""

    ranking: RiskRanking
    department_filter: Literal["50", "73"] | None
    visible_municipality_codes: list[Code] = Field(max_length=76)


def read_json(raw: bytes) -> dict:
    """Rechazar claves duplicadas y constantes no finitas antes del contrato."""

    def pairs(values: list[tuple]) -> dict:
        """Impedir ambigüedad entre consumidores JSON."""
        result = {}
        for k, v in values:
            if k in result:
                raise ValueError("Clave duplicada")
            result[k] = v
        return result

    def invalid(value: str) -> None:
        """Rechazar NaN e infinitos."""
        raise ValueError("Constante no finita")

    result = json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)
    if not isinstance(result, dict):
        raise TypeError("Objeto requerido")
    return result


class RiskRepository:
    """Validar el lote completo por hashes antes de servir cualquier mes."""

    def __init__(
        self, directory: Path | None, *, allow_synthetic: bool = False
    ) -> None:
        """Seleccionar una edición local; no buscar fallback histórico o remoto."""
        self.directory = directory
        self.allow_synthetic = allow_synthetic

    def read_all(self) -> dict[str, RiskRanking]:
        """Verificar manifiesto, cardinalidad, linaje común y nombres del lote."""
        root = self.directory
        if root is None:
            return {}
        if any(p.is_symlink() for p in (root, *root.parents)):
            raise ValueError("Enlace en la edición")
        if not root.exists():
            return {}
        manifest_path = root / ".publication/manifest.json"
        if manifest_path.is_symlink() or manifest_path.parent.is_symlink():
            raise ValueError("Manifiesto inseguro")
        manifest = read_json(manifest_path.read_bytes())
        if set(manifest) != {
            "schema",
            "candidate",
            "procedure",
            "artifact_sha256",
            "files",
        } or (
            manifest["schema"] != "satd-risk-ranking-v1"
            or manifest["candidate"] != "logistic_onset"
            or manifest["procedure"] != "SATD-RISK-2025-LOG-CLIMATE-v1"
            or len(manifest["files"]) != 12
            or {f["name"] for f in manifest["files"]} != NAMES
            or {p.name for p in root.glob("*.json")} != NAMES
        ):
            raise ValueError("Edición incompleta o manifiesto incompatible")
        documents = {}
        identity = None
        for entry in manifest["files"]:
            if set(entry) != {"name", "size_bytes", "sha256"}:
                raise ValueError("Entrada de manifiesto incompatible")
            path = root / entry["name"]
            if path.is_symlink():
                raise ValueError("Resultado inseguro")
            raw = path.read_bytes()
            if (
                len(raw) != entry["size_bytes"]
                or hashlib.sha256(raw).hexdigest() != entry["sha256"]
            ):
                raise ValueError("Resultado alterado")
            model = RiskRanking.model_validate(read_json(raw))
            if not self.allow_synthetic and model.data_kind == "SYNTHETIC":
                raise ValueError("Una edición artificial no es publicación científica")
            if entry[
                "name"
            ] != f"prioridades_{model.horizon}_{model.target_period}.json" or (
                model.trace.artifact_sha256 != manifest["artifact_sha256"]
            ):
                raise ValueError("Nombre o artefacto incompatible")
            common = model.trace.model_dump(exclude={"feature_sha256"})
            common.update(data_version=model.data_version, data_kind=model.data_kind)
            if identity is not None and common != identity:
                raise ValueError("Edición mezcla identidades")
            identity = common
            documents[model.target_period] = model
        return documents


def create_risk_router(repository: RiskRepository) -> APIRouter:
    """Exponer consultas GET sobre resultados publicados, sin recalcular posiciones."""
    router = APIRouter(
        prefix="/api/prioridades/v1", tags=["Prioridades retrospectivas"]
    )

    def documents() -> dict[str, RiskRanking]:
        """Convertir errores de almacenamiento en respuesta sanitizada."""
        try:
            return repository.read_all()
        except (OSError, ValueError, TypeError, KeyError):
            raise HTTPException(500, "Edición de prioridades inválida") from None

    @router.get("/periodos", response_model=list[str])
    def periods() -> list[str]:
        """Enumerar meses objetivo de la edición validada."""
        return sorted(documents())

    @router.get("", response_model=RiskView)
    def priorities(
        target_period: str = Query(..., pattern=r"^2025-(0[1-9]|1[0-2])$"),
        horizon: Literal["T2"] = "T2",
        department_code: Literal["50", "73"] | None = None,
    ) -> RiskView:
        """Filtrar claves visibles conservando la identidad y el cupo globales."""
        model = documents().get(target_period)
        if model is None:
            raise HTTPException(
                404, "Prioridades no publicadas para ese mes y horizonte"
            )
        return RiskView(
            ranking=model,
            department_filter=department_code,
            visible_municipality_codes=[
                t.municipality_code
                for t in model.municipalities
                if department_code is None or t.department_code == department_code
            ],
        )

    return router
