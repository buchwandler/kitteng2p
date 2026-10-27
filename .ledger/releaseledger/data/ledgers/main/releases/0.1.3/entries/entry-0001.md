---
schema_version: 2
object_type: release_entry
versioning:
  schema_version: 1
  revision: 1
entry_id: entry-0001
release_version: 0.1.3
kind: fixed
summary:
  Accept punctuation and tokenizer-specific linguistic annotations without
  redefining Kitten word segmentation
status: accepted
audience: null
scopes: []
source_refs:
  - tl:task-0050
paths:
  - kitteng2p/api.py
  - tests/test_linguistic_tokens.py
issues: []
prs: []
sources: []
contributors: []
breaking: false
internal: false
order: 1
---

Safe one-word hints are projected onto Kitteng2p's internal words; non-word and incompatible hints are ignored while invalid source alignment remains an error.
