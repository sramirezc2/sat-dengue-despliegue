"""Registro cerrado, rutas confinadas, hashes y transiciones verificables en Git."""

import json
import re
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

import yaml

from sat_dengue_pipeline.acquisition.contracts import relative_path
from sat_dengue_pipeline.experiments.rolling import stable_digest
from sat_dengue_pipeline.raw.contract import sha256
from sat_dengue_pipeline.raw.serialization import atomic_write, canonical_bytes

STATES = {"PROPOSED", "APPROVED", "RUNNING", "COMPLETED", "BLOCKED"}
TRANSITIONS = {
    "PROPOSED": {"APPROVED"},
    "APPROVED": {"RUNNING"},
    "RUNNING": {"COMPLETED", "BLOCKED"},
    "COMPLETED": set(),
    "BLOCKED": set(),
}
RESULTS = {"PENDING", "POSITIVE", "NEGATIVE", "INCONCLUSIVE", "BLOCKED", "NOT_APPLICABLE"}
FIELDS = set(
    (
        "experiment_id experiment_slug hypothesis_id title experiment_type status protocol "
        "protocol_sha256 configuration configuration_sha256 pipeline conclusions scientific_result "
        "champion_status"
    ).split()
)
CONCLUSION_SECTIONS = (
    "Hipótesis",
    "Resultado",
    "Métricas principales",
    "Comparación",
    "Limitaciones",
    "Decisión científica",
    "Qué se aprendió",
    "Próximo paso",
)


class UniqueLoader(yaml.SafeLoader):
    """YAML sin claves duplicadas ni objetos ejecutables."""


def _mapping(loader: UniqueLoader, node: yaml.MappingNode) -> dict:
    pairs = loader.construct_pairs(node)
    result = {}
    for key, value in pairs:
        if not isinstance(key, str) or key in result:
            raise ValueError("Clave YAML duplicada o no textual")
        result[key] = value
    return result


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _mapping)


def read_yaml(path: Path) -> dict:
    """Cargar únicamente un objeto YAML pequeño, sin aliases recursivos."""
    if path.stat().st_size > 512_000:
        raise ValueError("Documento pesado")
    value = yaml.load(path.read_text(encoding="utf-8"), Loader=UniqueLoader)
    # JSON rechaza objetos no declarativos y ciclos provenientes de aliases.
    canonical_bytes(value)
    if not isinstance(value, dict):
        raise ValueError("Documento debe ser un objeto")
    return value


def identifier(value: str) -> str:
    """Aceptar identidades portables sin componentes de rutas."""
    if not isinstance(value, str) or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", value) is None:
        raise ValueError("Identificador inválido")
    return value


def confined(root: Path, value: str, prefix: str, *, exists: bool = True) -> Path:
    """Rechazar escapes y symlinks en cada componente, incluso el destino final.

    Args:
        root: Raíz explícita del repositorio.
        value: Ruta POSIX relativa versionable.
        prefix: Subárbol autorizado para esta clase de archivo.
        exists: Exigir un archivo existente al leer.

    Returns:
        Ruta sin resolver enlaces simbólicos.
    """
    relative_path(value)
    if not value.startswith(prefix + "/"):
        raise ValueError("Ruta fuera del subárbol autorizado")
    current = root
    if root.is_symlink():
        raise ValueError("Raíz symlink")
    for part in Path(value).parts:
        current = current / part
        if current.is_symlink():
            raise ValueError("Symlink no permitido")
    if exists and not current.is_file():
        raise ValueError("Archivo requerido ausente")
    return current


def validate_conclusions(root: Path, entry: dict) -> None:
    """Exigir secciones no vacías y referencias verificadas a evidencia agregada."""
    path = confined(root, entry["conclusions"], "docs/experiments")
    text = path.read_text(encoding="utf-8")
    if entry["experiment_id"] not in text or entry["scientific_result"] not in text:
        raise ValueError("Conclusiones sin identidad o resultado declarado")
    for section in CONCLUSION_SECTIONS:
        match = re.search(r"^## " + section + r"\s*\n(.*?)(?=^## |\Z)", text, re.M | re.S)
        if match is None or len(match[1].strip()) < 12 or "TODO" in match[1]:
            raise ValueError("Conclusiones incompletas: " + section)
    references = re.findall(
        r"docs/evidence/experiments/" + entry["experiment_id"] + r"/[A-Za-z0-9_-]+/inventory.json",
        text,
    )
    if not references:
        raise ValueError("Conclusiones sin evidencia")
    from .evidence import verify_execution

    records = [verify_execution(root, ref) for ref in references]
    if any(
        any(
            record[k] != entry[k]
            for k in ("experiment_id", "protocol_sha256", "configuration_sha256")
        )
        for record in records
    ):
        raise ValueError("Conclusiones con otra receta")
    if not any(record["status"] == "COMPLETED" for record in records):
        raise ValueError("Conclusiones sin ejecución completada")


