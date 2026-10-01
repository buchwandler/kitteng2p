from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CodecResult:
    phonemes: str
    ids: tuple[int, ...]
    dropped_symbols: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class PhonemizeResult:
    text: str
    raw_phonemes: str
    phonemes: str
    token_ids: tuple[int, ...]
    language: str
    dropped_symbols: tuple[str, ...] = ()

    @property
    def ids(self) -> tuple[int, ...]:
        return self.token_ids
