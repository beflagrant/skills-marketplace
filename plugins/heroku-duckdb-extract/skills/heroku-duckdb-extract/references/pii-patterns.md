# PII column patterns and anonymization expressions

All expressions are id-keyed (deterministic across runs). Never use `ROW_NUMBER()` without `ORDER BY`.

## Classification rules

A column's class is determined by name pattern first, then type. Patterns are case-insensitive against the bare column name (without table prefix).

### obvious-keep (silent default)

- `id`, `*_id` (foreign keys)
- All numeric types (`integer`, `bigint`, `decimal`, `numeric`, `float`)
- All boolean
- All date/time types (`date`, `timestamp`, `time`, `datetime`)
- `country`, `country_code`, `locale`, `language`, `timezone`
- Enum-like string columns with no PII risk: `status`, `kind`, `type`, `state`, `role` (when value range is small/discrete)

### obvious-anon (silent default)

| Pattern (case-insensitive) | DuckDB expression |
|---|---|
| `email`, `*_email`, `email_*`, `*_emails` | `'user' \|\| CAST(id AS VARCHAR) \|\| '@example.com'` |
| `first_name`, `given_name` | `'First' \|\| CAST(id AS VARCHAR)` |
| `last_name`, `family_name`, `surname` | `'Last' \|\| CAST(id AS VARCHAR)` |
| `middle_name` | `'Middle' \|\| CAST(id AS VARCHAR)` |
| `full_name`, `display_name`, `preferred_name`, `name` (on people-shaped tables) | `'User ' \|\| CAST(id AS VARCHAR)` |
| `phone`, `phone_number`, `*_phone`, `phone_*`, `mobile`, `mobile_number`, `fax`, `fax_number` | `'555-000-' \|\| LPAD(CAST(id AS VARCHAR), 4, '0')` |
| `address`, `address_1`, `address_2`, `street`, `street_address` | `CAST(id AS VARCHAR) \|\| ' Anonymized St'` |
| `city` | `'Anytown'` |
| `state`, `province` | `'CA'` |
| `zip`, `zip_code`, `postal_code` | `'00000'` |
| `ssn`, `social_security_number` | `'000-00-' \|\| LPAD(CAST(id % 10000 AS VARCHAR), 4, '0')` |
| `tax_id`, `ein`, `passport_number`, `drivers_license` | `'TAX-' \|\| CAST(id AS VARCHAR)` |
| `dob`, `date_of_birth`, `birth_date`, `birthday` | `DATE '2000-01-01'` |
| `password`, `encrypted_password`, `password_digest` | `'[redacted]'` |
| `*_token`, `*_secret`, `api_key`, `secret_key`, `access_token`, `refresh_token` | `NULL` |
| `ip`, `ip_address`, `*_ip`, `last_sign_in_ip`, `current_sign_in_ip`, `remote_ip` | `NULL` |
| `user_agent`, `*_user_agent`, `ua` | `'[redacted]'` |

### gray-zone (force review)

Any column NOT matched above, when type is `text` / `varchar` / `string` / `jsonb`, AND name matches any of:

- Free-text named columns: `notes`, `description`, `bio`, `comment`, `comments`, `message`, `body`, `content`, `summary`, `feedback`
- URL-shaped: `url`, `*_url`, `referer`, `referrer`, `landing_page`, `exit_page`
- All `text` type columns regardless of name
- All `jsonb` type columns regardless of name

Gray-zone default:

- Text: `'[redacted]'`
- jsonb: `'{}'::JSON`

When user explicitly allows a gray-zone column to pass through:

- Text: keep as-is, no expression
- jsonb: `CAST(column AS JSON)` (native DuckDB JSON, not VARCHAR)

## Deterministic guarantee

Every expression in the obvious-anon table is a pure function of `id` (or a constant). Two runs against the same source row produce the same anonymized value. This makes CSV diffs across runs meaningful.

Anti-pattern (do not use):

```sql
-- WRONG: ROW_NUMBER without ORDER BY produces different values per run
'555-000-' || LPAD(CAST(ROW_NUMBER() OVER () AS VARCHAR), 4, '0')
```

Right:

```sql
'555-000-' || LPAD(CAST(id AS VARCHAR), 4, '0')
```
