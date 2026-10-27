# Architecture

`kitteng2p` is the Kitten-specific frontend between prepared text and KittenTTS input IDs. It owns source selection and occurrence-level pronunciation decisions without depending on KittenSynth or VoiceRender.

```text
prepared text + optional linguistic tokens / request-local IPA spans
       |
       v
explicit span -> ordered local G2Lex files -> ordered named Lexphon sources
       |                   |                         |
       +-------------------+-------------------------+
                           |
                           v
          exact tag -> broad POS -> context selector -> DEFAULT
                           |
                           v
       contextual English rule (when no source reading applies)
                           |
                           v
       eSpeak for maximal contiguous fallback text runs
                           |
                           v
       assemble IPA / preserve punctuation / prepare once
                           |
                           v
       Kitten v0.8 character table + [0] ... [10, 0] framing
                           |
                           v
                    tuple[int, ...]
```

With no selected lexicons, tokens, or explicit overrides, the original whole-request eSpeak path is retained. Catalog discovery is metadata-only; named data is provisioned only when selected and allowed by the configured data policy. Local files are explicit paths, validated by content hash, logical hash, locale, and IPA encoding. No filesystem scan is performed.

The G2Lex runtime uses ordered source precedence: request-local override, local files, named sources, contextual fallback, then eSpeak. Within each tagged record, the selector order is exact tag, broad POS, context/sense selector, and `DEFAULT`. Every non-eSpeak decision is represented in the per-occurrence pronunciation trace. Selected lexicon IPA and explicit IPA overrides are rejected if encoding would drop unsupported Kitten symbols; ordinary eSpeak output retains its existing `dropped_symbols` behavior.

## Backend boundary

`PhonemeBackend` remains structural:

```python
phonemize(text, *, language) -> str
close() -> None
```

Tests can inject a deterministic backend. Production defaults to `espeakng-runtime`; fallback calls remain phrase-sized rather than issuing one eSpeak call per ordinary word.

## Dependency boundaries

The dependency direction is `g2lex + lexphon -> kitteng2p -> kittensynth -> voicerender`. Kitteng2p does not import OnnxVoice, NumPy, KittenSynth, VoiceRender, or KokoroG2P.

## Compatibility policy

The character inventory and framing are exact translations of the public v0.8 code. The default eSpeak execution layer is modernized from upstream `phonemizer` to shared `espeakng-runtime`. Existing eSpeak-only calls and codec behavior remain unchanged; selected lexicon data is validated strictly before encoding.
