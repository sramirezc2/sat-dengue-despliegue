"""Integración externa Pydantic/Zod; no forma parte del código productivo del pipeline."""

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path


def main() -> None:
    """Contrastar nombres, snapshot y todos los JSON indicados con consumidores reales."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, action="append", required=True)
    parser.add_argument("--api-python", type=Path, default=Path(sys.executable))
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[2]
    contract = repo / "pipeline/src/sat_dengue_pipeline/pipelines/deployment_publication"
    receipt = json.loads((contract / "schema_receipt.json").read_bytes())
    source = repo / receipt["source_path"]
    assert hashlib.sha256(source.read_bytes()).hexdigest() == receipt["source_sha256"], (
        "Contract source drift"
    )
    documents = []
    for directory in args.directory:
        paths = sorted(directory.glob("*.json"))
        assert paths, f"No result JSON in {directory}"
        for path in paths:
            data = path.read_text(encoding="utf-8")
            document = json.loads(data)
            department = document["department"]["department_code"]
            period = document["department"]["requested_period"]
            assert path.name == f"resultado_{department}_{period}.json", path.name
            documents.append(data)
    api_code = """
import json,runpy,sys
model=runpy.run_path(sys.argv[1])['DashboardResponse']
payload=json.load(sys.stdin)
assert model.model_json_schema()==payload['schema'], 'Contract snapshot drift'
for data in payload['documents']: model.model_validate_json(data)
print(f"Pydantic: {len(payload['documents'])} documents valid")
"""
    subprocess.run(
        [str(args.api_python.absolute()), "-c", api_code, str(source)],
        input=json.dumps(
            {
                "schema": json.loads((contract / "dashboard.schema.json").read_bytes()),
                "documents": documents,
            }
        ),
        text=True,
        check=True,
    )
    zod_code = """
import {readFileSync} from "node:fs";
import {dashboardResponseSchema} from "./src/lib/dashboard-contract.ts";
const documents=JSON.parse(readFileSync(0,"utf8"));
for(const data of documents) dashboardResponseSchema.parse(JSON.parse(data));
console.log(`Zod: ${documents.length} documents valid`);
"""
    subprocess.run(
        ["bun", "--eval", zod_code],
        input=json.dumps(documents),
        text=True,
        cwd=repo / "app/dashboard",
        check=True,
    )


if __name__ == "__main__":
    main()
