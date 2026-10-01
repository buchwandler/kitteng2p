from __future__ import annotations

import re

_PAD = "$"
_PUNCTUATION = ';:,.!?¡¿—…”«»"" '
_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
_LETTERS_IPA = (
    "ɑɐɒæɓʙβɔɕçɗɖðʤəɘɚɛɜɝɞɟʄɡɠɢʛɦɧħɥʜɨɪʝɭɬɫɮʟɱɯɰŋɳɲɴøɵɸ"
    "θœɶʘɹɺɾɻʀʁɽʂʃʈʧʉʊʋⱱʌɣɤʍχʎʏʑʐʒʔʡʕʢǀǁǂǃˈˌːˑʼʴʰʱʲʷˠˤ˞"
    "↓↑→↗↘'̩'ᵻ"
)
SYMBOLS: tuple[str, ...] = tuple([_PAD, *list(_PUNCTUATION), *list(_LETTERS), *list(_LETTERS_IPA)])

# This comprehension intentionally gives duplicate symbols their last upstream index, matching:
#   for i in range(len(symbols)): dicts[symbols[i]] = i
SYMBOL_TO_ID: dict[str, int] = {symbol: index for index, symbol in enumerate(SYMBOLS)}

FRAME_PREFIX_ID = 0
FRAME_SUFFIX_IDS = (10, 0)
_TOKEN_RE = re.compile(r"\w+|[^\w\s]", re.UNICODE)


def basic_english_tokenize(text: str) -> tuple[str, ...]:
    """Split phoneme text into word and punctuation tokens.

    Parameters
    ----------
    text:
        Raw phoneme text.

    Returns
    -------
    tuple[str, ...]
        Tokens in source order, excluding whitespace separators.
    """
    return tuple(_TOKEN_RE.findall(text))


def prepare_phoneme_text(raw_phonemes: str) -> str:
    """Tokenize raw phonemes and join tokens with one ASCII space.

    Parameters
    ----------
    raw_phonemes:
        Phoneme text returned by the backend.

    Returns
    -------
    str
        Prepared text passed to the character encoder.
    """
    return " ".join(basic_english_tokenize(raw_phonemes))


def encode_phonemes(phonemes: str) -> tuple[tuple[int, ...], tuple[str, ...]]:
    """Encode known symbols and report unknown characters in encounter order.

    Unknown characters are dropped from the encoded IDs and returned in the
    second tuple. The IDs are unframed; use :func:`frame_token_ids` before
    passing them to a model.

    Parameters
    ----------
    phonemes:
        Prepared phoneme text.

    Returns
    -------
    tuple[tuple[int, ...], tuple[str, ...]]
        Unframed character IDs and dropped characters.
    """
    ids: list[int] = []
    dropped: list[str] = []
    for char in phonemes:
        value = SYMBOL_TO_ID.get(char)
        if value is None:
            dropped.append(char)
        else:
            ids.append(value)
    return tuple(ids), tuple(dropped)


def frame_token_ids(ids: tuple[int, ...]) -> tuple[int, ...]:
    """Add the Kitten model prefix and suffix to unframed character IDs.

    Parameters
    ----------
    ids:
        Unframed IDs returned by :func:`encode_phonemes`.

    Returns
    -------
    tuple[int, ...]
        Framed IDs in the form ``(0, *ids, 10, 0)``.
    """
    return (FRAME_PREFIX_ID, *ids, *FRAME_SUFFIX_IDS)
