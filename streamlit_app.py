"""Entrada de Community Cloud con dependencias instaladas desde la raíz."""

import json
import os
import runpy
import sys
from pathlib import Path

DEMO = Path(__file__).resolve().parent / "demo"
sys.path.insert(0, str(DEMO))
release = json.loads((DEMO / "context-release.json").read_text(encoding="utf-8"))
for variable, field in {
    "SATD_DEMO_HF_REPO_ID": "repo_id",
    "SATD_DEMO_HF_REVISION": "revision",
    "SATD_DEMO_HF_FILENAME": "filename",
    "SATD_DEMO_CONTEXT_BUNDLE_SHA256": "sha256",
}.items():
    os.environ.setdefault(variable, release[field])
runpy.run_path(str(DEMO / "app.py"), run_name="__main__")
