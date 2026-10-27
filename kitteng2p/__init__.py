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
from .lexicons import discover_lexicons, inspect_g2lex_file
from .types import (
    G2LexFileInspection,
    G2LexFileRef,
    LexiconDiscoveryResult,
    LinguisticToken,
    NamedLexiconInfo,
    PhonemizeResult,
    PronunciationDiagnostic,
    PronunciationOverride,
    PronunciationTrace,
)

try:
    __version__ = _distribution_version("kitteng2p")
except PackageNotFoundError:
    __version__ = "0+unknown"

__all__ = [
    "__version__",
    "BackendUnavailableError",
    "FRAME_PREFIX_ID",
    "FRAME_SUFFIX_IDS",
    "G2LexFileInspection",
    "G2LexFileRef",
    "KittenG2P",
    "KittenG2PConfig",
    "KittenG2PError",
    "LexiconDiscoveryResult",
    "LinguisticToken",
    "NamedLexiconInfo",
    "PhonemizationError",
    "PhonemizeResult",
    "PronunciationDiagnostic",
    "PronunciationOverride",
    "PronunciationTrace",
    "SYMBOLS",
    "basic_english_tokenize",
    "discover_lexicons",
    "encode_phonemes",
    "frame_token_ids",
    "get_g2p",
    "inspect_g2lex_file",
    "phoneme_ids",
    "phonemes",
    "phonemize_prepared",
    "prepare_phoneme_text",
]
