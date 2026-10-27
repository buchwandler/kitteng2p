from __future__ import annotations

import hashlib
import os
import re
import threading
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import g2lex
from g2lex import TaggedValue
from lexphon import DataStore
from lexphon.catalog import Catalog, CatalogArtifact, load_catalog

from .types import G2LexFileInspection, G2LexFileRef, LexiconDiscoveryResult, NamedLexiconInfo

_IPA_ENCODING = "ipa"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_CATALOG_LOCK = threading.Lock()
_CATALOG_CACHE: Catalog | None = None


def _language(value: str) -> str:
    return value.strip().casefold().replace("_", "-")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _normalize_pin(value: str | None, label: str) -> str | None:
    if value is None:
        return None
    normalized = value.strip().casefold().removeprefix("sha256:")
    if not _SHA256_RE.fullmatch(normalized):
        raise ValueError(f"{label} must be a 64-character SHA-256 hex digest")
    return normalized


def _manifest_metadata(metadata: Mapping[str, Any]) -> tuple[str | None, str | None, str | None]:
    source = metadata.get("source")
    source = source if isinstance(source, Mapping) else {}
    language = metadata.get("language") or metadata.get("locale")
    language = language or source.get("language") or source.get("locale")
    encoding = metadata.get("phoneme_encoding") or metadata.get("pronunciation_alphabet")
    encoding = encoding or source.get("phoneme_encoding") or source.get("pronunciation_alphabet")
    display_name = (
        metadata.get("display_name") or metadata.get("name") or source.get("display_name")
    )
    return (
        str(language).strip() if isinstance(language, str) and language.strip() else None,
        str(encoding).strip().casefold()
        if isinstance(encoding, str) and encoding.strip()
        else None,
        str(display_name).strip()
        if isinstance(display_name, str) and display_name.strip()
        else None,
    )


def inspect_g2lex_file(path: str | Path) -> G2LexFileInspection:
    """Inspect a local G2Lex file without registering or installing it."""
    raw_path = Path(path).expanduser()
    try:
        canonical = raw_path.resolve(strict=True)
        if not canonical.is_file():
            raise ValueError("path is not a regular file")
        content_hash = _sha256(canonical)
        with g2lex.open(canonical) as lexicon:
            metadata = dict(lexicon.metadata)
            language, encoding, display_name = _manifest_metadata(metadata)
            logical_hash = metadata.get("logical_sha256")
            if not isinstance(logical_hash, str) or not logical_hash:
                logical_hash = g2lex.logical_sha256(lexicon)
            compatible = encoding == _IPA_ENCODING
            reason = (
                None
                if compatible
                else (f"Kitten requires phoneme encoding 'ipa'; file declares {encoding!r}.")
            )
            if language is None:
                reason = "G2Lex file has no language/locale metadata."
                compatible = False
            return G2LexFileInspection(
                valid=True,
                path=str(canonical),
                sha256=content_hash,
                logical_sha256=str(logical_hash),
                entry_count=len(lexicon),
                language=language,
                phoneme_encoding=encoding,
                display_name=display_name,
                compatible=compatible,
                reason=reason,
                metadata=metadata,
            )
    except Exception as exc:
        try:
            shown_path = str(raw_path.resolve())
        except OSError:
            shown_path = str(raw_path)
        return G2LexFileInspection(
            valid=False,
            path=shown_path,
            sha256=None,
            logical_sha256=None,
            entry_count=0,
            language=None,
            phoneme_encoding=None,
            display_name=None,
            compatible=False,
            reason=f"Invalid G2Lex file {shown_path}: {exc}",
            metadata={},
        )


def _get_catalog(*, offline: bool, refresh: bool) -> Catalog:
    global _CATALOG_CACHE
    with _CATALOG_LOCK:
        if _CATALOG_CACHE is not None and not refresh:
            return _CATALOG_CACHE
        if offline:
            location = os.environ.get("LEXPHON_CATALOG_URL")
            if location and not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", location):
                catalog = load_catalog(location)
                _CATALOG_CACHE = catalog
                return catalog
            if _CATALOG_CACHE is None:
                raise RuntimeError(
                    "No Lexphon catalog is cached for offline discovery; run discovery online "
                    "once or set LEXPHON_CATALOG_URL to a local catalog file."
                )
            return _CATALOG_CACHE
        catalog = load_catalog()
        _CATALOG_CACHE = catalog
        return catalog


def _installed_ids(store: DataStore) -> set[str]:
    return {
        str(item.get("id"))
        for item in store.installed()
        if isinstance(item, Mapping) and item.get("id") is not None
    }


