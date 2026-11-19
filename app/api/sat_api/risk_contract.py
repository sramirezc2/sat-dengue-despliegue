"""Contrato público de prioridades retrospectivas, sin dependencias científicas."""

from typing import Annotated, Any, Literal, Self

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    StringConstraints,
    model_validator,
)

RECIPE_SHA256 = "7d67f0595cfdd990e331682ae581d4f49d1f74f83a107f4d9474540412443ec8"
BASE_COMMIT = "a9c2c1abac386053b2e78f072bdb44e0141f4045"
LEGEND = (
    "Orden de prioridad retrospectivo. La posición no representa una probabilidad "
    "calibrada ni una autorización para uso operativo."
)
Month = Annotated[str, StringConstraints(pattern=r"^2025-(0[1-9]|1[0-2])$")]
Origin = Annotated[str, StringConstraints(pattern=r"^20[0-9]{2}-(0[1-9]|1[0-2])$")]
Hash = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
Code = Annotated[str, StringConstraints(pattern=r"^(50|73)[0-9]{3}$")]
Name = Annotated[str, StringConstraints(min_length=1, max_length=150)]


def integer_number(value: Any) -> Any:
    """Aceptar números JSON integrales como JSON Schema/Zod, sin convertir strings."""
    return int(value) if type(value) is float and value.is_integer() else value


Integer = Annotated[int, BeforeValidator(integer_number)]


class StrictContract(BaseModel):
    """Rechazar campos adicionales y conversiones implícitas de tipos."""

    model_config = ConfigDict(extra="forbid", strict=True)


class RiskTrace(StrictContract):
    """Linaje público sin modelos, observaciones ni rutas privadas."""

    recipe_sha256: Literal[RECIPE_SHA256]
    recipe_commit: Literal[BASE_COMMIT]
    model_family: Literal["logistic_onset"]
    adapter_version: Literal["v1"]
    library_version: Literal["1.7.2"]
    artifact_sha256: Hash
    effective_state_sha256: Hash
    training_keys_sha256: Hash
    preparation_sha256: Hash
    predictors_sha256: Hash
    raw_manifest_sha256: Hash
    code_sha: Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{40}$")]
    code_tree_sha256: Hash
    lock_sha256: Hash
    feature_sha256: Hash
    procedure_id: Literal["SATD-RISK-2025-LOG-CLIMATE-v1"]
    procedure_sha256: Hash
    training_target_start: Literal["2012-01"]
    training_target_end: Literal["2024-09"]
    training_available_end: Literal["2024-10"]
    first_origin: Literal["2024-11"]
    artifact_contract: Literal["satd-frozen-logistic-v1"]


class RiskGovernance(StrictContract):
    """Separar selección para informe, reproducción y autorización operativa."""

    report_selection: Literal["SELECTED"]
    historical_reproduction: Literal["APPROVED"]
    operational_use: Literal["NOT_AUTHORIZED"]
    champion_status: Literal["NOT_SELECTED"]
    limitation: Literal[LEGEND]


class MunicipalPriority(StrictContract):
    """Una fila territorial, incluida cuando no puede participar en el cupo."""

    municipality_code: Code
    municipality_name: Name
    department_code: Literal["50", "73"]
    department_name: Literal["Meta", "Tolima"]
    risk_rank: Annotated[Integer, Field(ge=1, le=76)] | None
    selected_for_attention: bool
    eligibility_status: Literal["ELIGIBLE", "INELIGIBLE"]
    ineligibility_reason: (
        Literal[
            "ORIGIN_STATE_MISSING", "EXCESS_AT_ORIGIN", "REQUIRED_PREDICTORS_MISSING"
        ]
        | None
    )


class RiskRanking(StrictContract):
    """Paquete global completo; filtros nunca modifican su ranking o presupuesto."""

    schema_version: Literal["satd-risk-ranking-v1"]
    reference_period: Origin
    horizon: Literal["T2"]
    target_period: Month
    data_cutoff: Origin
    logical_generated_at: Literal["2024-11-01T00:00:00Z"]
    data_version: Annotated[str, StringConstraints(min_length=1, max_length=128)]
    data_kind: Literal["CONSOLIDATED_RETROSPECTIVE", "SYNTHETIC"]
    selection_budget: Literal[8]
    selection_scope: Literal["META_TOLIMA_GLOBAL"]
    population_count: Literal[76]
    eligible_count: Annotated[Integer, Field(ge=8, le=76)]
    tie_break: Literal["SCORE_DESC_DIVIPOLA_ASC"]
    trace: RiskTrace
    governance: RiskGovernance
    municipalities: Annotated[
        list[MunicipalPriority], Field(min_length=76, max_length=76)
    ]

    @model_validator(mode="after")
    def validate_global_ranking(self) -> Self:
        """Comprobar calendario, universo, elegibilidad, orden y selección exactos."""
        year, month = map(int, self.target_period.split("-"))
        index = year * 12 + month - 3
        origin = f"{index // 12:04d}-{index % 12 + 1:02d}"
        if self.reference_period != origin or self.data_cutoff != origin:
            raise ValueError("Calendario de inferencia incompatible")
        towns = self.municipalities
        codes = [t.municipality_code for t in towns]
        if codes != sorted(set(codes)):
            raise ValueError("Municipios duplicados o fuera de orden")
        if {d: sum(t.department_code == d for t in towns) for d in ("50", "73")} != {
            "50": 29,
            "73": 47,
        }:
            raise ValueError("Universo municipal incompleto")
        ranks = []
        for town in towns:
            if (
                town.department_code != town.municipality_code[:2]
                or town.department_name
                != {"50": "Meta", "73": "Tolima"}[town.department_code]
            ):
                raise ValueError("Identidad territorial incompatible")
            eligible = town.eligibility_status == "ELIGIBLE"
            if eligible != (town.risk_rank is not None) or eligible != (
                town.ineligibility_reason is None
            ):
                raise ValueError("Elegibilidad incoherente")
            if town.selected_for_attention != (
                town.risk_rank is not None and town.risk_rank <= 8
            ):
                raise ValueError("Selección incompatible con el ranking")
            if eligible:
                ranks.append(town.risk_rank)
        if sorted(ranks) != list(range(1, self.eligible_count + 1)):
            raise ValueError("Ranking global incompleto o duplicado")
        return self
