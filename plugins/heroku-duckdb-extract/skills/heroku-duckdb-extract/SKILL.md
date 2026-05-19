---
name: heroku-duckdb-extract
description: >
  Use when the user wants to extract data from a Heroku Postgres database into a local DuckDB file with anonymization. Triggers: "pull production data into DuckDB", "snapshot Heroku to DuckDB", "anonymize Heroku data for local analysis", "set up local analytics DB from Heroku". Do not use for: schema review without extraction, Heroku Postgres connection troubleshooting, or running migrations.
metadata:
  publish: marketplace
---

# Heroku → DuckDB Extraction

This skill produces a repeatable, anonymized DuckDB snapshot of a Heroku Postgres database. Output: a per-run timestamped directory containing `extraction.sql`, a `.duckdb` file, per-table CSVs, and a wrapper script to re-run the extract.

The skill is a guided conversation. Some steps require user judgment (table selection, PII review); the wrapper script captures everything deterministic for re-runs.

---

## Step 1 — Preflight checks

Hard-refuse and stop if any check fails. No silent partial flows.

### Detect platform

```bash
uname -s
```

### Heroku CLI

```bash
heroku --version
heroku auth:whoami
```

If `heroku` is missing, refuse with the install command for the detected platform:

- `Darwin` → `brew tap heroku/brew && brew install heroku`
- `Linux` → `curl https://cli-assets.heroku.com/install.sh | sh`
- Other → "See https://devcenter.heroku.com/articles/heroku-cli"

If `heroku auth:whoami` errors, instruct: `heroku login` then re-run.

### DuckDB ≥ 0.9.0

```bash
duckdb --version
```

Parse the version. If below 0.9.0, hard refuse: "Requires DuckDB ≥ 0.9.0. Upgrade and re-run."

---

## Step 2 — App and database selection

Ask for the Heroku app name. Verify access:

```bash
heroku apps:info --app <name> --json
```

Display: app name, region, and Postgres tier (read tier from `heroku pg:info --app <name>`). The tier informs later decisions about followers and connection load.

Enumerate Postgres URLs in the app:

```bash
heroku config --app <name> | grep -E '^(DATABASE_URL|HEROKU_POSTGRESQL_[A-Z]+_URL)'
```

Heroku Postgres add-ons surface as `HEROKU_POSTGRESQL_<COLOR>_URL`. `DATABASE_URL` is an alias for one of them — annotate which one as "primary".

Show the list. User picks the URL var name (default: `DATABASE_URL`). Record both the **env name** (e.g. `HEROKU_POSTGRESQL_BLACK_URL`) and the **environment label** (derived from the app name suffix: `-staging`, `-production`, `-prod`; default `production` when no suffix).

If user picks a non-primary DB, warn: "schema.rb typically describes the primary database. The DB you picked may have a different schema. Continue? You'll see errors at extract time if column names don't match."

---

## Step 3 — Schema discovery

Search in order:

1. `db/schema.rb` (Rails default)
2. `db/structure.sql` (Rails with `schema_format = :sql`)
3. `app/*/db/schema.rb` (engines or Rails monorepos)

If found, read it and summarize: "Found schema with N tables, M columns. Use this?" User confirms.

If not found, fall back: ask user to paste schema contents.

Schema is required for table inventory, FK relationships, and column-name-based PII heuristics. The skill will NOT query `information_schema` — schema.rb is the source of truth.

If extraction later fails on a Postgres type (citext, hstore, custom enum), instruct user to cast it to VARCHAR explicitly in the SELECT. The skill will not auto-handle these.

---

## Step 4 — Table selection

Apply default excludes (see `references/exclude-tables.md`). Hard-exclude:

- `schema_migrations`, `ar_internal_metadata`
- `*_versions` (PaperTrail)
- `audits` (Audited gem)
- `delayed_jobs`, `solid_queue_*`, `good_jobs`

Soft-prompt for:

- `ahoy_*` (analytics — often desired but tables are massive)
- `active_storage_*` (rarely the data being analyzed)

