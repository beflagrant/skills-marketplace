# Preflight row-count thresholds

Run a quick `SELECT count(*)` per chosen table before generating `extraction.sql`. Apply tiered prompts based on the count.

## Tiers

| Row count | Behavior |
|---|---|
| < 100,000 | Silent. Proceed without prompting. |
| 100,000 – 999,999 | Ask: "Table `<name>` has N rows. Add a filter (WHERE clause) or include all rows?" |
| 1,000,000 – 9,999,999 | Strongly suggest: "Table `<name>` has N rows. Recommend `WHERE created_at > CURRENT_DATE - INTERVAL '90 days'` or similar. Proceed without filter? (y/N)" |
| ≥ 10,000,000 | Require explicit acknowledgement: "Table `<name>` has N rows. Extracting this fully will take significant time and put load on the source database. Type the table name to confirm extracting all rows, or provide a filter." |

## Filter suggestions

The most common useful filter is a recent-data window. Suggest by table-name heuristic:

- Event-shaped tables (`events`, `*_events`, `ahoy_events`, `audits`, `*_versions`): `WHERE created_at > CURRENT_DATE - INTERVAL '90 days'`
- Visit-shaped tables (`visits`, `ahoy_visits`, `sessions`): `WHERE started_at > CURRENT_DATE - INTERVAL '30 days'`
- Transactional tables (`orders`, `payments`, `transactions`): `WHERE created_at > CURRENT_DATE - INTERVAL '1 year'` (or longer for analytical relevance)
- Other: no automatic suggestion — ask user

## FK dependency annotation

When a filter is applied, find FK references TO this table from other chosen tables (using `add_foreign_key` lines in schema.rb).

Annotate the generated SQL:

```sql
-- NOTE: filtered users to last 90 days. Dependent tables: orders, sessions, payments.
-- Records in those tables that reference filtered-out users will appear as orphans.
-- Consider whether to also filter the dependent tables for consistency.
```

Do NOT cascade the filter automatically — FK graphs get tangled (polymorphic associations, multi-level, etc.). The user owns the choice.

## Connection load note

For tables on a Heroku Postgres tier ≥ standard-0, when ≥ 1M rows, suggest:

> Heavy extracts can affect the source database's connection limit and serving capacity. Options:
> 1. Run off-peak.
> 2. Run against a follower DB (read replica): `heroku addons:create heroku-postgresql:<tier> --follow <primary> --app <app>` creates one. Then pick its `HEROKU_POSTGRESQL_*_URL` in Step 2.
> 3. Snapshot via `heroku pg:backups` and restore locally (out of scope for this skill).

Don't automate — surface the option, user decides.
