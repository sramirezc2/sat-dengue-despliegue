"""Excepciones del publicador; únicamente la frontera CLI decide códigos de salida."""


class PublicationError(ValueError):
    """La publicación no puede construirse o promoverse de forma válida."""


class PublicationInputError(PublicationError):
    """Las entradas calculadas incumplen su contrato local."""


class PublicationContractError(PublicationError):
    """El conjunto de salida viola nombres, integridad o contrato del producto."""


class PublicationTransactionError(PublicationError):
    """La promoción falló; el recibo de éxito no se emite."""
