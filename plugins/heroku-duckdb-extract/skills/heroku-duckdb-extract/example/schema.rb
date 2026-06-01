# Example schema for a fictitious training-compliance SaaS.
# This file is shipped with the heroku-duckdb-extract skill as a reference
# example. The corresponding extraction.sql lives alongside it.

ActiveRecord::Schema[7.1].define(version: 2026_05_10_120000) do
  enable_extension "plpgsql"

  create_table "companies", force: :cascade do |t|
    t.string "name", null: false
    t.string "plan", default: "free", null: false
    t.string "status", default: "active", null: false
    t.text "notes"
    t.string "country", default: "US"
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
  end

  create_table "users", force: :cascade do |t|
    t.bigint "company_id", null: false
    t.string "email", null: false
    t.string "first_name"
    t.string "last_name"
    t.string "phone"
    t.string "encrypted_password", default: "", null: false
    t.string "reset_password_token"
    t.datetime "reset_password_sent_at"
    t.datetime "remember_created_at"
    t.integer "sign_in_count", default: 0, null: false
    t.datetime "current_sign_in_at"
    t.datetime "last_sign_in_at"
    t.inet "current_sign_in_ip"
    t.inet "last_sign_in_ip"
    t.string "role", default: "trainee", null: false
    t.text "bio"
    t.jsonb "preferences", default: {}
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.index ["company_id"], name: "index_users_on_company_id"
    t.index ["email"], name: "index_users_on_email", unique: true
  end

  create_table "training_courses", force: :cascade do |t|
    t.string "title", null: false
    t.text "description"
    t.integer "duration_minutes"
    t.boolean "active", default: true
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
  end

  create_table "assignments", force: :cascade do |t|
    t.bigint "user_id", null: false
    t.bigint "training_course_id", null: false
    t.datetime "assigned_at", null: false
    t.datetime "due_at"
    t.datetime "completed_at"
    t.string "status", default: "pending", null: false
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.index ["training_course_id"], name: "index_assignments_on_training_course_id"
    t.index ["user_id"], name: "index_assignments_on_user_id"
  end

  add_foreign_key "users", "companies"
  add_foreign_key "assignments", "training_courses"
  add_foreign_key "assignments", "users"
end
