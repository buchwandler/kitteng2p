"""Independent KittenTTS G2P/token-ID frontend."""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _distribution_version

from .api import KittenG2P, get_g2p, phoneme_ids, phonemes, phonemize_prepared
from .codec import (
    FRAME_PREFIX_ID,
    FRAME_SUFFIX_IDS,
    SYMBOLS,
    basic_english_tokenize,
    encode_phonemes,
    frame_token_ids,
    prepare_phoneme_text,
)
from .config import KittenG2PConfig
from .errors import BackendUnavailableError, KittenG2PError, PhonemizationError
from .types import PhonemizeResult

try:
    __version__ = _distribution_version("kitteng2p")
except PackageNotFoundError:
    __version__ = "0+unknown"

__all__ = [
    "__version__",
    "BackendUnavailableError",
    "FRAME_PREFIX_ID",
    "FRAME_SUFFIX_IDS",
    "KittenG2P",
    "KittenG2PConfig",
    "KittenG2PError",
    "PhonemizationError",
    "PhonemizeResult",
    "SYMBOLS",
    "basic_english_tokenize",
    "encode_phonemes",
    "frame_token_ids",
    "get_g2p",
    "phoneme_ids",
    "phonemes",
    "phonemize_prepared",
    "prepare_phoneme_text",
]
