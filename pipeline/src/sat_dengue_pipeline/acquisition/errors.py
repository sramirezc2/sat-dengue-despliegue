"""Errores de adquisición con mensajes independientes de URLs y credenciales."""


class AcquisitionError(RuntimeError):
    """No fue posible resolver una entrada científica local verificable."""


class ManifestError(AcquisitionError, ValueError):
    """El manifiesto no cumple su esquema o invariantes."""


class UnknownProviderError(ManifestError):
    """La fábrica no dispone del proveedor solicitado."""


class MutableRevisionError(ManifestError):
    """La referencia no identifica una revisión inmutable."""


class SourceFileNotFoundError(AcquisitionError):
    """El archivo solicitado no existe en el origen local."""


class DownloadError(AcquisitionError):
    """La transferencia no pudo completarse."""


class IntegrityError(AcquisitionError):
    """El tamaño o SHA-256 no coincide con el manifiesto."""


class CacheError(AcquisitionError):
    """La caché no permite materializar el archivo de forma segura."""
