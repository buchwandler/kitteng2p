from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..errors import BackendUnavailableError, PhonemizationError


def _compose_clauses(values: Any) -> str:
    pieces: list[str] = []
    for value in values:
        phonemes = str(getattr(value, "phonemes", "") or "")
        terminator = getattr(value, "terminator", None)
        if phonemes:
            pieces.append(phonemes)
        if terminator:
            pieces.append(str(terminator))
    return " ".join(piece for piece in pieces if piece)


@dataclass
class EspeakBackend:
    """Thin Kitten-specific wrapper around the shared espeakng-runtime package."""

    mode: str = "auto"
    executable: str | None = None
    library: str | None = None
    data: str | None = None
    timeout: float | None = None

    def __post_init__(self) -> None:
        if self.mode not in {"auto", "native", "cli"}:
            raise ValueError("mode must be 'auto', 'native', or 'cli'")
        try:
            from espeakng_runtime import EspeakRuntime
        except ModuleNotFoundError as exc:
            raise BackendUnavailableError(
                "espeakng-runtime is required for the default Kitten backend"
            ) from exc
        try:
            self._runtime = EspeakRuntime(
                mode=self.mode,
                executable=self.executable,
                library=self.library,
                data=self.data,
                timeout=self.timeout,
            )
        except Exception as exc:
            raise BackendUnavailableError(str(exc)) from exc

    @property
    def diagnostics(self) -> object:
        return self._runtime.info

    def phonemize(self, text: str, *, language: str) -> str:
        if not text:
            return ""
        try:
            # clauses() preserves common source terminators while the Kitten codec later
            # performs the same regex tokenization used by upstream v0.8.
            values = self._runtime.clauses(text, voice=language)
            rendered = _compose_clauses(values)
            if rendered:
                return rendered
            return str(self._runtime.phonemize(text, voice=language))
        except Exception as exc:
            raise PhonemizationError(str(exc)) from exc

    def close(self) -> None:
        self._runtime.close()

    def __enter__(self) -> EspeakBackend:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
