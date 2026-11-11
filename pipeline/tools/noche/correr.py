"""Correr el nodo del retroanálisis sobre el panel canónico ya construido, sin reconstruirlo.

Es el mismo nodo que llama `kedro run --pipelines retroanalisis`; solo se salta la
reconstrucción del panel (unos 16 minutos) usando el artefacto aprobado que ya está en
disco. El digest semántico del panel se verifica contra el certificado del release.
Uso: python tools/noche/correr.py <parameters_retroanalisis.yml> [clave=valor ...]
"""

import hashlib
import sys
from pathlib import Path

import yaml

from sat_dengue_pipeline.pipelines.retroanalisis.nodes import retroanalisis
from sat_dengue_pipeline.raw.serialization import CanonicalArtifact

CERTIFICADO = "de49b11bad43c35983a098ead2faa149d4e744da4172432aecdaadd828c73158"
params = yaml.safe_load(Path(sys.argv[1]).read_text(encoding="utf-8"))["retroanalisis"]
for extra in sys.argv[2:]:
    clave, valor = extra.split("=", 1)
    params[clave] = yaml.safe_load(valor)
p = Path(f"data/noche_panel/{CERTIFICADO}/canonical.json")
artefacto = CanonicalArtifact(p, p.parent.name, hashlib.sha256(p.read_bytes()).hexdigest())
retroanalisis(artefacto, params)
print("FIN", params["salida"])
