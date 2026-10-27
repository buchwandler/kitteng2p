from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Literal


@dataclass(frozen=True, slots=True)
class G2LexFileRef:
    path: str | Path
    sha256: str | None = None
    logical_sha256: str | None = None

    def __post_init__(self) -> None:
        if not str(self.path).strip():
            raise ValueError("G2Lex file path cannot be empty")
        for label, value in (("sha256", self.sha256), ("logical_sha256", self.logical_sha256)):
            if value is None:
                continue
            if not isinstance(value, str):
                raise TypeError(f"G2Lex {label} must be a string")
            normalized = value.strip().casefold().removeprefix("sha256:")
            if len(normalized) != 64:
                raise ValueError(f"G2Lex {label} must be a 64-character SHA-256 digest")
            try:
                int(normalized, 16)
            except ValueError as exc:
                raise ValueError(f"G2Lex {label} must be a hexadecimal SHA-256 digest") from exc
            object.__setattr__(self, label, normalized)


@dataclass(frozen=True, slots=True)
class LinguisticToken:
    start: int
    end: int
    text: str
    pos: str | None = None
    tag: str | None = None
    lemma: str | None = None
    morph: str | None = None
    language: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.start, int) or not isinstance(self.end, int):
            raise TypeError("linguistic token start/end offsets must be integers")
        if self.start < 0 or self.end <= self.start:
            raise ValueError("linguistic token span must satisfy 0 <= start < end")
        if not self.text:
            raise ValueError("linguistic token text cannot be empty")


@dataclass(frozen=True, slots=True)
class PronunciationOverride:
    start: int
    end: int
    phonemes: str
    language: str | None = None
    alphabet: str = "ipa"

    def __post_init__(self) -> None:
        if not isinstance(self.start, int) or not isinstance(self.end, int):
            raise TypeError("pronunciation override start/end offsets must be integers")
        if self.start < 0 or self.end <= self.start:
            raise ValueError("pronunciation override span must satisfy 0 <= start < end")
        if not isinstance(self.phonemes, str) or not self.phonemes.strip():
            raise ValueError("pronunciation override phonemes cannot be empty")
        if self.alphabet.casefold() != "ipa":
            raise ValueError("Kitten pronunciation overrides must use the 'ipa' alphabet")


@dataclass(frozen=True, slots=True)
class PronunciationTrace:
    text: str
    start: int
    end: int
    phonemes: str
    source: Literal["explicit", "local-g2lex", "named-g2lex", "context-rule", "espeak"]
    source_name: str | None = None
    sha256: str | None = None
    logical_sha256: str | None = None
    selector: str | None = None
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class PronunciationDiagnostic:
    code: str
    message: str
    severity: Literal["info", "warning", "error"] = "warning"


@dataclass(frozen=True, slots=True)
class NamedLexiconInfo:
    selector: str
    id: str
    language: str
    display_name: str
    default: bool
    installed: bool
    phoneme_encoding: str
    backend: str
    asset_id: str
    data_version: str
    logical_sha256: str | None
    content_sha256: str
    model_support: bool
    compatibility_reason: str | None = None


@dataclass(frozen=True, slots=True)
class LexiconDiscoveryResult:
    language: str
    entries: tuple[NamedLexiconInfo, ...]


@dataclass(frozen=True, slots=True)
class G2LexFileInspection:
    valid: bool
    path: str
    sha256: str | None
    logical_sha256: str | None
    entry_count: int
    language: str | None
    phoneme_encoding: str | None
    display_name: str | None
    compatible: bool
    reason: str | None
    metadata: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class CodecResult:
    phonemes: str
    ids: tuple[int, ...]
    dropped_symbols: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class PhonemizeResult:
    """Detailed result of phonemizing prepared text.

    Attributes
    ----------
    text:
        Input text passed to the backend.
    raw_phonemes:
        Direct backend output before Kitten token preparation.
    phonemes:
        Prepared phoneme string passed to the character encoder.
    token_ids:
        Character IDs framed as ``(0, *ids, 10, 0)``.
    language:
        eSpeak voice or language selector used for the request.
    dropped_symbols:
        Characters absent from the Kitten inventory, in encounter order.
    """

    text: str
    raw_phonemes: str
    phonemes: str
    token_ids: tuple[int, ...]
    language: str
    dropped_symbols: tuple[str, ...] = ()
    pronunciation_trace: tuple[PronunciationTrace, ...] = ()
    diagnostics: tuple[PronunciationDiagnostic, ...] = ()

    @property
    def ids(self) -> tuple[int, ...]:
        """Alias for the framed ``token_ids`` tuple."""
        return self.token_ids
