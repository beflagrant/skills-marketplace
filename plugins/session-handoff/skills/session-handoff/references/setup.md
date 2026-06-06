# Setup

One-time host configuration for the session-handoff skill. The agent does not need to read this file at runtime. The permissions and tests below are ergonomic; the optional SessionStart hook (last section) adds the proactive session-start surfacing that makes the skill feel automatic.

## Recommended Permissions

Claude Code's permission system prompts on every tool invocation that isn't on an allow-list. To avoid prompts during normal use of this skill, add these entries to `~/.claude/settings.json` under `permissions.allow` (or the project equivalent):

```jsonc
"Bash(python3 *skills/session-handoff/scripts/create_handoff.py *)",
"Bash(python3 *skills/session-handoff/scripts/list_handoffs.py *)",
"Bash(python3 *skills/session-handoff/scripts/validate_handoff.py *)",
"Bash(python3 *skills/session-handoff/scripts/check_staleness.py *)",
"Write(**/.claude/handoffs/*.md)",
"Write(**/.claude/handoffs/artifacts/**)",
"Edit(**/.claude/handoffs/*.md)",
"Edit(**/.claude/handoffs/artifacts/**)"
```

The leading `*` in each Bash pattern lets the rule match both in-repo (`skills/session-handoff/scripts/...`) and installed (`~/.claude/skills/...`) locations. `**` in the Write/Edit patterns matches any project's `.claude/handoffs/` directory. The separate `artifacts/**` rules cover companion files (drafts, wireframes, &c.) that the skill prescribes saving alongside handoffs — those live in the `artifacts/` subdirectory to stay out of the way of the `SessionStart` hook and `list_handoffs.py`, which only see top-level `.md` files.

Skill frontmatter does not drive permissions — `settings.json` is the only source.

## Tests

Run the script-helper unit tests from the skill directory:

```bash
python3 -m unittest discover -t skills/session-handoff -s skills/session-handoff/tests
```

Tests cover the slug sanitizer, `infer_project_root`, `_is_safe_rmtree_path`, the secret-detection patterns, and date parsing — i.e. the helpers most likely to silently regress. `pytest` is supported via the included `conftest.py` if installed.

## Proactive Surfacing (optional)

The CREATE and RESUME workflows run on demand. To also have the agent *proactively* surface a recent handoff at the start of a session — so a fresh or resumed session offers to pick up where you left off instead of waiting for you to remember — install the companion `SessionStart` hook. This is the piece that makes the skill feel automatic, and it does **not** travel with the skill directory; the skill works fully without it (you just invoke create/resume yourself).

The script lives next to this file at `hooks/recent-handoff-notice.sh` in the skill directory. It checks `.claude/handoffs/` for a handoff modified within the last 7 days (single-level — `find -maxdepth 1` — which is what makes the `artifacts/` subdir convention safe) and, if found, emits a system reminder telling the agent to offer a resume on the first turn. Treat the in-skill copy as the single source of truth — don't paste a copy elsewhere, or the two drift (the reminder text carries behavioral instructions that get refined over time).

To wire it up, add the hook to `~/.claude/settings.json` (or the project equivalent) under `hooks.SessionStart`. If you already have a `SessionStart` array, merge this entry into it rather than replacing it:

```jsonc
"SessionStart": [
  {
    "matcher": "startup|resume|clear|compact",
    "hooks": [
      { "type": "command", "command": "$HOME/.claude/skills/session-handoff/hooks/recent-handoff-notice.sh" }
    ]
  }
]
```

The command path assumes the skill is installed at `~/.claude/skills/session-handoff/`. Adjust if the skill lives elsewhere. The `matcher` fires the reminder on a new session, an explicit resume, a `/clear`, and after compaction — every point where prior context may have been lost.
