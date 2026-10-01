# eSpeak backend

`kitteng2p` delegates eSpeak discovery and execution to `espeakng-runtime`.
The package does not contain its own native loader, executable discovery,
voice inventory, or platform-specific eSpeak integration.

## Modes

`KittenG2PConfig.espeak_mode` accepts:

- `"auto"`: prefer a usable native library and fall back to the CLI;
- `"native"`: require the native runtime;
- `"cli"`: require the command-line runtime.

```python
from kitteng2p import KittenG2P, KittenG2PConfig

config = KittenG2PConfig(espeak_mode="cli")
with KittenG2P(config) as g2p:
    result = g2p.phonemize_prepared("Hello world")
```

## Explicit runtime paths

Configuration can forward paths for the selected runtime:

```python
config = KittenG2PConfig(
    executable="/path/to/espeak-ng",
    library="/path/to/libespeak-ng.so",
    data="/path/to/espeak-ng-data",
)
```

Only specify paths needed by the selected runtime mode.

## Clause handling

The default backend first requests clauses from `espeakng-runtime`. When
clauses contain terminators, `kitteng2p` composes them back into the raw
phoneme stream before applying the Kitten regex and character codec. If clause
rendering produces no text, the backend falls back to ordinary runtime
phonemization.

## Errors

Backend construction failures are wrapped as `BackendUnavailableError`.
Phonemization failures are wrapped as `PhonemizationError`. The original
exception is retained as the Python exception cause.

## Backend injection

Tests and advanced callers can inject an object satisfying this protocol:

```python
class PhonemeBackend(Protocol):
    def phonemize(self, text: str, *, language: str) -> str: ...
    def close(self) -> None: ...
```

Injected backends are caller-owned. `KittenG2P.close()` does not close them.
