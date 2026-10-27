from __future__ import annotations

import json
from pathlib import Path

import pytest

from kitteng2p import KittenG2P, LinguisticToken


class FakeBackend:
    def phonemize(self, text: str, *, language: str) -> str:
        return "fallback"

    def close(self) -> None:
        pass


def _result(text: str, word: str, *, pos: str | None = None, tag: str | None = None):
    start = text.index(word)
    token = LinguisticToken(start, start + len(word), word, pos=pos, tag=tag, lemma=word.casefold())
    with KittenG2P(backend=FakeBackend()) as g2p:
        return g2p.phonemize_prepared(text, tokens=(token,))


_CORRECTED_EVALUATION = json.loads(
    (Path(__file__).parent / "fixtures" / "heteronym_evaluation.json").read_text(encoding="utf-8")
)
_CONTEXT_CASES = [
    pytest.param(
        case["text"],
        case["word"],
        case["expected_ipa"],
        case["selector"],
        id=case["id"],
    )
    for case in _CORRECTED_EVALUATION
]
_CONTEXT_CASES.extend(
    [
        ("The bass played music with the band.", "bass", "beɪs", "SENSE_MUSIC"),
        ("A bass fish swam in the lake.", "bass", "bæs", "SENSE_FISH"),
        ("The lead role was important.", "lead", "liːd", "SENSE_PRINCIPAL"),
        ("Lead pipes contain a toxic metal.", "Lead", "lɛd", "SENSE_METAL"),
        ("Does wandered through the herd of deer.", "Does", "doʊz", "SENSE_DEER"),
        ("She does not agree.", "does", "dʌz", "SENSE_AUXILIARY"),
        ("The refuse was collected with the rubbish.", "refuse", "ˈrɛfjuːs", "SENSE_NOUN"),
        ("They refuse the offer.", "refuse", "rɪˈfjuːz", "SENSE_VERB"),
        ("The highly learned scholar spoke.", "learned", "ˈlɜːrnɪd", "SENSE_ADJECTIVE"),
        ("They had learned the lesson.", "learned", "lɜːrnd", "SENSE_PAST"),
    ]
)


@pytest.mark.parametrize(("text", "word", "expected", "selector"), _CONTEXT_CASES)
def test_known_heteronyms_have_traceable_contextual_pronunciations(
    text: str, word: str, expected: str, selector: str
):
    result = _result(text, word)
    trace = next(
        item for item in result.pronunciation_trace if item.text.casefold() == word.casefold()
    )

    assert trace.source == "context-rule"
    assert trace.phonemes == expected
    assert trace.selector == selector
    assert trace.reason
    assert trace.phonemes in result.phonemes


def test_context_cues_do_not_cross_sentence_boundaries():
    result = _result("We saw a bow. The gesture was polite.", "bow")
    trace = next(item for item in result.pronunciation_trace if item.text.casefold() == "bow")

    assert trace.source == "espeak"
