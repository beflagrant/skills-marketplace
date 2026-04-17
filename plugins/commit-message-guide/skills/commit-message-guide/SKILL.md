---
name: commit-message-guide
description: "Guide for creating well-structured conventional commits. TRIGGER when: about to run `git commit`, user asks to commit or save changes to git, or drafting/reviewing a commit message. Use for single logical changes. Enforces conventional commit format, forbids AI attribution and Co-Authored-By trailers."
allowed-tools: Bash(git *)
---

# Commit Message Guide

## Body

**Only include a body when the title and file changes alone cannot reasonably convey the reason for the commit.**

Never include:
- Information visible on GitHub (files changed, lines added/removed, diff stats)
- Test status ("All tests pass")
- Time-related information (estimates, time spent)
- AI authorship or attribution — no "Generated with Claude Code", Co-Authored-By tags, emojis, or tool attribution of any kind

## Special commit types

**WIP** — no formatting required, may have failing tests:
```
WIP: debugging race condition in scheduler
```

**FIXUP** — created with `git commit --fixup=<hash>` for automatic squashing:
```
fixup! feat(api): add support for webhook callbacks
```

WIP and FIXUP commits skip all other requirements.

## When creating commits

If the work spans multiple concerns, use `purposeful-commits` first to structure the commits, then apply this guide to each individual message.

1. Draft the commit message
2. Show the draft to the user before committing
3. Ask for feedback if the commit is complex or touches multiple concerns
4. **NEVER add AI attribution** — no tool attribution of any kind