def _named_info(artifact: CatalogArtifact, installed: set[str]) -> NamedLexiconInfo:
    compatible = artifact.kind == "pronunciation" and artifact.phoneme_encoding == _IPA_ENCODING
    reason = (
        None
        if compatible
        else (
            f"Kitten requires a pronunciation lexicon encoded as IPA; this asset uses "
            f"{artifact.phoneme_encoding!r} ({artifact.kind})."
        )
    )
    asset_id = artifact.asset.get("id") or artifact.asset.get("name")
    return NamedLexiconInfo(
        selector=artifact.name,
        id=artifact.id,
        language=artifact.language,
        display_name=artifact.display_name,
        default=bool(artifact.manifest.get("default", False)),
        installed=artifact.id in installed,
        phoneme_encoding=artifact.phoneme_encoding,
        backend=str(artifact.manifest.get("backend", "lexphon")),
        asset_id=str(asset_id) if asset_id is not None else artifact.id,
        data_version=artifact.data_version,
        logical_sha256=(
            str(artifact.asset["logical_sha256"])
            if artifact.asset.get("logical_sha256") is not None
            else None
        ),
        content_sha256=str(artifact.asset["sha256"]),
        model_support=compatible,
        compatibility_reason=reason,
    )


def discover_lexicons(
    language: str = "en-us",
    *,
    offline: bool = False,
    refresh: bool = False,
    preference: str = "auto",
) -> LexiconDiscoveryResult:
    """List catalog sources and installed state without installing any assets."""
    if not isinstance(language, str) or not language.strip():
        raise ValueError("language must be a non-empty string")
    if preference not in {"auto", "catalog", "installed-first"}:
        raise ValueError("preference must be 'auto', 'catalog', or 'installed-first'")
    catalog = _get_catalog(offline=offline, refresh=refresh)
    store = DataStore()
    installed = _installed_ids(store)
    entries = tuple(
        _named_info(item, installed)
        for item in catalog.for_language(_language(language))
        if item.kind in {"pronunciation", "membership"}
    )
    if preference == "installed-first":
        entries = tuple(sorted(entries, key=lambda item: (not item.installed, item.selector)))
    return LexiconDiscoveryResult(language=_language(language), entries=entries)


@dataclass(slots=True)
class LoadedLexiconSource:
    """An opened, validated G2Lex source and its stable provenance."""

    selector: str
    source_type: str
    handle: Any
    language: str
    phoneme_encoding: str
    source_name: str
    source_path: str | None
    content_sha256: str
    logical_sha256: str
    asset_id: str | None = None
    data_version: str | None = None

    def close(self) -> None:
        close = getattr(self.handle, "close", None)
        if close is not None:
            close()

    def lookup(self, word: str, selectors: Sequence[str]) -> tuple[str, str | None] | None:
        try:
            value = self.handle.get(word)
        except AttributeError:
            value = self.handle[word] if word in self.handle else None
        if value is None:
            return None
        if isinstance(value, TaggedValue) or isinstance(value, Mapping):
            pairs = value.items if isinstance(value, TaggedValue) else tuple(value.items())
            values = {str(tag).casefold(): pronunciation for tag, pronunciation in pairs}
            for selector in selectors:
                pronunciation = values.get(selector.casefold())
                selected = _first(pronunciation)
                if selected:
                    return selected, selector
            return None
        selected = _first(value)
        return (selected, None) if selected else None


def _first(value: object) -> str | None:
    if isinstance(value, str):
        return value or None
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for item in value:
            if isinstance(item, str) and item:
                return item
    return None


def _open_checked(
    path: Path,
    requested_language: str,
    *,
    expected_encoding: str | None = None,
) -> tuple[Any, str, str, str]:
    try:
        handle = g2lex.open(path)
    except Exception as exc:
        raise ValueError(f"Invalid G2Lex file {path}: {exc}") from exc
    try:
        metadata = handle.metadata
        language, encoding, _display_name = _manifest_metadata(metadata)
        if language is None:
            raise ValueError(f"G2Lex file {path} has no language/locale metadata")
        if _language(language) != _language(requested_language):
            raise ValueError(
                f"G2Lex language metadata conflicts with the request: file is {language}, "
                f"request is {requested_language}"
            )
        if encoding != _IPA_ENCODING:
            raise ValueError(
                f"Kitten requires compatible IPA pronunciation data; G2Lex file {path} "
                f"declares encoding {encoding!r}"
            )
        if expected_encoding is not None and encoding != expected_encoding.casefold():
            raise ValueError(
                f"G2Lex encoding {encoding!r} does not match catalog encoding {expected_encoding!r}"
            )
        logical = metadata.get("logical_sha256")
        if not isinstance(logical, str) or not logical:
            logical = g2lex.logical_sha256(handle)
        return handle, language, encoding, str(logical)
    except Exception:
        handle.close()
        raise


