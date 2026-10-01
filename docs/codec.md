# Codec contract

The codec converts eSpeak phoneme text into the character IDs expected by the
public KittenTTS v0.8 text-cleaner contract.

## Stages

```text
raw phoneme text
    |
    v
basic_english_tokenize()
    |
    v
tokens joined with one ASCII space
    |
    v
character-to-ID lookup
    |
    v
unknown characters dropped
    |
    v
(0, *ids, 10, 0)
```

## Symbol inventory

The inventory is assembled from the pad symbol `$`, the target punctuation
string, ASCII uppercase and lowercase letters, and the target IPA and
suprasegmental symbols. The mapping is built in sequence order. When a symbol
occurs more than once, its later occurrence overwrites the earlier dictionary
entry. This is intentional compatibility behavior.

## Unknown symbols

`encode_phonemes()` does not raise for unknown characters. It returns encoded
IDs and the dropped characters:

```python
ids, dropped = encode_phonemes(text)
```

`dropped` preserves unknown characters in encounter order. Dropping unknown
symbols is codec compatibility behavior, not error recovery.

## Framing

`frame_token_ids()` adds prefix ID `0` and suffix IDs `(10, 0)` to unframed
character IDs. The framing is already applied to `PhonemizeResult.token_ids`.

```python
from kitteng2p import encode_phonemes, frame_token_ids

ids, dropped = encode_phonemes("həˈloʊ")
model_ids = frame_token_ids(ids)
```
