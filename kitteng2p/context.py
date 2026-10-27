from __future__ import annotations

from dataclasses import dataclass

from .types import LinguisticToken


@dataclass(frozen=True, slots=True)
class ContextResolution:
    phonemes: str
    selector: str
    reason: str


def _word(value: str) -> str:
    return value.casefold().strip(".,!?;:()[]{}\"'“”‘’")


def _tag_pos(token: LinguisticToken) -> str | None:
    if token.pos:
        pos = token.pos.upper()
        if pos in {"NOUN", "VERB", "ADJ", "ADV", "AUX", "PROPN", "PRON"}:
            return pos
    tag = (token.tag or "").upper()
    if tag.startswith("NN"):
        return "NOUN"
    if tag.startswith("VB"):
        return "VERB"
    if tag.startswith("JJ"):
        return "ADJ"
    if tag.startswith("RB"):
        return "ADV"
    return None


def _sense(phonemes: str, sense: str, reason: str) -> ContextResolution:
    return ContextResolution(phonemes, f"SENSE_{sense.upper()}", reason)


def resolve_english_heteronym(
    token: LinguisticToken,
    tokens: tuple[LinguisticToken, ...],
    index: int,
    *,
    text: str | None = None,
) -> ContextResolution | None:
    """Resolve only well-supported cases of the documented English heteronyms.

    This deliberately small deterministic resolver consumes existing token annotations;
    it does not infer general POS or introduce an NLP/model dependency.
    """
    word = _word(token.text)
    sentence_start = 0
    sentence_end = len(text) if text is not None else None
    if text is not None:
        left_boundaries = [text.rfind(mark, 0, token.start) for mark in ".!?;:"]
        sentence_start = max(left_boundaries, default=-1) + 1
        right_boundaries = [
            boundary for mark in ".!?;:" if (boundary := text.find(mark, token.end)) >= 0
        ]
        sentence_end = min(right_boundaries, default=len(text))
    left = [
        _word(item.text)
        for item in tokens[max(0, index - 5) : index]
        if item.start >= sentence_start
    ]
    right = [
        _word(item.text)
        for item in tokens[index + 1 : index + 6]
        if sentence_end is None or item.start < sentence_end
    ]
    context = set(left + right)
    before = left[-1] if left else ""
    after = right[0] if right else ""
    pos = _tag_pos(token)
    tag = (token.tag or "").upper()

    if word == "bow":
        if context & {"gesture", "greeting", "polite", "respect", "audience", "curtsy"}:
            return _sense("baʊ", "gesture", "nearby words indicate a bowing gesture")
        if context & {"weapon", "arrow", "hunting", "archer", "shoot", "string", "quiver"}:
            return _sense("boʊ", "weapon", "nearby words indicate a bow weapon")
    elif word == "bass":
        if context & {"fish", "fishing", "lake", "river", "aquarium", "caught", "angler"}:
            return _sense("bæs", "fish", "nearby words indicate the fish")
        if context & {"music", "musical", "guitar", "singer", "note", "instrument", "band", "song"}:
            return _sense("beɪs", "music", "nearby words indicate the musical sense")
    elif word == "minute":
        if context & {"crack", "detail", "amount", "quantity", "particle", "difference"}:
            if pos in {None, "ADJ", "NOUN"} or tag in {"JJ", "NN"}:
                return _sense(
                    "maɪˈnuːt",
                    "small",
                    "the following/context noun indicates the adjective 'tiny'",
                )
        if context & {"later", "ago", "wait", "took", "lasted", "elapsed", "hour", "second"}:
            return _sense("ˈmɪnɪt", "time", "temporal context indicates a unit of time")
        if after in {"later", "ago"} or before in {"one", "five", "ten", "few", "every"}:
            return _sense(
                "ˈmɪnɪt",
                "time",
                "quantity or temporal modifier indicates a unit of time",
            )
    elif word == "lead":
        if context & {
            "metal",
            "pipe",
            "pipes",
            "plumbing",
            "paint",
            "poison",
            "weight",
            "bullet",
            "ore",
        }:
            return _sense("lɛd", "metal", "nearby words indicate the metal")
        if context & {
            "principal",
            "chief",
            "main",
            "leading",
            "role",
            "example",
            "team",
            "company",
            "performer",
        }:
            return _sense("liːd", "principal", "nearby words indicate the principal/leading sense")
    elif word == "does":
        if context & {"deer", "herd", "buck", "fawn", "antler", "wildlife", "doe", "does"}:
            return _sense("doʊz", "deer", "nearby animal context identifies the plural deer noun")
        if after in {"not", "n't"} or before in {"she", "he", "it", "what", "who"}:
            return _sense("dʌz", "auxiliary", "grammatical context identifies the auxiliary")
        if pos == "AUX" or tag in {"VBZ", "VBP"}:
            return _sense("dʌz", "auxiliary", "grammatical context identifies the auxiliary")
    elif word == "refuse":
        if context & {
            "rubbish",
            "garbage",
            "waste",
            "trash",
            "collection",
            "dump",
            "bin",
            "heap",
            "recycling",
        }:
            return _sense(
                "ˈrɛfjuːs",
                "noun",
                "nearby disposal context identifies refuse as rubbish",
            )
        if before in {"the", "household", "industrial", "municipal"} and after in {
            "was",
            "is",
            "smelled",
            "collected",
            "lay",
        }:
            return _sense(
                "ˈrɛfjuːs",
                "noun",
                "determiner and predicate indicate the rubbish noun",
            )
        if (
            pos == "VERB"
            or tag.startswith("VB")
            or (
                before in {"i", "we", "you", "they", "he", "she", "it"}
                and after in {"to", "the", "a", "an", "help", "offer", "permission"}
            )
        ):
            return _sense(
                "rɪˈfjuːz",
                "verb",
                "grammatical context identifies the action 'decline'",
            )
    elif word == "learned":
        if context & {
            "scholar",
            "scholarly",
            "professor",
            "academic",
            "man",
            "woman",
            "colleague",
            "person",
        }:
            if before in {"highly", "very", "well", "deeply"} or after in {
                "scholar",
                "professor",
                "academic",
                "colleague",
                "man",
                "woman",
                "person",
            }:
                return _sense(
                    "ˈlɜːrnɪd",
                    "adjective",
                    "descriptive context indicates the scholarly adjective",
                )
        if before in {"have", "has", "had", "was", "were", "been", "being"}:
            return _sense("lɜːrnd", "past", "auxiliary context identifies the past participle")
    return None


__all__ = ["ContextResolution", "resolve_english_heteronym"]
