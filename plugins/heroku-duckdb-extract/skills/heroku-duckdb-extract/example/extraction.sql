-- extraction.sql
-- App: training-tracker-production
-- Env: production
-- Generated: 2026-05-15T14-30-00Z
-- Skill: heroku-duckdb-extract @ abc1234
-- NEVER includes DATABASE_URL or any credential.

-- ANONYMIZATION AUDIT TRAIL
-- Columns passing through unredacted:
--   companies.id, companies.name, companies.plan, companies.status, companies.country, companies.created_at, companies.updated_at
--   users.id, users.company_id, users.sign_in_count, users.current_sign_in_at, users.last_sign_in_at, users.role, users.created_at, users.updated_at, users.reset_password_sent_at, users.remember_created_at
--   training_courses.* (no PII; analytical reference data)
--   assignments.* (FKs, timestamps, status only — no PII)
-- Explicitly redacted to '[redacted]':
--   companies.notes (gray-zone, user did not allow)
--   users.bio (gray-zone, user did not allow)
-- Explicitly allowed to pass through:
--   users.preferences (jsonb, cast to JSON)
-- User acknowledged 2026-05-15T14:30:00Z.

CREATE OR REPLACE TABLE companies AS
SELECT
  id,
  name,
  plan,
  status,
  '[redacted]' AS notes,
  country,
  created_at,
  updated_at
FROM prod.companies;
COPY companies TO 'csvs/companies.csv' (HEADER, DELIMITER ',');

CREATE OR REPLACE TABLE users AS
SELECT
  id,
  company_id,
  'user' || CAST(id AS VARCHAR) || '@example.com' AS email,
  'First' || CAST(id AS VARCHAR) AS first_name,
  'Last' || CAST(id AS VARCHAR) AS last_name,
  '555-000-' || LPAD(CAST(id AS VARCHAR), 4, '0') AS phone,
  '[redacted]' AS encrypted_password,
  NULL AS reset_password_token,
  reset_password_sent_at,
  remember_created_at,
  sign_in_count,
  current_sign_in_at,
  last_sign_in_at,
  NULL AS current_sign_in_ip,
  NULL AS last_sign_in_ip,
  role,
  '[redacted]' AS bio,
  CAST(preferences AS JSON) AS preferences,
  created_at,
  updated_at
FROM prod.users;
COPY users TO 'csvs/users.csv' (HEADER, DELIMITER ',');

CREATE OR REPLACE TABLE training_courses AS
SELECT
  id,
  title,
  description,
  duration_minutes,
  active,
  created_at,
  updated_at
FROM prod.training_courses;
COPY training_courses TO 'csvs/training_courses.csv' (HEADER, DELIMITER ',');

-- NOTE: assignments preserves user_id and training_course_id FKs as-is.
-- If users or training_courses were filtered, orphan assignments may result.
CREATE OR REPLACE TABLE assignments AS
SELECT
  id,
  user_id,
  training_course_id,
  assigned_at,
  due_at,
  completed_at,
  status,
  created_at,
  updated_at
FROM prod.assignments;
COPY assignments TO 'csvs/assignments.csv' (HEADER, DELIMITER ',');

DETACH prod;
