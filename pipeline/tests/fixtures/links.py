"""Cobertura de guards aun sin el privilegio Windows de crear symlinks."""

import errno
from pathlib import Path


class TestLinks:
    """Crear enlaces nativos o dobles limitados a rutas temporales de la prueba."""

    __test__ = False

    def __init__(self, monkeypatch, root: Path):
        """Conservar la semántica nativa fuera de los enlaces registrados."""
        self.root = root.absolute()
        self.links: dict[Path, Path] = {}
        original_is_link, original_resolve = Path.is_symlink, Path.resolve

        def is_link(path):
            """Reconocer un doble solo mientras exista su marcador temporal."""
            return (path.absolute() in self.links and path.exists()) or original_is_link(path)

        def resolve(path, strict=False):
            """Resolver únicamente prefijos que pertenecen al doble controlado."""
            absolute = path.absolute()
            for prefix in (absolute, *absolute.parents):
                if prefix in self.links and prefix.exists():
                    return original_resolve(
                        self.links[prefix] / absolute.relative_to(prefix), strict
                    )
            return original_resolve(path, strict)

        monkeypatch.setattr(Path, "is_symlink", is_link)
        monkeypatch.setattr(Path, "resolve", resolve)

    def __call__(self, path: Path, target: Path, target_is_directory: bool = False) -> None:
        """Intentar enlace real y mantener cobertura ante falta explícita de privilegios."""
        try:
            path.symlink_to(target, target_is_directory=target_is_directory)
        except OSError as error:
            if (
                error.errno not in {errno.EPERM, errno.EACCES, errno.ENOTSUP}
                and getattr(error, "winerror", None) != 1314
            ):
                raise
            if not path.absolute().is_relative_to(self.root):
                raise ValueError("El doble solo puede vivir en el tmp_path de la prueba") from error
            path.write_bytes(b"controlled symlink test double")
            self.links[path.absolute()] = target.absolute()