def open_g2lex_sources(
    language: str,
    local_files: Sequence[G2LexFileRef],
    lexicons: Sequence[str] | None,
    data_policy: str,
) -> tuple[LoadedLexiconSource, ...]:
    """Open validated local files followed by selected named catalog sources."""
    loaded: list[LoadedLexiconSource] = []
    try:
        for ref in local_files:
            raw_path = Path(ref.path).expanduser()
            try:
                path = raw_path.resolve(strict=True)
            except FileNotFoundError as exc:
                raise FileNotFoundError(
                    f"Configured Kitten G2Lex file does not exist: {raw_path}\n"
                    "Re-bind the profile with --g2lex PATH."
                ) from exc
            if not path.is_file():
                raise ValueError(f"Configured Kitten G2Lex path is not a file: {path}")
            content_hash = _sha256(path)
            expected_hash = _normalize_pin(ref.sha256, "G2Lex content SHA-256 pin")
            if expected_hash is not None and content_hash != expected_hash:
                raise ValueError(
                    "Configured Kitten G2Lex file changed after it was selected.\n"
                    f"  path:     {path}\n  expected: {expected_hash}\n"
                    f"  actual:   {content_hash}\n"
                    "Re-bind or refresh the profile to accept the new content."
                )
            handle, source_language, encoding, logical_hash = _open_checked(path, language)
            expected_logical = _normalize_pin(ref.logical_sha256, "G2Lex logical SHA-256 pin")
            if expected_logical is not None and logical_hash != expected_logical:
                handle.close()
                raise ValueError(
                    "Configured Kitten G2Lex logical hash does not match its pin.\n"
                    f"  path:     {path}\n  expected: {expected_logical}\n"
                    f"  actual:   {logical_hash}"
                )
            if _sha256(path) != content_hash:
                handle.close()
                raise ValueError(f"G2Lex file changed while it was being opened: {path}")
            metadata = handle.metadata
            source_name = str(metadata.get("display_name") or metadata.get("name") or path.name)
            loaded.append(
                LoadedLexiconSource(
                    selector=source_name,
                    source_type="local-g2lex",
                    handle=handle,
                    language=source_language,
                    phoneme_encoding=encoding,
                    source_name=str(path),
                    source_path=str(path),
                    content_sha256=content_hash,
                    logical_sha256=logical_hash,
                    asset_id=None,
                )
            )

        if lexicons:
            catalog = _get_catalog(offline=False, refresh=False)
            store = DataStore()
            artifacts = catalog.for_language(_language(language))
            installed = _installed_ids(store)
            used_ids: set[str] = set()
            for selector in lexicons:
                matches = tuple(
                    artifact
                    for artifact in artifacts
                    if selector.casefold()
                    in {
                        artifact.name.casefold(),
                        artifact.id.casefold(),
                        artifact.id.split(":", 1)[-1].casefold(),
                    }
                )
                if not matches:
                    available = ", ".join(sorted(item.name for item in artifacts)) or "none"
                    raise ValueError(
                        f"Kitten lexicon {selector!r} is not available for {language}.\n"
                        f"Available selectors: {available}\n"
                        "Run: voicerender lexicons list --engine kitten --lang " + language
                    )
                if len(matches) != 1:
                    raise ValueError(f"Kitten lexicon selector {selector!r} is ambiguous")
                artifact = matches[0]
                if artifact.id in used_ids:
                    raise ValueError(f"duplicate Kitten lexicon selector: {selector!r}")
                used_ids.add(artifact.id)
                if artifact.kind != "pronunciation" or artifact.phoneme_encoding != _IPA_ENCODING:
                    raise ValueError(
                        f"Kitten cannot use lexicon {artifact.id!r}: phoneme encoding "
                        f"{artifact.phoneme_encoding!r} is not supported. Kitten requires a "
                        "compatible IPA pronunciation source."
                    )
                if artifact.id in installed:
                    path = store.path(artifact.id)
                elif data_policy == "installed-only":
                    raise ValueError(
                        f"Kitten lexicon {artifact.id!r} is not installed; "
                        "install it or use lexicon_data_policy='auto'."
                    )
                else:
                    path = store.install(artifact)
                actual_hash = _sha256(path)
                expected_asset_hash = str(artifact.asset["sha256"])
                if actual_hash != expected_asset_hash:
                    raise ValueError(
                        f"Installed Kitten lexicon {artifact.id!r} failed its content hash check"
                    )
                handle, source_language, encoding, logical_hash = _open_checked(
                    path, language, expected_encoding=artifact.phoneme_encoding
                )
                expected_logical = artifact.asset.get("logical_sha256")
                if expected_logical is not None and logical_hash != expected_logical:
                    handle.close()
                    raise ValueError(
                        f"Installed Kitten lexicon {artifact.id!r} failed its logical hash check"
                    )
                loaded.append(
                    LoadedLexiconSource(
                        selector=artifact.name,
                        source_type="named-g2lex",
                        handle=handle,
                        language=source_language,
                        phoneme_encoding=encoding,
                        source_name=artifact.id,
                        source_path=str(path),
                        content_sha256=actual_hash,
                        logical_sha256=logical_hash,
                        asset_id=artifact.id,
                        data_version=artifact.data_version,
                    )
                )
        return tuple(loaded)
    except Exception:
        for source in reversed(loaded):
            source.close()
        raise


__all__ = ["discover_lexicons", "inspect_g2lex_file"]
