"""CLI de registro, aprobación, cierre y comparación reproducible sin interfaz web."""

import argparse
import json
from pathlib import Path

import yaml

from sat_dengue_pipeline.factory.configuration import project_root
from sat_dengue_pipeline.raw.serialization import atomic_write

from .compare import compare
from .configuration import load_configuration
from .registry import Registry, confined, read_yaml, registry_lock
from .runner import execute


def main() -> None:
    """Ejecutar operaciones explícitas, manteniendo aprobación y ciencia separadas."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=project_root().parent)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("validate")
    commands.add_parser("list")
    registration = commands.add_parser("register")
    registration.add_argument("--entry", required=True)
    transition = commands.add_parser("transition")
    transition.add_argument("experiment_id")
    transition.add_argument("status", choices=["APPROVED", "COMPLETED", "BLOCKED"])
    transition.add_argument("--result", default="PENDING")
    run = commands.add_parser("run")
    run.add_argument("experiment_id")
    comparison = commands.add_parser("compare")
    comparison.add_argument("--status")
    comparison.add_argument("--candidate")
    comparison.add_argument("--horizon", type=int, choices=[1, 2])
    args = parser.parse_args()
    root = args.root
    if args.command == "run":
        value = execute(args.experiment_id, root=root)
    elif args.command == "compare":
        value = compare(root, status=args.status, candidate=args.candidate, horizon=args.horizon)
    elif args.command in {"register", "transition"}:
        with registry_lock(root):
            registry = Registry(root)
            if args.command == "register":
                entry = read_yaml(confined(root, args.entry, "docs/experiments"))
                if entry["status"] != "PROPOSED":
                    raise ValueError("Registrar solo propuestas; aprobación es otra transición")
                document = {
                    **registry.document,
                    "experiments": [*registry.document["experiments"], entry],
                }
                validated = Registry(root, document=document)
                load_configuration(root, validated.get(entry["experiment_id"]))
                atomic_write(
                    registry.path, yaml.safe_dump(document, sort_keys=False).encode("utf-8")
                )
            else:
                load_configuration(root, registry.get(args.experiment_id))
                registry.assert_identity(registry.get(args.experiment_id))
                registry.transition(args.experiment_id, args.status, args.result)
        value = {"status": "OK"}
    else:
        registry = Registry(root, verify_documents=args.command != "list")
        for entry in registry.entries.values():
            if args.command != "list":
                load_configuration(root, entry)
            registry.assert_identity(entry)
        value = list(registry.entries.values()) if args.command == "list" else {"status": "VALID"}
    print(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
