# Architecture

`kitteng2p` is the model-specific frontend between prepared text and KittenTTS input IDs.

```text
caller semantic preparation
       |
       v
prepared English text
       |
       v
espeakng-runtime
       |
       v
Kitten v0.8 regex tokenization
       |
       v
Kitten character table + [0] ... [10, 0] framing
       |
       v
tuple[int, ...]
```

The package deliberately does not import OnnxVoice, NumPy, or KittenSynth.

## Backend boundary

`PhonemeBackend` is structural:

```python
phonemize(text, *, language) -> str
close() -> None
```

Tests can inject a deterministic backend. Production defaults to `espeakng-runtime`.

## Compatibility policy

The character inventory and framing are exact translations of the public v0.8 code. The default
eSpeak execution layer is modernized from upstream `phonemizer` to the shared `espeakng-runtime`.
A golden parity suite against released KittenTTS should therefore be the first post-MVP task.
