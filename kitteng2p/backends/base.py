from __future__ import annotations

from typing import Protocol


class PhonemeBackend(Protocol):
    def phonemize(self, text: str, *, language: str) -> str: ...
    def close(self) -> None: ...