Show the remaining table list. User confirms or edits.

---

## Step 5 — Preflight row counts

Run an ephemeral DuckDB session that attaches Postgres and counts rows per chosen table:

```sql
INSTALL postgres;
LOAD postgres;
ATTACH '<URL>' AS prod (TYPE postgres, READ_ONLY);
SELECT 'users' AS table_name, count(*) FROM prod.users
UNION ALL SELECT 'orders', count(*) FROM prod.orders
-- ...
;
```

Apply tiered prompts per `references/preflight-thresholds.md`:

- **< 100k**: silent
- **100k – 1M**: ask "Big enough to want a filter?"
- **1M – 10M**: strongly suggest `WHERE created_at > CURRENT_DATE - INTERVAL '90 days'`
- **≥ 10M**: require explicit ack before proceeding

For tables on a tier ≥ standard-0, mention that a Heroku follower DB would offload read load from the primary. Don't automate — user decides.

If user adds a WHERE clause, and the table is referenced by FK from other chosen tables, annotate that decision in the generated SQL as a comment:

```sql
-- NOTE: filtered users to last 90 days. Dependent tables: orders, sessions.
-- Orders/sessions referencing filtered-out users will be orphans in this extract.
```

---

## Step 6 — Anonymization map

Load `references/pii-patterns.md` and `references/encrypted-columns.md`.

For each chosen table, classify every column:

- **obvious-keep**: id, FK (`*_id`), numeric, boolean, date/timestamp, enum-like columns matching kept patterns. No prompt.
- **obvious-anon**: name matches a PII pattern (email, person name, phone, address, IP, user-agent, sensitive ID, auth token). Auto-apply the deterministic expression from `references/pii-patterns.md`. No prompt.
- **encrypted**: `encrypted_*`, `*_ciphertext`, `*_iv`, Devise auth tokens. Apply rules from `references/encrypted-columns.md`. No prompt.
- **gray-zone**: any `text` / `jsonb` column not matched above, plus named columns (`notes`, `description`, `bio`, `comment`, `message`, `body`, `content`). Default: `'[redacted]'` for text, `'{}'::JSON` for jsonb. **Require explicit user allow to pass through.**

### Re-run handling

If a prior `extraction.sql` exists for this app (look in `./<app>-<env>-extract/`), parse its anonymization map. For unchanged columns, carry forward the prior decision. Prompt only for new or changed columns. Show a summary of carried-forward decisions before generating the new file.

### Gray-zone review

Present each table containing gray-zone columns. For each:

- Show the proposed default (redact)
- Ask user to mark any columns "allow through"

When user allows a free-text column, it passes through verbatim. When user allows a jsonb column, cast it to native DuckDB `JSON` type (NOT `VARCHAR`).

### Final acknowledgement

Before generating `extraction.sql`, show a consolidated summary of every column that will pass through unredacted (including obvious-keeps and explicit allows). User must confirm. The summary is also written as a comment block at the top of `extraction.sql`:

```sql
-- ANONYMIZATION AUDIT TRAIL
-- The following columns pass through unredacted:
--   users.country
--   users.bio  (user explicitly allowed)
--   accounts.metadata  (user explicitly allowed, cast to JSON)
-- User acknowledged 2026-05-15T14:30:00Z.
```

---

## Step 7 — Generate output directory

Determine the env label (Step 2). Build a per-run timestamped directory:

```
./<app>-<env>-extract/<ISO-timestamp>/
├── extraction.sql
├── <app>-<env>.duckdb        (populated by run-extract.sh)
├── run-extract.sh
└── csvs/
    └── (one CSV per chosen table, populated by run-extract.sh)
```

ISO timestamp format: `YYYY-MM-DDTHH-MM-SS` (UTC, filesystem-safe).

The skill itself generates `extraction.sql` and `run-extract.sh`. The `.duckdb` file and CSVs are produced by running `run-extract.sh`.

### extraction.sql header

