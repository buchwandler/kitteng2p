from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class KittenG2PConfig:
    language: str = "en-us"
    espeak_mode: str = "auto"
    executable: str | None = None
    library: str | None = None
    data: str | None = None
    timeout: float | None = None

    def __post_init__(self) -> None:
        if self.espeak_mode not in {"auto", "native", "cli"}:
            raise ValueError("espeak_mode must be 'auto', 'native', or 'cli'")
        if not self.language.strip():
            raise ValueError("language cannot be empty")
        if self.timeout is not None and self.timeout <= 0:
            raise ValueError("timeout must be positive")
