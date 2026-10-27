---
schema_version: 2
object_type: release_entry
versioning:
  schema_version: 1
  revision: 1
entry_id: entry-0001
release_version: 0.1.2
kind: added
summary:
  Added opt-in local and named G2Lex pronunciation sources with IPA validation
  and lexicon discovery
status: accepted
audience: null
scopes: []
source_refs:
  - git:5746236b6f7c81af019ea368e7d895ccf639d213
paths:
  - kitteng2p/config.py
  - kitteng2p/lexicons.py
  - kitteng2p/__init__.py
  - docs/api.md
  - docs/quickstart.md
  - pyproject.toml
issues: []
prs: []
sources:
  - git:5746236b6f7c81af019ea368e7d895ccf639d213
contributors:
  - "@holgern"
breaking: false
internal: false
order: 1
---

Callers can select local or named pronunciation sources, inspect available lexicons, pin source hashes, and retain deterministic source precedence without changing the default eSpeak path.
