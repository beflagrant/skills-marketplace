# Companion Infrastructure

What `session-handoff` depends on beyond the skill directory itself. The skill works standalone — `create_handoff.py` and the resume workflow don't need anything else — but several behaviors that make handoffs feel automatic live in files the skill *cannot* carry: rule files loaded passively each session, a `settings.json` hook, and permission allowlist entries.

## Why this file exists

A skill packages as a self-contained directory and can be installed in many ways — a personal config repo, a plugin, a marketplace install. But anything that integrates with the host — rules loaded passively each session, `settings.json` hooks, permission allowlist entries — lives *outside* the skill directory and doesn't ship with the package.

This file is the manual half: when you install `session-handoff` into a new environment, this is what to set up alongside it. Skip it and the skill still works on demand; adopt it and the handoff workflow feels automatic.

## 1. Host config: see `references/setup.md`

`references/setup.md` (which *does* sync with the skill) covers:

- The `settings.json` permission allowlist entries so the skill's scripts don't prompt on each invocation.
- The script unit tests.
- The optional `SessionStart` hook (`recent-handoff-notice.sh`) that surfaces recent handoffs at session start.

Start there for the configuration that's plumbing-level.

## 2. Companion rules (passively loaded each session)

The skill is invocation-triggered: it fires when the user (or the model) explicitly invokes it. The behaviors below are what fill the gaps *between* invocations — what the model should notice about the conversation that should lead to invoking the skill, and how to handle artifacts the skill will depend on at handoff-write time. Rules in `~/.claude/rules/` (or a project's `CLAUDE.md`) load passively each session, which is why they're the right home for ambient behavior.

Adopt as many as suit your taste. Each section gives the intent, the failure mode it prevents, and sample wording you can paste into your own rule file.

### 2a. Proactive handoff suggestion

**Intent:** the model surfaces a handoff suggestion when one of several conditions is true, not only when the user asks.

**Failure without it:** handoffs get written too late or not at all. Claude Code's `PreCompact` hook can't inject context for the model to react to (it can only block or show a user-facing message), so the model has to take responsibility for noticing.

**Sample wording:**

> Any one of these signals is enough to surface a `/session-handoff` suggestion:
>
> - 5+ file edits, multiple commits, or non-trivial decisions that wouldn't be obvious from the diff alone
> - The user pauses, switches topic, or signals winding down
> - The conversation has been long enough that compaction is plausible (extended back-and-forth, large tool outputs)
> - A new phase of work is starting that depends on context from the previous phase
>
> Bias toward suggesting earlier rather than later: false positives are cheap; a missed handoff before compaction means the context is lost.

### 2b. Handle the SessionStart reminder

**Intent:** when the `recent-handoff-notice.sh` hook surfaces a recent handoff at session start, the model knows what to do with the reminder.

**Failure without it:** the reminder either gets silently ignored (and the prior context is lost), or triggers an unwanted resume on a prompt that wasn't actually a continuation.

**Sample wording:**

> A `SessionStart` hook surfaces the most recent handoff (within 7 days) at session start. When that reminder fires, surface it to the user on the first turn and ask whether to resume — do not silently judge from the prompt alone. Phrase the question briefly (e.g., "There's a recent handoff: `<slug>`. Resume?") and let the user decide.
>
> **Exception:** if the first message already answers the question, honor it directly instead of re-asking — "resume" / "continue where we left off" → resume from the handoff; an explicit "start fresh" / "ignore the handoff" → skip it. The "don't judge from the prompt alone" guard is against *inferring* a decline from a merely unrelated-looking prompt, not against honoring an explicit instruction. A prompt that's topically unrelated but doesn't explicitly decline (e.g. "add a logout button", no mention of the handoff) still gets the question.

### 2c. Save external artifacts as they're produced

**Intent:** when the session produces an artifact that lives outside the repo — a draft message to a teammate, an ASCII wireframe in a chat window, a question put to a stakeholder — a copy gets saved under `.claude/handoffs/artifacts/` while it's still in front of the model. The skill carries this principle at handoff-write time (see `SKILL.md`); the rule carries the *timing* half. The `artifacts/` subdirectory keeps companion files out of the way of the hook and listing scripts, which only see top-level `.md` handoffs.

**Failure without it:** draft artifacts scroll out of context before the handoff is written, and the resuming session can't reason about replies like "I like B" that came in afterwards.

**Sample wording:**

> When work in a session produces an artifact that lives outside the repo — a draft message sent to a teammate, an ASCII wireframe in a chat window, a question put to a stakeholder — save a copy under `.claude/handoffs/artifacts/` while the artifact is still in front of you. The `session-handoff` skill covers how a handoff should reference these; the rule's half is timing, because by handoff-write time a chat-only draft may already be scrolled out of context.

## Adopting these in a new environment

Rough order:

1. Apply the `settings.json` entries from `references/setup.md` (permissions + optional `SessionStart` hook registration).
2. Register the `SessionStart` hook (the script ships at `hooks/recent-handoff-notice.sh` inside this skill) if you want the proactive surfacing — `references/setup.md` has the exact entry.
3. Paste the sample wording above into your rule file (`~/.claude/rules/<something>.md`, or your project's `CLAUDE.md`), editing freely. Three sections, three behaviors — adopt all or just the ones that fit.

None of these are required for the skill to function; they make the surrounding workflow feel automatic instead of on-demand.
