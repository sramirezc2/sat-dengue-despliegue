"""Certificar tres materializaciones en procesos aislados; solo bajo autorización."""

import subprocess
import sys
import uuid

from sat_dengue_pipeline.models.logistic import canonical_json
from sat_dengue_pipeline.pipelines.deployment_publication.contract import decode_json

from .configuration import ROOT, local_path, sha


def certify(*, synthetic: bool = False) -> dict:
    """Ejecutar N=3 por la entrada Kedro normal, sin promover ningún documento.

    Args:
        synthetic: Solo fuentes artificiales explícitas; no acredita datos reales.

    Returns:
        Identidad del certificado y rutas relativas de artefacto/recibo.
    """
    workspace = local_path("data/risk-2025/certifications/" + uuid.uuid4().hex)
    workspace.mkdir(parents=True, exist_ok=False)
    relative = workspace.relative_to(ROOT / "pipeline").as_posix()
    runs = []
    for index in range(1, 4):
        params = ",".join(
            [
                "risk_2025.mode=materialize",
                "risk_2025.source=" + ("synthetic" if synthetic else "approved"),
                f"risk_2025.artifact_directory={relative}/model-{index}",
                f"risk_2025.run_directory={relative}/run-{index}",
            ]
        )
        process = subprocess.run(
            [
                sys.executable,
                "-m",
                "kedro",
                "run",
                "--pipeline",
                "risk_2025_publication",
                "--params",
                params,
            ],
            cwd=ROOT / "pipeline",
            capture_output=True,
            check=False,
        )
        if process.returncode:
            # Los nodos conservan su terminal sanitizado. No escribir excepciones SDK.
            (workspace / "failure.json").write_bytes(
                canonical_json(
                    {
                        "status": "FAILED",
                        "run": index,
                        "returncode": process.returncode,
                    }
                )
            )
            raise ValueError("Materialización fallida; se conserva el intento sin reintentar")
        receipt = decode_json((workspace / f"run-{index}/receipt.json").read_bytes())
        if receipt["status"] != "MATERIALIZED_NOT_PUBLISHED":
            raise ValueError("Materialización incompleta")
        runs.append({k: receipt[k] for k in ("execution_id", "artifact_sha256", "package_sha256")})
    if (
        len({r["artifact_sha256"] for r in runs}) != 1
        or len({r["package_sha256"] for r in runs}) != 1
    ):
        (workspace / "failure.json").write_bytes(
            canonical_json({"status": "DIVERGENT", "runs": runs})
        )
        raise ValueError("N=3 divergente; ninguna publicación autorizada")
    certificate = {
        "status": "CERTIFIED_N3",
        "artifact_sha256": runs[0]["artifact_sha256"],
        "package_sha256": runs[0]["package_sha256"],
        "runs": runs,
    }
    raw = canonical_json(certificate)
    with (workspace / "certification.json").open("xb") as stream:
        stream.write(raw)
    return {
        "certificate": f"{relative}/certification.json",
        "certificate_sha256": sha(raw),
        "artifact_directory": f"{relative}/model-1",
        **certificate,
    }
