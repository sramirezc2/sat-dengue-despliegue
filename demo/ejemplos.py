"""Notificaciones artificiales reproducibles para ambas descargas, sin desenlaces reales."""

import csv
import io

from sat_dengue_pipeline.domain.calendar import validate_period

HEADERS = ("COD_DPTO_R", "COD_MUN_R", "INI_SIN", "COD_EVE")
SAMPLE_FILENAME = "muestra-artificial.csv"


def sample_csv(month: str) -> bytes:
    """Generar 24 registros inventados de ambos eventos y departamentos.

    Los códigos territoriales son del catálogo; fechas y conteos son artificiales
    y no representan observaciones ni desenlaces de ningún año.
    """
    validate_period(month)
    stream = io.StringIO()
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(HEADERS)
    for code in ("50001", "50006", "50110", "73001", "73024", "73026"):
        for day, event in ((1, 210), (9, 220), (18, 210), (28, 210)):
            writer.writerow([code[:2], code[2:], f"{month}-{day:02d}", event])
    return stream.getvalue().encode()
