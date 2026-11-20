"""Construir el contexto privado de predictores de los orígenes publicados en 2025.

Uso, con acceso al release crudo aprobado:

    python demo/contexto.py [--origen 2025-01] [--raw DIRECTORIO]

Cada origen se calcula con su propio prefijo temporal, como la publicación
congelada. El archivo resultante queda en ``pipeline/data/demo/`` y no se versiona.
"""

import argparse
import hashlib
import io
import json
import sys
from pathlib import Path

import pandas as pd
from sat_dengue_pipeline.acquisition.contracts import ReleaseManifest, ResolvedBundle, ResolvedFile
from sat_dengue_pipeline.acquisition.raw_manifest import OPERATIONAL_MANIFEST
from sat_dengue_pipeline.domain.calendar import add_months
from sat_dengue_pipeline.domain.canonical import KEYS, PREDICTORS
from sat_dengue_pipeline.raw.contract import sha256
from sat_dengue_pipeline.risk.inference import feature_prefix

ROOT = Path(__file__).resolve().parents[1]
CONTEXT_DIR = ROOT / "pipeline/data/demo"
ORIGINS = [add_months(f"2025-{m:02d}", -2) for m in range(1, 13)]
COLUMNS = [*KEYS, "department_code", "municipality_name", *PREDICTORS]


def manifest() -> ReleaseManifest:
    """Leer el manifiesto operativo con el que se materializó el modelo."""
    return ReleaseManifest.from_json((ROOT / "pipeline" / OPERATIONAL_MANIFEST).read_text())


def bundle(raw: Path | None = None) -> ResolvedBundle:
    """Resolver las cinco fuentes y exigir sus huellas aprobadas."""
    release = manifest()
    cache = (
        raw or ROOT / "pipeline/data/01_raw/inbox" / release.release_id / release.manifest_sha256
    )
    files = []
    for f in release.files:
        path = cache / f.relative_path
        if not path.is_file() or path.stat().st_size != f.size_bytes or sha256(path) != f.sha256:
            raise ValueError(f"Fuente ausente o distinta del release aprobado: {f.relative_path}")
        files.append(ResolvedFile(f.logical_name, path, f.size_bytes, f.sha256))
    return ResolvedBundle(
        release.release_id,
        release.manifest_sha256,
        release.coverage_start,
        release.coverage_end,
        tuple(files),
        release.release_kind,
    )


def origin_rows(source: ResolvedBundle, origin: str) -> pd.DataFrame:
    """Calcular las 76 filas del origen con el prefijo observable hasta ese mes."""
    table, _ = feature_prefix(source, origin)
    return table.loc[table.year_month.eq(origin), COLUMNS].sort_values(KEYS)


def main(argv: list[str] | None = None) -> None:
    """Escribir un CSV por origen y un índice con sus huellas."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--origen", choices=ORIGINS, action="append")
    parser.add_argument("--raw", type=Path)
    args = parser.parse_args(argv)
    source = bundle(args.raw)
    CONTEXT_DIR.mkdir(parents=True, exist_ok=True)
    index_path = CONTEXT_DIR / "contexto.json"
    index = json.loads(index_path.read_text()) if index_path.exists() else {}
    if index.get("raw_manifest_sha256", source.manifest_sha256) != source.manifest_sha256:
        raise ValueError("El índice existente procede de otro release")
    files = index.setdefault("files", {})
    for origin in args.origen or ORIGINS:
        buffer = io.StringIO()
        origin_rows(source, origin).to_csv(buffer, index=False, lineterminator="\n")
        data = buffer.getvalue().encode()
        (CONTEXT_DIR / f"contexto-{origin}.csv").write_bytes(data)
        files[origin] = hashlib.sha256(data).hexdigest()
        print(origin, files[origin], file=sys.stderr)
    index["raw_manifest_sha256"] = source.manifest_sha256
    index["files"] = dict(sorted(files.items()))
    index_path.write_text(json.dumps(index, indent=2) + "\n")


if __name__ == "__main__":
    main()
