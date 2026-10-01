from __future__ import annotations

from dataclasses import dataclass


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

    @property
    def ids(self) -> tuple[int, ...]:
        """Alias for the framed ``token_ids`` tuple."""
        return self.token_ids
