"""Construye resultados del tablero desde panel, predicciones y comparación locales.

La publicación conserva el criterio y contrato del publicador V3 caracterizado.
No entrena modelos ni autoriza su uso operativo. Desde la raíz:
uv run --project pipeline python scripts/construir_resultados.py --help
"""

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

from .errors import PublicationError
from .io import load_schema, promote, stage_package, validate_staging
from .nodes import construct, local_inputs
from .package import PublicationConfig


def main() -> None:
    """Traducir argumentos, reloj y errores a mensajes/códigos compatibles del CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ("panel", "predicciones", "comparacion"):
        parser.add_argument(f"--{flag}", type=Path, required=True)
    parser.add_argument(
        "--candidato", default="auto", help="Candidato automático o override explícito"
    )
    parser.add_argument("--procedimiento", required=True, help="Identificador de la corrida")
    parser.add_argument("--version-modelo", default=None)
    parser.add_argument("--version-datos", required=True)
    parser.add_argument(
        "--retroanalisis", type=Path, default=Path("datos/retro/ventana_expansiva.json")
    )
    parser.add_argument("--salida", type=Path, default=Path("datos/resultados"))
    parser.add_argument(
        "--generado", default=None, help="Fecha UTC fija; por defecto usa el reloj UTC"
    )
    parser.add_argument(
        "--justificacion",
        default="elegido a mano por bandera",
        help="Motivo auditable del override",
    )
    args = parser.parse_args()
    try:
        generated = args.generado or datetime.now(timezone.utc).isoformat(timespec="seconds")
        config = PublicationConfig(
            args.procedimiento,
            args.version_datos,
            generated,
            args.candidato,
            args.version_modelo,
            args.justificacion,
        )
        paths = {
            key: getattr(args, key)
            for key in ("panel", "predicciones", "comparacion", "retroanalisis")
        }
        source = local_inputs(paths, config, args.salida)
        if source.retro:
            rows = source.retro["rows"]
            accumulated = sum(row.get("year") is None for row in rows)
            print(
                f"Retroanalisis: {args.retroanalisis}, {len(rows)} filas, "
                f"{accumulated} acumuladas, "
                f"procedencia {source.retro['provenance']}"
            )
        else:
            print("Retroanalisis: ausente, se publica sin ese bloque")
        package = construct(source)
        audit = package.audit
        if audit["selection"]["forced"]:
            print(f"Candidato forzado por bandera: {audit['candidate']}")
            print("  AVISO: anula el criterio de elegir_candidato(); justificarlo por escrito")
        else:
            print(f"Candidato elegido por criterio: {audit['candidate']}")
            print(f"  {audit['selection']['reason']}")
        if audit["omitted_periods"]:
            print(
                "  meses omitidos por tener un solo horizonte: "
                f"{', '.join(audit['omitted_periods'])}"
            )
        for horizon, threshold in audit["thresholds"].items():
            print(
                f"  umbral T+{horizon}: {threshold['value']:.6f} (margen {threshold['margin']:.2e})"
            )
        schema = load_schema()
        promote(validate_staging(stage_package(package, args.salida, schema), schema), schema)
        print(f"{len(package.files)} archivo(s) escritos en {args.salida}")
    except (PublicationError, OSError, KeyError, TypeError) as exc:
        message = str(exc)
        print(message if message.startswith("ERROR:") else f"ERROR: {message}", file=sys.stderr)
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
