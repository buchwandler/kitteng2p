---
schema_version: 2
object_type: release_entry
versioning:
  schema_version: 1
  revision: 1
entry_id: entry-0002
release_version: 0.1.2
kind: added
summary:
  Added contextual pronunciation overrides, heteronym resolution, and traceable
  pronunciation diagnostics
status: accepted
audience: null
scopes: []
source_refs: []
paths:
  - kitteng2p/api.py
  - kitteng2p/context.py
  - kitteng2p/types.py
  - docs/architecture.md
  - docs/compatibility.md
  - tests/test_g2lex_sources.py
  - tests/test_heteronym_context.py
  - tests/test_pronunciation_overrides.py
issues: []
prs: []
sources:
  - git:5746236b6f7c81af019ea368e7d895ccf639d213
contributors:
  - "@holgern"
breaking: false
internal: false
order: 2
---

Request-local IPA spans and supported contextual rules now participate in pronunciation selection, while results expose source traces and diagnostics for inspection.
