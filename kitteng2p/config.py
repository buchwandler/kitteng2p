from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from .types import G2LexFileRef


def _file_refs(value: object) -> tuple[G2LexFileRef, ...]:
    if value is None:
        return ()
    values = (value,) if isinstance(value, (str, Path, G2LexFileRef, Mapping)) else value
    if not isinstance(values, Sequence):
        raise TypeError("g2lex_files must be a sequence of paths or G2LexFileRef values")
    refs: list[G2LexFileRef] = []
    for item in values:
        if isinstance(item, G2LexFileRef):
            refs.append(item)
        elif isinstance(item, (str, Path)):
            refs.append(G2LexFileRef(item))
        elif isinstance(item, Mapping):
            path = item.get("path")
            if not isinstance(path, (str, Path)):
                raise TypeError("each G2Lex file mapping must have a string or Path 'path'")
            refs.append(
                G2LexFileRef(
                    path=path,
                    sha256=item.get("sha256"),
                    logical_sha256=item.get("logical_sha256"),
                )
            )
        else:
            raise TypeError(
                "g2lex_files items must be paths, G2LexFileRef values, or path mappings"
            )
    return tuple(refs)


def _selectors(value: object) -> tuple[str, ...] | None:
    if value is None:
        return None
    values = (value,) if isinstance(value, str) else value
    if not isinstance(values, Sequence):
        raise TypeError("lexicons must be a selector or a sequence of selectors")
    result: list[str] = []
    seen: set[str] = set()
    for item in values:
        if not isinstance(item, str) or not item.strip():
            raise ValueError("lexicon selectors must be non-empty strings")
        selector = item.strip()
        key = selector.casefold()
        if key in seen:
            raise ValueError(f"duplicate lexicon selector: {selector!r}")
        seen.add(key)
        result.append(selector)
    return tuple(result)


@dataclass(frozen=True, slots=True)
class KittenG2PConfig:
    """Configure eSpeak and optional Kitten-compatible pronunciation sources.

    With no explicitly selected G2Lex sources the frontend retains its original
    whole-request eSpeak behavior. Named sources are provisioned only when they
    are selected and the policy is ``"auto"``.
    """

    language: str = "en-us"
    espeak_mode: str = "auto"
    executable: str | None = None
    library: str | None = None
    data: str | None = None
    timeout: float | None = None
    lexicons: tuple[str, ...] | None = None
    g2lex_files: tuple[G2LexFileRef, ...] = ()
    lexicon_data_policy: Literal["auto", "installed-only"] = "auto"
    heteronym_policy: Literal["auto", "off"] = "auto"

    def __post_init__(self) -> None:
        if self.espeak_mode not in {"auto", "native", "cli"}:
            raise ValueError("espeak_mode must be 'auto', 'native', or 'cli'")
        if not self.language.strip():
            raise ValueError("language cannot be empty")
        if self.timeout is not None and self.timeout <= 0:
            raise ValueError("timeout must be positive")
        if self.lexicon_data_policy not in {"auto", "installed-only"}:
            raise ValueError("lexicon_data_policy must be 'auto' or 'installed-only'")
        if self.heteronym_policy not in {"auto", "off"}:
            raise ValueError("heteronym_policy must be 'auto' or 'off'")

        lexicons = _selectors(self.lexicons)
        refs = _file_refs(self.g2lex_files)
        paths: set[str] = set()
        for ref in refs:
            key = str(Path(ref.path).expanduser().resolve()).casefold()
            if key in paths:
                raise ValueError(f"duplicate G2Lex file path: {ref.path}")
            paths.add(key)
        object.__setattr__(self, "lexicons", lexicons)
        object.__setattr__(self, "g2lex_files", refs)
