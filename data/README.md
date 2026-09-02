# Bundled data snapshot

`financial.sqlite3` is a portable demonstration snapshot for the read-only query service.
It contains reviewed Saudi Aramco annual data for 2021-2025 and the existing US sample.
Every current fact points to its official source and keeps its staging and version audit trail.
The snapshot also carries the active `backlog_items` ledger. These rows describe known
coverage/domain gaps and are not counted as verified production facts.

`imports/` contains the structured, source-referenced manifests used to reproduce the
snapshot through the normal extraction, mapping, normalization, validation and publication
pipeline. Raw downloaded documents remain excluded from Git because they can be large; the
database preserves their URLs, hashes, processing states and provenance.

Regenerate the human-readable outputs with:

    python -m finengine --db data/financial.sqlite3 report
