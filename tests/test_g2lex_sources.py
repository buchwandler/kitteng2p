from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from g2lex import TaggedValue
from g2lex.format import pack_typed

from kitteng2p import (
    G2LexFileRef,
    KittenG2P,
    KittenG2PConfig,
    LinguisticToken,
    inspect_g2lex_file,
)


class FakeBackend:
    def __init__(self, output: str = "ə") -> None:
        self.output = output
        self.calls: list[str] = []
        self.closed = False

    def phonemize(self, text: str, *, language: str) -> str:
        assert language.casefold() == "en-us"
        self.calls.append(text)
        return self.output

    def close(self) -> None:
        self.closed = True


def write_lexicon(
    path: Path,
    entries: dict[str, object],
    *,
    language: str = "en-US",
    encoding: str = "ipa",
) -> Path:
    path.write_bytes(
        pack_typed(
            entries,  # type: ignore[arg-type]
            metadata={
                "language": language,
                "phoneme_encoding": encoding,
                "display_name": path.stem,
            },
        )
    )
    return path


def test_inspection_reports_content_and_logical_hashes(tmp_path: Path):
    path = write_lexicon(tmp_path / "words.g2lex", {"read": "ɹɛd"})

    inspection = inspect_g2lex_file(path)

    assert inspection.valid is True
    assert inspection.compatible is True
    assert inspection.path == str(path.resolve())
    assert inspection.sha256 == hashlib.sha256(path.read_bytes()).hexdigest()
    assert inspection.logical_sha256
    assert inspection.entry_count == 1
    assert inspection.language == "en-US"
    assert inspection.phoneme_encoding == "ipa"


def test_local_sources_preserve_order_and_exact_tag_precedes_pos_and_default(tmp_path: Path):
    first = write_lexicon(
        tmp_path / "first.g2lex",
        {"read": TaggedValue((("VBN", "ɹɛd"), ("VERB", "ɹiːd"), ("DEFAULT", "ɹɪd")))},
    )
    second = write_lexicon(tmp_path / "second.g2lex", {"read": "ɹiːd"})
    backend = FakeBackend()
    token = LinguisticToken(0, 4, "read", pos="VERB", tag="VBN")

    with KittenG2P(KittenG2PConfig(g2lex_files=(first, second)), backend=backend) as g2p:
        result = g2p.phonemize_prepared("read!", tokens=(token,))

    assert result.raw_phonemes == "ɹɛd!"
    assert result.pronunciation_trace[0].source == "local-g2lex"
    assert result.pronunciation_trace[0].selector == "VBN"
    assert result.pronunciation_trace[0].source_name == str(first.resolve())
    assert result.pronunciation_trace[0].sha256 == hashlib.sha256(first.read_bytes()).hexdigest()
    assert backend.calls == []


def test_parent_pos_selector_precedes_default(tmp_path: Path):
    path = write_lexicon(
        tmp_path / "tagged.g2lex",
        {"read": TaggedValue((("VERB", "ɹiːd"), ("DEFAULT", "ɹɛd")))},
    )
    token = LinguisticToken(0, 4, "read", pos="VERB", tag="VBN")

    with KittenG2P(KittenG2PConfig(g2lex_files=(path,)), backend=FakeBackend()) as g2p:
        result = g2p.phonemize_prepared("read", tokens=(token,))

    assert result.raw_phonemes == "ɹiːd"
    assert result.pronunciation_trace[0].selector == "VERB"


def test_local_file_hash_pin_and_incompatible_metadata_fail_clearly(tmp_path: Path):
    path = write_lexicon(tmp_path / "pinned.g2lex", {"read": "ɹɛd"})
    wrong_hash = "0" * 64
    with pytest.raises(ValueError, match="changed after it was selected"):
        KittenG2P(
            KittenG2PConfig(g2lex_files=(G2LexFileRef(path, sha256=wrong_hash),)),
            backend=FakeBackend(),
        )

    wrong_language = write_lexicon(
        tmp_path / "wrong-language.g2lex", {"read": "ɹɛd"}, language="fr-FR"
    )
    with pytest.raises(ValueError, match="language metadata conflicts"):
        KittenG2P(KittenG2PConfig(g2lex_files=(wrong_language,)), backend=FakeBackend())

    wrong_encoding = write_lexicon(
        tmp_path / "wrong-encoding.g2lex", {"read": "ɹɛd"}, encoding="kokoro-v1"
    )
    inspection = inspect_g2lex_file(wrong_encoding)
    assert inspection.valid is True
    assert inspection.compatible is False
    with pytest.raises(ValueError, match="requires compatible IPA"):
        KittenG2P(KittenG2PConfig(g2lex_files=(wrong_encoding,)), backend=FakeBackend())


def test_unsupported_selected_ipa_is_rejected_instead_of_truncated(tmp_path: Path):
    path = write_lexicon(tmp_path / "bad-ipa.g2lex", {"read": "☃"})
    with KittenG2P(KittenG2PConfig(g2lex_files=(path,)), backend=FakeBackend()) as g2p:
        with pytest.raises(ValueError, match="unsupported Kitten phoneme symbol"):
            g2p.phonemize_prepared("read")


def test_duplicate_local_paths_are_rejected(tmp_path: Path):
    path = tmp_path / "same.g2lex"
    with pytest.raises(ValueError, match="duplicate G2Lex file path"):
        KittenG2PConfig(g2lex_files=(path, path.parent / "." / path.name))


def test_context_selector_precedes_default_in_tagged_entry(tmp_path: Path):
    path = write_lexicon(
        tmp_path / "context.g2lex",
        {"minute": TaggedValue((("SENSE_SMALL", "maɪˈnuːt"), ("DEFAULT", "ˈmɪnɪt")))},
    )

    with KittenG2P(KittenG2PConfig(g2lex_files=(path,)), backend=FakeBackend()) as g2p:
        result = g2p.phonemize_prepared("A minute crack.")

    trace = next(item for item in result.pronunciation_trace if item.text == "minute")
    assert trace.source == "local-g2lex"
    assert trace.selector == "SENSE_SMALL"
    assert trace.phonemes == "maɪˈnuːt"


def test_source_miss_falls_back_to_one_whole_request_espeak_call(tmp_path: Path):
    path = write_lexicon(tmp_path / "other.g2lex", {"unmatched": "ˈʌnˌmætʃt"})
    backend = FakeBackend("eɪˈspiːk")

    with KittenG2P(KittenG2PConfig(g2lex_files=(path,)), backend=backend) as g2p:
        result = g2p.phonemize_prepared("Read, then wait!")

    assert backend.calls == ["Read, then wait!"]
    assert result.raw_phonemes == "eɪˈspiːk"
    assert [item.source for item in result.pronunciation_trace] == ["espeak", "espeak", "espeak"]