```sql
-- extraction.sql
-- App: <heroku-app-name>
-- Env: <production|staging|...>
-- Generated: <ISO timestamp>
-- Skill: heroku-duckdb-extract @ <skill-git-sha>
-- NEVER includes DATABASE_URL or any credential.
```

Get the skill SHA:

```bash
git -C <path-to-this-skill-dir> log -1 --format=%h -- SKILL.md
```

Followed by the anonymization audit trail comment block (Step 6), then the per-table SQL:

```sql
CREATE OR REPLACE TABLE users AS
SELECT
  id,
  'user' || CAST(id AS VARCHAR) || '@example.com' AS email,
  'User' || CAST(id AS VARCHAR) AS first_name,
  'Last' || CAST(id AS VARCHAR) AS last_name,
  country,
  created_at,
  updated_at
FROM prod.users;
COPY users TO 'csvs/users.csv' (HEADER, DELIMITER ',');

-- ... additional tables ...

DETACH prod;
```

### run-extract.sh

```bash
#!/usr/bin/env bash
set -euo pipefail

# App: <heroku-app-name>
# DB URL var: <DATABASE_URL or HEROKU_POSTGRESQL_*_URL>
# Re-run from this directory at any time.

# Prereqs
command -v heroku >/dev/null || { echo "heroku CLI required"; exit 1; }
command -v duckdb >/dev/null || { echo "duckdb required"; exit 1; }
heroku auth:whoami >/dev/null || { echo "run: heroku login"; exit 1; }

# Fetch fresh DB URL at runtime — never persisted on disk
URL=$(heroku config:get <URL_VAR_NAME> --app <APP_NAME>)
[ -n "$URL" ] || { echo "could not fetch DB URL"; exit 1; }

export PGSSLMODE=require

mkdir -p csvs
{
  echo "INSTALL postgres; LOAD postgres;"
  echo "ATTACH '$URL' AS prod (TYPE postgres, READ_ONLY);"
  cat extraction.sql
} | duckdb <APP>-<ENV>.duckdb
```

---

## Step 8 — gitignore handling

Determine the project root (closest ancestor with `.git/`). If found:

1. Read `.gitignore` (or create empty).
2. If the pattern `<app>-<env>-extract/` is not present, append it.
3. Run `git ls-files <app>-<env>-extract/` — if any output, warn loudly: "These extract files are already tracked in git. They contain anonymized but recognizable data. Remove them with `git rm --cached -r <app>-<env>-extract/` and recommit."

If no `.git/` ancestor, skip silently. Skill is being run outside a repo.

---

## Step 9 — Run the wrapper script

Tell the user:

```bash
cd <app>-<env>-extract/<timestamp>
./run-extract.sh
```

Confirm exit status. On success, the `.duckdb` and CSVs exist in this directory.

---

## Step 10 — Post-extract orientation (optional)

Offer: "Want suggestions for analytical queries against your loaded schema?"

If yes, propose schema-aware queries grouped by category:

- **Data quality**: orphans, nulls, FK mismatches, stale sync records
- **Engagement / activity**: declining usage signals, dormant accounts
- **Compliance / completion**: due dates, expirations, never-completed work
- **Integration health**: sync success rates, failed external IDs
- **Billing**: usage vs plan, suspended accounts

Write queries on demand using the loaded schema's actual table and column names. Don't ship a canned list — propose against what's actually in the file.

---

## Cross-cutting rules

- **Never embed `DATABASE_URL`** in `extraction.sql`, `run-extract.sh`, or any file on disk. Always fetch at runtime via Heroku CLI.
- **All anonymization expressions are id-keyed** (deterministic). Never use `ROW_NUMBER()` without `ORDER BY` — it produces different values per run.
- **`CREATE OR REPLACE TABLE`** makes re-runs idempotent. No partial-load resume logic.
- **Fail loud on unsupported types** (citext, hstore, custom Postgres enums). Don't silently mistranslate.
- **DETACH at end** of `extraction.sql` is cosmetic — the `duckdb` process exit closes the Postgres connection. Keep it for clarity when running interactively.
