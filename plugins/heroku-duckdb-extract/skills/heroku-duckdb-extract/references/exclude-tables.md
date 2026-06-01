# Default-excluded tables

Tables that almost no one wants in an analytical extract. The skill silently excludes the hard list; the soft list prompts the user.

## Hard-exclude (no prompt)

These tables exist for framework infrastructure, not domain data.

- `schema_migrations` — Rails migration tracking
- `ar_internal_metadata` — Rails internal metadata
- `*_versions` — PaperTrail audit log table per source table
- `versions` — PaperTrail singular table (older default)
- `audits` — Audited gem audit log
- `delayed_jobs` — Delayed::Job queue
- `solid_queue_*` — Rails 8+ Solid Queue (jobs, semaphores, processes, etc.)
- `good_jobs` — GoodJob queue
- `que_jobs` — Que queue
- `que_lockers`
- `solid_cache_entries` — Rails 8+ Solid Cache
- `solid_cable_messages` — Rails 8+ Solid Cable

## Soft-prompt

The skill asks the user whether to include these. Defaults are user choice — they're sometimes the whole point of an extract, sometimes noise.

- `ahoy_visits`, `ahoy_events` — Ahoy analytics. Often huge. Default suggestion: exclude unless user is doing usage analysis.
- `active_storage_blobs`, `active_storage_attachments`, `active_storage_variant_records` — file attachment metadata. Default suggestion: exclude unless analyzing storage usage or attachment patterns.

## Why this list

`schema_migrations` etc. are pure framework state — no rows are interesting domain data. Including them wastes extraction time and pollutes the analytical surface area.

Audit tables (`*_versions`, `audits`) duplicate every row of every audited table. Doubles or triples extract size for content already present in the source tables. Useful only when investigating historical changes — a different workflow.

Job tables hold ephemeral queue state. Their content (`solid_queue_jobs.arguments`, etc.) often includes serialized objects with PII — extracting them is high-risk and rarely useful.
