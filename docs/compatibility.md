# Compatibility policy

## Target

`kitteng2p` targets the public KittenTTS v0.8 text-cleaner symbol and framing
contract used by the 0.8-era models.

The symbol inventory and framing are translated from this public v0.8 contract.

## Codec compatibility

The implementation preserves the target pad symbol, punctuation ordering,
ASCII letter ordering, IPA and suprasegmental symbol ordering, last-index-wins
behavior for duplicate symbols, dropping of characters absent from the
inventory, and model framing `(0, *ids, 10, 0)`. These are codec-level
guarantees.

## eSpeak execution difference

The released KittenTTS 0.8.1 stack uses `phonemizer` around eSpeak.
`kitteng2p` instead uses `espeakng-runtime`. This removes model and audio
dependencies and centralizes native and CLI eSpeak handling, but codec
compatibility alone does not prove that every input produces identical
phoneme text or token IDs across platforms and eSpeak versions.

## Optional G2Lex compatibility

G2Lex sources are an additive opt-in path; no named lexicon becomes a silent default. Kitten currently accepts only IPA pronunciation sources whose symbols survive the Kitten codec. Catalog entries with another encoding are discoverable but reported as incompatible, and selected local/named values or explicit overrides containing unsupported symbols fail rather than producing truncated IDs. eSpeak-only calls retain the historical dropped-symbol behavior.

When source-aware composition is active, fallback eSpeak calls receive maximal contiguous text runs around overridden spans. Original punctuation is retained, and the Kitten preparation/encoding/framing step runs once on the assembled stream. Pronunciation traces distinguish explicit, local, named, contextual, and eSpeak decisions. This lexical behavior is separate from prosody and does not claim to fix clause-boundary or intonation differences.

## Golden parity

Exact sentence-level ID parity has not been established across a representative
corpus. Before advertising end-to-end parity, maintain versioned fixtures
comparing prepared sentences through the released KittenTTS 0.8.1
phonemizer/text-cleaner path and `kitteng2p`, including final framed IDs.
Record the upstream package version, eSpeak version, voice selector, and
platform with each golden set.

A useful corpus covers ordinary sentences, punctuation and clause boundaries,
contractions, stress marks, expanded numbers and abbreviations, quotes, em dash
and ellipsis, empty input, and symbols outside the target inventory.

## Semantic normalization

Written-to-spoken normalization is not part of the compatibility contract.
Callers prepare dates, currencies, units, URLs, abbreviations, and similar
written forms before phonemization.