class Registry:
    """Fuente versionada de recetas y aprobaciones; no depende de MLflow."""

    def __init__(
        self, root: Path, *, document: dict | None = None, verify_documents: bool = True
    ) -> None:
        """Recibir raíz explícita, sin descubrir repositorios vecinos."""
        self.root = root
        self.path = confined(root, "docs/experiments/registry.yml", "docs/experiments")
        self.document = read_yaml(self.path) if document is None else document
        if set(self.document) != {"schema_version", "experiments"} or (
            type(self.document["schema_version"]) is not int
            or self.document["schema_version"] != 1
            or not isinstance(self.document["experiments"], list)
        ):
            raise ValueError("Esquema de registro inválido")
        self.entries: dict[str, dict[str, Any]] = {}
        slugs = set()
        for entry in self.document["experiments"]:
            if not isinstance(entry, dict) or set(entry) != FIELDS:
                raise ValueError("Campos de registro desconocidos o ausentes")
            for name in ("experiment_id", "experiment_slug", "hypothesis_id"):
                identifier(entry[name])
            eid = entry["experiment_id"]
            if eid in self.entries or entry["experiment_slug"] in slugs:
                raise ValueError("Identificador o slug duplicado")
            slugs.add(entry["experiment_slug"])
            if (
                entry["status"] not in STATES
                or entry["experiment_type"] not in {"synthetic_fixture", "scientific"}
                or entry["scientific_result"] not in RESULTS
                or entry["champion_status"] != "NOT_SELECTED"
                or entry["pipeline"] != "experiment_run"
                or not isinstance(entry["title"], str)
                or not entry["title"].strip()
            ):
                raise ValueError("Estado, tipo o propósito no permitido")
            for name, prefix in (
                ("protocol", "docs/experiments"),
                ("configuration", "pipeline/conf/experiments"),
            ):
                path = confined(root, entry[name], prefix, exists=verify_documents)
                if not re.fullmatch(r"[a-f0-9]{64}", entry[name + "_sha256"]) or (
                    verify_documents and sha256(path) != entry[name + "_sha256"]
                ):
                    raise ValueError("Hash de protocolo/configuración alterado")
            if entry["protocol"] != f"docs/experiments/{eid}/SPECIFICATION.md" or (
                entry["conclusions"] != f"docs/experiments/{eid}/CONCLUSIONS.md"
            ):
                raise ValueError("Rutas documentales inconsistentes")
            confined(root, entry["conclusions"], "docs/experiments", exists=False)
            if entry["status"] == "COMPLETED":
                if entry["scientific_result"] == "PENDING":
                    raise ValueError("Resultado pendiente no permite COMPLETED")
                if verify_documents:
                    validate_conclusions(root, entry)
            self.entries[eid] = entry

    def get(self, experiment_id: str, *, approved: bool = False) -> dict:
        """Resolver identidad única y exigir aprobación antes de cualquier ejecución."""
        identifier(experiment_id)
        if experiment_id not in self.entries:
            raise ValueError("Experimento no registrado")
        entry = self.entries[experiment_id]
        if approved and entry["status"] != "APPROVED":
            raise ValueError("Experimento no APPROVED")
        return entry.copy()

    def transition(self, experiment_id: str, status: str, result: str | None = None) -> None:
        """Aplicar una transición legal; las recetas de la historia no se reemplazan."""
        entry = self.entries[experiment_id]
        result = entry["scientific_result"] if result is None else result
        if status not in TRANSITIONS[entry["status"]] or result not in RESULTS:
            raise ValueError("Transición o resultado inválidos")
        changed = {**entry, "status": status, "scientific_result": result}
        if status == "COMPLETED":
            if result == "PENDING":
                raise ValueError("Conclusiones y resultado requeridos")
            validate_conclusions(self.root, changed)
        entry.update(changed)
        atomic_write(self.path, yaml.safe_dump(self.document, sort_keys=False).encode("utf-8"))

    def assert_identity(self, entry: dict) -> None:
        """Impedir reutilizar un ID con otra receta aun si se recalculan sus hashes."""
        folder = confined(
            self.root,
            "docs/evidence/experiments/" + entry["experiment_id"],
            "docs/evidence/experiments",
            exists=False,
        )
        if folder.exists():
            for path in sorted(folder.iterdir()):
                receipt = confined(
                    self.root,
                    str((path / "receipt.json").relative_to(self.root)),
                    "docs/evidence/experiments",
                )
                old = json.loads(receipt.read_bytes())
                if any(
                    old[name] != entry[name]
                    for name in ("experiment_id", "protocol_sha256", "configuration_sha256")
                ):
                    raise ValueError("Identificador con otra receta histórica")


@contextmanager
def registry_lock(root: Path) -> Iterator[None]:
    """Serializar mutaciones con mkdir exclusivo portable; lock abandonado falla cerrado."""
    path = confined(root, "pipeline/data/experiment-registry.lock", "pipeline/data", exists=False)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.mkdir()
    try:
        yield
    finally:
        path.rmdir()


def recipe_identity(entry: dict) -> str:
    """Identificar solamente la receta congelada, sin estados mutables."""
    return stable_digest(
        {k: entry[k] for k in ("experiment_id", "protocol_sha256", "configuration_sha256")}
    )
