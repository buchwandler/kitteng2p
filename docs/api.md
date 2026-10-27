# API reference

## High-level frontend

```{eval-rst}
.. autoclass:: kitteng2p.KittenG2P
   :members:
```

## Configuration

```{eval-rst}
.. autoclass:: kitteng2p.KittenG2PConfig
   :members:
```

## Lexicon discovery and inspection

```{eval-rst}
.. autofunction:: kitteng2p.discover_lexicons
.. autofunction:: kitteng2p.inspect_g2lex_file
.. autoclass:: kitteng2p.G2LexFileRef
   :members:
.. autoclass:: kitteng2p.G2LexFileInspection
   :members:
.. autoclass:: kitteng2p.LexiconDiscoveryResult
   :members:
.. autoclass:: kitteng2p.NamedLexiconInfo
   :members:
```

## Request tokens, overrides, and provenance

Pass `LinguisticToken` and `PronunciationOverride` values to `KittenG2P.phonemize_prepared()` or the convenience function. Their offsets are half-open character spans into the original prepared text. Explicit spans use Kitten-supported IPA and are authoritative over configured lexicons and contextual rules.

```{eval-rst}
.. autoclass:: kitteng2p.LinguisticToken
   :members:
.. autoclass:: kitteng2p.PronunciationOverride
   :members:
.. autoclass:: kitteng2p.PronunciationTrace
   :members:
.. autoclass:: kitteng2p.PronunciationDiagnostic
   :members:
```

## Result

```{eval-rst}
.. autoclass:: kitteng2p.PhonemizeResult
   :members: ids, pronunciation_trace, diagnostics
   :exclude-members: text, raw_phonemes, phonemes, token_ids, language, dropped_symbols
```

## Convenience functions

```{eval-rst}
.. autofunction:: kitteng2p.get_g2p
.. autofunction:: kitteng2p.phonemize_prepared
.. autofunction:: kitteng2p.phonemes
.. autofunction:: kitteng2p.phoneme_ids
```

## Codec helpers

```{eval-rst}
.. autofunction:: kitteng2p.basic_english_tokenize
.. autofunction:: kitteng2p.prepare_phoneme_text
.. autofunction:: kitteng2p.encode_phonemes
.. autofunction:: kitteng2p.frame_token_ids
```

## Errors

```{eval-rst}
.. automodule:: kitteng2p.errors
   :members:
```
