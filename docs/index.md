# kitteng2p documentation

`kitteng2p` is an independent phoneme and token-ID frontend targeting the
public KittenTTS v0.8 text-cleaner contract.

It accepts prepared, speakable text and returns raw eSpeak phonemes,
Kitten-prepared phoneme text, character IDs, and model framing `(0, *ids, 10, 0)`.

It does not synthesize audio, load Kitten ONNX models, download voices, or
perform written-to-spoken semantic normalization.

## Guides

```{toctree}
:maxdepth: 2

installation
quickstart
api
codec
backends
cli
compatibility
architecture
changelog
```

## Semantic preparation

`phonemize_prepared()` expects text that is already suitable to speak. An
application may convert currencies, dates, units, URLs, or abbreviations before
calling `kitteng2p`. That preparation layer is intentionally outside this
package.
