# Quick start

## High-level API

```python
from kitteng2p import KittenG2P

with KittenG2P() as g2p:
    result = g2p.phonemize_prepared("Hello, world.")

print(result.phonemes)
print(result.token_ids)
print(result.dropped_symbols)
```

`token_ids` already includes Kitten framing: `(0, ..., 10, 0)`.

## Convenience functions

```python
from kitteng2p import phoneme_ids, phonemes

print(phonemes("Hello world"))
print(phoneme_ids("Hello world"))
```

The convenience functions create and close a temporary `KittenG2P` instance.

## Select a language or backend mode

```python
from kitteng2p import KittenG2P, KittenG2PConfig

config = KittenG2PConfig(language="en-gb", espeak_mode="auto")
with KittenG2P(config) as g2p:
    result = g2p.phonemize_prepared("Hello world")
```

The language is forwarded as an eSpeak voice/language selector. Use `native`
or `cli` instead of `auto` only when the application needs a specific runtime
path.

## Named and local G2Lex sources

G2Lex selection is opt-in; `KittenG2PConfig()` still uses whole-request eSpeak by default. Supply local files and named Lexphon selectors explicitly. Local file order precedes named-selector order, and named assets are installed only when selected with `lexicon_data_policy="auto"`.

```python
from kitteng2p import G2LexFileRef, KittenG2P, KittenG2PConfig, LinguisticToken

text = "A minute crack appeared."
start = text.index("minute")
config = KittenG2PConfig(
    g2lex_files=(G2LexFileRef("./book-pronunciations.g2lex"),),
    lexicons=("lexhint",),
    lexicon_data_policy="installed-only",
)
tokens = (LinguisticToken(start, start + 6, "minute", pos="NOUN", tag="NN"),)
with KittenG2P(config) as g2p:
    result = g2p.phonemize_prepared(text, tokens=tokens)

print(result.pronunciation_trace)
```

Use `PronunciationOverride(start, end, phonemes, alphabet="ipa")` for a request-local pronunciation that overrides every configured source. Token and override spans are half-open character offsets into the original text. Selected IPA must use the Kitten-supported symbol inventory; unsupported symbols raise an actionable error instead of being dropped.

`discover_lexicons(language="en-us")` lists catalog metadata and installed state without installing data. `inspect_g2lex_file(path)` reports file hashes, entry count, language, encoding, and Kitten compatibility. Context rules cover a small set of well-supported English heteronyms and require no NLP model download.

## Prepared-text boundary

`kitteng2p` does not expand semantic written forms. If an application wants
`$12.50` spoken as “twelve dollars and fifty cents”, it must perform that
conversion before calling `phonemize_prepared()`.

## Inspect dropped symbols

```python
result = g2p.phonemize_prepared("...")
if result.dropped_symbols:
    print("not in Kitten symbol inventory:", result.dropped_symbols)
```

Unknown characters are dropped to match the target codec behavior. Inspect
`dropped_symbols` when diagnosing pronunciation or token-ID differences.
