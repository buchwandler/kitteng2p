class KittenG2PError(Exception):
    """Base error for kitteng2p."""


class BackendUnavailableError(KittenG2PError, RuntimeError):
    """Raised when eSpeak cannot be initialized."""


class PhonemizationError(KittenG2PError, RuntimeError):
    """Raised when the backend cannot phonemize input."""
