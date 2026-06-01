# Setup

One-time host configuration for the session-handoff skill. None of this affects how the skill runs once configured; the agent does not need to read this file at runtime.

## Recommended Permissions

Claude Code's permission system prompts on every tool invocation that isn't on an allow-list. To avoid prompts during normal use of this skill, add these entries to `~/.claude/settings.json` under `permissions.allow` (or the project equivalent):

```jsonc
"Bash(python3 *skills/session-handoff/scripts/create_handoff.py *)",
"Bash(python3 *skills/session-handoff/scripts/list_handoffs.py *)",
"Bash(python3 *skills/session-handoff/scripts/validate_handoff.py *)",
"Bash(python3 *skills/session-handoff/scripts/check_staleness.py *)",
"Write(**/.claude/handoffs/*.md)",
"Edit(**/.claude/handoffs/*.md)"
```

The leading `*` in each Bash pattern lets the rule match both in-repo (`skills/session-handoff/scripts/...`) and installed (`~/.claude/skills/...`) locations. `**` in the Write/Edit patterns matches any project's `.claude/handoffs/` directory.

Skill frontmatter does not drive permissions — `settings.json` is the only source.

## Tests

Run the script-helper unit tests from the skill directory:

```bash
python3 -m unittest discover -t skills/session-handoff -s skills/session-handoff/tests
```

Tests cover the slug sanitizer, `infer_project_root`, `_is_safe_rmtree_path`, the secret-detection patterns, and date parsing — i.e. the helpers most likely to silently regress. `pytest` is supported via the included `conftest.py` if installed.
