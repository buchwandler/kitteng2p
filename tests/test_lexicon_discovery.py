from __future__ import annotations

import hashlib
from pathlib import Path
from types import SimpleNamespace

import pytest
from g2lex.format import pack_typed

import kitteng2p.lexicons as lexicons_module
from kitteng2p import KittenG2P, KittenG2PConfig, discover_lexicons


class FakeBackend:
    def phonemize(self, text: str, *, language: str) -> str:
        return "fallback"

    def close(self) -> None:
        pass


class FakeCatalog:
    def __init__(self, artifacts):
        self.artifacts = tuple(artifacts)

    def for_language(self, language: str):
        key = language.casefold().replace("_", "-")
        return tuple(
            artifact
            for artifact in self.artifacts
            if artifact.language.casefold().replace("_", "-") == key
        )


def make_artifact(path: Path, name: str, *, encoding: str = "ipa"):
    language = "en-US"
    path.write_bytes(
        pack_typed(
            {"word": f"{name}ɪ"},
            metadata={"language": language, "phoneme_encoding": encoding},
        )
    )
    return SimpleNamespace(
        id=f"en-us:{name}",
        language=language,
        name=name,
        display_name=f"{name.title()} pronunciations",
        kind="pronunciation",
        phoneme_encoding=encoding,
        data_version="1.0.0",
        manifest={"default": name == "first"},
        asset={"sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "name": path.name},
        path=path,
    )


class FakeStore:
    instances = []
    current = None

    def __init__(self):
        self.instances.append(self)
        self.installs: list[str] = []
        self.paths = {item.id: item.path for item in self.current.artifacts}
        self.installed_ids: set[str] = set()

    def installed(self):
        return tuple({"id": item} for item in sorted(self.installed_ids))

    def path(self, identifier: str) -> Path:
        if identifier not in self.installed_ids:
            from lexphon import LexiconNotInstalledError

            raise LexiconNotInstalledError(identifier)
        return self.paths[identifier]

    def install(self, artifact) -> Path:
        self.installs.append(artifact.id)
        self.installed_ids.add(artifact.id)
        return self.paths[artifact.id]


def _install_fakes(monkeypatch, artifacts):
    FakeStore.instances.clear()
    catalog = FakeCatalog(artifacts)
    FakeStore.current = catalog
    monkeypatch.setattr(lexicons_module, "_get_catalog", lambda **_: catalog)
    monkeypatch.setattr(lexicons_module, "DataStore", FakeStore)
    return catalog


def test_discovery_lists_metadata_and_compatibility_without_installing(tmp_path: Path, monkeypatch):
    good = make_artifact(tmp_path / "ipa.g2lex", "ipa")
    bad = make_artifact(tmp_path / "kokoro.g2lex", "kokoro", encoding="kokoro-v1")
    _install_fakes(monkeypatch, (good, bad))

    result = discover_lexicons("en-US")

    assert [entry.selector for entry in result.entries] == ["ipa", "kokoro"]
    assert result.entries[0].model_support is True
    assert result.entries[0].installed is False
    assert result.entries[1].model_support is False
    assert "kokoro-v1" in result.entries[1].compatibility_reason
    assert FakeStore.instances[-1].installs == []


def test_auto_policy_installs_only_the_selected_named_source(tmp_path: Path, monkeypatch):
    selected = make_artifact(tmp_path / "selected.g2lex", "selected")
    unused = make_artifact(tmp_path / "unused.g2lex", "unused")
    _install_fakes(monkeypatch, (selected, unused))

    with KittenG2P(
        KittenG2PConfig(lexicons=("selected",), lexicon_data_policy="auto"),
        backend=FakeBackend(),
    ) as g2p:
        result = g2p.phonemize_prepared("word")

    assert FakeStore.instances[-1].installs == [selected.id]
    assert result.raw_phonemes == "selectedɪ"
    assert result.pronunciation_trace[0].source == "named-g2lex"
    assert result.pronunciation_trace[0].source_name == selected.id
    assert FakeStore.current is not None


def test_installed_only_never_provisions_a_missing_named_source(tmp_path: Path, monkeypatch):
    selected = make_artifact(tmp_path / "selected.g2lex", "selected")
    _install_fakes(monkeypatch, (selected,))

    with pytest.raises(ValueError, match="is not installed"):
        KittenG2P(
            KittenG2PConfig(lexicons=("selected",), lexicon_data_policy="installed-only"),
            backend=FakeBackend(),
        )

    assert FakeStore.instances[-1].installs == []


def test_local_files_precede_ordered_named_sources(tmp_path: Path, monkeypatch):
    first = make_artifact(tmp_path / "first.g2lex", "first")
    second = make_artifact(tmp_path / "second.g2lex", "second")
    _install_fakes(monkeypatch, (first, second))
    local = tmp_path / "local.g2lex"
    local.write_bytes(
        pack_typed(
            {"word": "loʊkəl"},
            metadata={"language": "en-US", "phoneme_encoding": "ipa"},
        )
    )

    with KittenG2P(
        KittenG2PConfig(g2lex_files=(local,), lexicons=("first", "second")),
        backend=FakeBackend(),
    ) as g2p:
        local_result = g2p.phonemize_prepared("word")
    assert local_result.raw_phonemes == "loʊkəl"
    assert local_result.pronunciation_trace[0].source == "local-g2lex"

    with KittenG2P(
        KittenG2PConfig(lexicons=("first", "second")),
        backend=FakeBackend(),
    ) as g2p:
        named_result = g2p.phonemize_prepared("word")

    assert named_result.raw_phonemes == "firstɪ"
    assert named_result.pronunciation_trace[0].source_name == first.id
    assert FakeStore.instances[-1].installs == [first.id, second.id]
