"""Notificaciones artificiales reproducibles para ambas descargas, sin desenlaces reales."""

import csv
import io

from sat_dengue_pipeline.domain.calendar import validate_period

HEADERS = ("COD_DPTO_R", "COD_MUN_R", "INI_SIN", "COD_EVE")
SAMPLE_FILENAME = "muestra-artificial.csv"


def sample_csv(month: str) -> bytes:
    """Generar 55 registros inventados de ocho municipios y ambos eventos.

    Los códigos territoriales son del catálogo; fechas y conteos son artificiales
    y no representan observaciones ni desenlaces de ningún año.
    """
    validate_period(month)
    stream = io.StringIO()
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(HEADERS)
    for code, days, severe in (
        ("73030", (1, 4, 7, 10, 13, 16, 19, 22, 25, 28, 3, 6), 2),
        ("73854", (5, 8, 11, 14, 17, 20, 23, 26, 1, 4), 1),
        ("73043", (4, 7, 10, 13, 16, 19, 22, 25), 1),
        ("73870", (1, 4, 7, 10, 13, 16, 19), 1),
        ("73873", (4, 7, 10, 13, 16, 19), 1),
        ("73226", (7, 10, 13, 16, 19), 1),
        ("50245", (6, 9, 12, 15), 1),
        ("73352", (3, 6, 9), 0),
    ):
        for index, day in enumerate(days):
            event = 220 if index < severe else 210
            writer.writerow([code[:2], code[2:], f"{month}-{day:02d}", event])
    return stream.getvalue().encode()
