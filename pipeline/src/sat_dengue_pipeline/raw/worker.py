"""Worker local sin red, proveedores, publicaciones ni datos reales en modo fixture."""

import builtins
import json
import os
import shutil
import socket
import sys
from pathlib import Path


def enforce_boundaries(synthetic: bool) -> None:
    """Mantener los centinelas también en intérpretes hijos, fuera de pytest."""

    def no_network(*args: object, **kwargs: object) -> None:
        """Bloquear red y resolución DNS en toda reconstrucción."""
        raise RuntimeError("La construcción canónica es local y sin red")

    socket.socket.connect = no_network
    socket.socket.connect_ex = no_network
    socket.create_connection = no_network
    socket.getaddrinfo = no_network
    original_import = builtins.__import__

    def isolated_import(name: str, *args: object, **kwargs: object) -> object:
        """Impedir SDKs de proveedores y dependencias inversas."""
        if name.split(".")[0] in {"huggingface_hub", "boto3", "botocore", "app", "sat_api"} or (
            name == "sat_dengue_pipeline.acquisition.sources"
        ):
            raise ImportError("Proveedor o producto después de adquisición")
        return original_import(name, *args, **kwargs)

    builtins.__import__ = isolated_import
    repo = Path(__file__).resolve().parents[4]
    protected = [repo / "datos/resultados", repo.parent / "SAT-Dengue-V2"]
    if synthetic:
        protected.append(repo / "datos/datos-crudos")

    def audit(event: str, args: tuple) -> None:
        """Bloquear los árboles protegidos antes de cualquier open de Python."""
        if event == "open" and isinstance(args[0], (str, bytes)):
            path = Path(os.fsdecode(args[0])).resolve()
            if any(path.is_relative_to(root) for root in protected):
                raise RuntimeError("Acceso a datos protegidos")

    sys.addaudithook(audit)


def main() -> None:
    """Copiar solo crudos a un inbox nuevo, reconstruir y devolver recibo agregado."""
    path = Path(sys.argv[1])
    request = json.loads(path.read_bytes())
    enforce_boundaries(request["config"]["profile"] == "synthetic")
    from sat_dengue_pipeline.acquisition.contracts import ResolvedBundle, ResolvedFile
    from sat_dengue_pipeline.raw.build import build
    from sat_dengue_pipeline.raw.contract import BuildConfig
    from sat_dengue_pipeline.raw.serialization import atomic_write, canonical_bytes

    raw = path.parent / "inbox"
    raw.mkdir()
    files = []
    for item in request["bundle"].pop("files"):
        original = Path(item.pop("path"))
        destination = raw / original.name
        shutil.copyfile(original, destination)
        files.append(ResolvedFile(path=destination, **item))
    bundle = ResolvedBundle(files=tuple(files), **request["bundle"])
    inventory = request["inventory"]
    if inventory is not None:
        inventory = {name: tuple(value) for name, value in inventory.items()}
    artifact, audit = build(bundle, BuildConfig(**request["config"]), path.parent, inventory)
    atomic_write(
        path.parent / "receipt.json",
        canonical_bytes(
            {
                "semantic_digest": artifact.semantic_digest,
                "serialized_sha256": artifact.serialized_sha256,
                "audit": audit,
                "pid": os.getpid(),
            }
        ),
    )


if __name__ == "__main__":
    main()
