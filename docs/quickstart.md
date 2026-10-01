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
