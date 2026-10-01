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

## Result

```{eval-rst}
.. autoclass:: kitteng2p.PhonemizeResult
   :members: ids
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
