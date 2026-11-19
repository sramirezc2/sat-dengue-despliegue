"""Exportar a `datos/panel/` el panel municipio-mes que sustenta el informe.

Por que existe
--------------

La rubrica del despliegue exige una carpeta `Datos/` con «muestras o estructura
de los datos usados». Los crudos no pueden ir: `dengue.csv` pesa 875 MB, es
microdato de notificacion individual y vive en un release privado de Hugging
Face. Lo que si puede ir, y es lo que de verdad usa el proyecto, es el panel
canonico: agregados municipio-mes de Meta y Tolima, 2007-2024.

Publicar ese panel es lo que permite que un tercero reproduzca el resultado
principal del articulo sin credenciales y sin reconstruir nada: el cuaderno
`notebooks/01-resultado-principal.ipynb` lo lee, lo cruza con las predicciones
versionadas y vuelve a calcular la Tabla 2.

Que escribe
-----------

- `datos/panel/panel_meta_tolima.csv`: las filas de los departamentos 50 y 73,
  con todas las columnas del esquema canonico y en su orden.
- `datos/panel/esquema.json`: el esquema que produjo el constructor canonico
  (nombre, dtype, nulabilidad, rol y origen de cada columna), mas la huella
  semantica del artefacto del que salio y el rango de periodos cubierto.

El esquema se copia del artefacto, no se escribe a mano: asi el CSV publicado y
su descripcion no pueden separarse.

Garantia
--------

El artefacto esta direccionado por contenido. Este script exige la huella
semantica esperada como argumento y `verify_artifact` comprueba ademas el
sha256 de los bytes, de modo que no puede exportar en silencio un panel que no
sea el declarado en el informe.

Uso
---

    uv run --locked --directory pipeline python tools/exportar_entregable.py RUTA HUELLA

donde RUTA es el `canonical.json` del artefacto y HUELLA su huella semantica.

Desde la raiz del repositorio, con el interprete del proyecto.
"""

import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

#: Departamentos del estudio: Meta (50) y Tolima (73).
DEPARTAMENTOS = ("50", "73")

#: Destino, relativo a la raiz del repositorio.
DESTINO = Path("datos") / "panel"


def leer_panel(carpeta: Path) -> tuple[pd.DataFrame, dict]:
    """Releer el panel exportado restaurando los tipos que el CSV no conserva.

    Vive aqui, junto al escritor, para que el formato tenga una sola definicion:
    los cuadernos de `notebooks/` importan esta funcion en vez de repetir la
    restauracion por su cuenta.

    Args:
        carpeta: Directorio con `panel_meta_tolima.csv` y `esquema.json`.

    Returns:
        El panel con los dtypes del esquema y el esquema leido.

    Raises:
        ValueError: Si el CSV no trae las filas que el esquema declara.

    """
    esquema = json.loads((carpeta / "esquema.json").read_text(encoding="utf-8"))
    panel = pd.read_csv(carpeta / "panel_meta_tolima.csv", dtype=object)
    for columna in esquema["columns"]:
        serie = panel[columna["name"]]
        if "bool" in columna["dtype"]:
            # El CSV guarda los booleanos como las cadenas "True" y "False", y
            # `astype("boolean")` sobre texto falla con "Need to pass bool-like
            # values". Se mapean antes; cualquier otro valor queda nulo y el
            # chequeo de filas de mas abajo no lo tapa, porque cuenta filas.
            serie = serie.map({"True": True, "False": False})
        panel[columna["name"]] = serie.astype(columna["dtype"])
    if len(panel) != esquema["panel"]["filas"]:
        raise ValueError("El CSV no trae las filas que declara el esquema")
    return panel, esquema


def exportar(ruta: Path, huella: str, destino: Path) -> dict:
    """Verificar el artefacto, recortarlo al estudio y escribir CSV y esquema.

    Args:
        ruta: Archivo `canonical.json` producido por el constructor canonico.
        huella: Huella semantica esperada del artefacto.
        destino: Carpeta donde se escriben el CSV y el esquema.

    Returns:
        El resumen que se imprime, para que la prueba pueda revisarlo.

    Raises:
        ValueError: Si el artefacto no es el declarado, si el recorte queda
            vacio o si el CSV no vuelve a leerse con las mismas dimensiones.

    """
    # El cargador canonico se importa aqui y no arriba a proposito: `leer_panel`
    # solo necesita pandas, y los cuadernos de `notebooks/` la importan de este
    # modulo. Si la cadena de adquisicion se importara al cargar el archivo, leer
    # un CSV exigiria el paquete entero y el interprete exacto del pipeline.
    from sat_dengue_pipeline.raw.serialization import CanonicalArtifact, load_canonical

    artefacto = CanonicalArtifact(
        ruta, huella, hashlib.sha256(ruta.read_bytes()).hexdigest()
    )
    tabla, esquema = load_canonical(artefacto)
    recorte = tabla[tabla.department_code.isin(DEPARTAMENTOS)].reset_index(drop=True)
    if recorte.empty:
        raise ValueError("El recorte de Meta y Tolima quedo vacio")

    destino.mkdir(parents=True, exist_ok=True)
    csv = destino / "panel_meta_tolima.csv"
    # `na_rep=""` deja los nulos como campo vacio y no como la cadena "nan": el
    # esquema dice que dtype restaurar y el cuaderno lo usa al releer.
    recorte.to_csv(csv, index=False, na_rep="")

    # Releer antes de declarar el exito. Un CSV que no vuelve con las mismas
    # dimensiones no sirve de entregable aunque se haya escrito sin error.
    vuelta = pd.read_csv(csv, dtype={"municipality_code": str, "year_month": str})
    if vuelta.shape != recorte.shape or list(vuelta) != list(recorte):
        raise ValueError("El CSV escrito no vuelve a leerse con la misma forma")

    resumen = {
        "huella_semantica": huella,
        "departamentos": list(DEPARTAMENTOS),
        "municipios": int(recorte.municipality_code.nunique()),
        "filas": int(len(recorte)),
        "columnas": int(len(recorte.columns)),
        "periodo_inicial": str(recorte.year_month.min()),
        "periodo_final": str(recorte.year_month.max()),
    }
    (destino / "esquema.json").write_text(
        json.dumps(
            {"panel": resumen, **esquema}, ensure_ascii=False, indent=2, sort_keys=False
        )
        + "\n",
        encoding="utf-8",
    )
    return resumen


def main() -> None:
    """Exportar el panel y describir lo escrito."""
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    ruta, huella = Path(sys.argv[1]), sys.argv[2]
    raiz = Path(__file__).resolve().parents[2]
    resumen = exportar(ruta, huella, raiz / DESTINO)
    print(f"panel verificado: {huella[:16]}…")
    print(
        f"  {resumen['filas']} filas | {resumen['municipios']} municipios"
        f" | {resumen['columnas']} columnas"
        f" | {resumen['periodo_inicial']} a {resumen['periodo_final']}"
    )
    print(f"  escrito en {DESTINO}/panel_meta_tolima.csv y {DESTINO}/esquema.json")


if __name__ == "__main__":
    main()
