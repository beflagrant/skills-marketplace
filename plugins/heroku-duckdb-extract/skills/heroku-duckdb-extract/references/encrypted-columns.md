# Encrypted column rules

Encrypted columns in the source DB store ciphertext, hashes, or auth artifacts. Extracting them as-is yields useless data and may leak signal. Replace per the rules below — no prompt.

## Rails 7+ ActiveRecord::Encryption

Schema.rb shows these as plain string columns. The application encrypts/decrypts via `encrypts :ssn` etc.

| Column name pattern | Action |
|---|---|
| Any column declared via `encrypts` in app code | The schema.rb name itself doesn't reveal this — skill can't detect from schema alone. Treat the column per its name (e.g., `ssn` → ssn anonymization). |

The `encrypts` declaration is invisible to the skill. If schema lists `users.ssn`, the PII patterns will anonymize it. The fact that the source value is encrypted (rather than plaintext) doesn't change what we write to the extract.

## attr_encrypted (older gem)

Pairs of columns: `encrypted_<name>` and `encrypted_<name>_iv`.

| Pattern | Action |
|---|---|
| `encrypted_*` (the ciphertext column) | Replace value with `'[encrypted]'` |
| `*_iv` (the initialization vector column) | Replace value with `NULL` |

The cleartext column name often exists in the model but not the DB. The DB has only the encrypted pair.

## Devise authentication columns

These are not encryption per se but related auth artifacts. Devise tokens and password digests should never appear in shared extract data.

| Column | Action |
|---|---|
| `encrypted_password` (bcrypt digest) | Replace with `'[redacted]'` |
| `reset_password_token` | `NULL` |
| `reset_password_sent_at` | Keep as-is (timestamp, no PII) |
| `remember_created_at` | Keep as-is |
| `confirmation_token` | `NULL` |
| `confirmed_at`, `confirmation_sent_at` | Keep as-is |
| `unlock_token` | `NULL` |
| `unconfirmed_email` | Apply email anonymization (per PII patterns) |
| `failed_attempts`, `sign_in_count` | Keep as-is (numeric, no PII) |
| `current_sign_in_at`, `last_sign_in_at` | Keep as-is (timestamps) |
| `current_sign_in_ip`, `last_sign_in_ip` | `NULL` (per IP rule in PII patterns) |

## Generic auth artifact patterns

Beyond Devise, anything matching these patterns:

| Pattern | Action |
|---|---|
| `*_token`, `*_secret`, `api_key`, `secret_key`, `access_token`, `refresh_token`, `*_api_key`, `*_access_token` | `NULL` |

Tokens are NULLed (not redacted to `'[redacted]'`) because they're typically meaningful only as live credentials — analytics has zero use for the redacted placeholder.
