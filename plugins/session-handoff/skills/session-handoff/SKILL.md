---
name: session-handoff
description: "Create or resume a session handoff document. Trigger: 'create/save/load/resume handoff', 'continue where we left off', context running low, or proactively after substantial work (5+ edits, major decisions)."
metadata:
  publish: marketplace
---

# Handoff

Creates comprehensive handoff documents that enable fresh AI agents to seamlessly continue work with zero ambiguity. Solves the long-running agent context exhaustion problem.

## Mode Selection

Determine which mode applies:

**Creating a handoff?** User wants to save current state, pause work, or context is getting full.
- Follow: CREATE Workflow below

**Resuming from a handoff?** User wants to continue previous work, load context, or mentions an existing handoff.
- Follow: RESUME Workflow below

**Proactive suggestion?** After substantial work (5+ file edits, complex debugging, major decisions), suggest:
> "We've made significant progress. Consider creating a handoff document to preserve this context for future sessions. Say 'create handoff' when ready."

## CREATE Workflow

### Step 1: Generate Scaffold

Run the smart scaffold script to create a pre-filled handoff document.

**Run it from the project root, using the script's absolute path — do NOT `cd` into the skill directory.** The script derives the project root (and therefore where the handoff is written, plus the git/commit metadata it pre-fills) from the current working directory. The `scripts/...` form below is relative for brevity; if you `cd` into the skill dir to make it resolve, the handoff lands in the *skill's* repo and captures the *skill's* git state instead of your project's. Invoke it like `python3 /absolute/path/to/skills/session-handoff/scripts/create_handoff.py [task-slug]` from the project you're handing off.

```bash
python scripts/create_handoff.py [task-slug]
```

Example: `python scripts/create_handoff.py implementing-user-auth`

**Specify the chain relationship to any prior handoff** (one of three flags):

```bash
# Linear continuation — same thread of work as a prior handoff:
python scripts/create_handoff.py "auth-part-2" --continues-from 2024-01-15-auth.md

# Branch — diverged from a prior thread; both threads remain valid.
# Use when a prior handoff was surfaced this session but NOT resumed
# (declined to continue and did something else instead):
python scripts/create_handoff.py "different-thing" --branches-from 2024-01-15-auth.md

# Independent — no relationship to any prior handoff:
python scripts/create_handoff.py "new-task" --no-chain
```

If none of the three flags is passed and prior handoffs exist, the script auto-suggests the most recent as a continuation and prints a hint to rerun with the right flag. Prefer being explicit — the script can't tell whether you resumed or declined a surfaced handoff.

The script will:
- Create `.claude/handoffs/` directory if needed
- Generate timestamped filename
- Pre-fill: timestamp, project path, git branch, recent commits, modified files
- Render the chain section based on the relationship flag
- Output file path for editing

### Step 2: Complete the Handoff Document

Open the generated file and fill in all `[TODO: ...]` sections. Prioritize these sections:

1. **Current State Summary** - What's happening right now
2. **Important Context** - Critical info the next agent MUST know
3. **Immediate Next Steps** - Clear, actionable first steps
4. **Decisions Made** - Choices with rationale (not just outcomes)

Use the template structure in [references/handoff-template.md](references/handoff-template.md) for guidance.

If the handoff references artifacts that live outside the repo — a draft message sent to a teammate, an ASCII wireframe in a chat window, a question put to a stakeholder — preserve copies under `.claude/handoffs/artifacts/` and link to them from "Related Resources". The `artifacts/` subdirectory keeps these companion files out of the way of the `SessionStart` hook and `list_handoffs.py`, both of which only look at top-level `.md` files in `.claude/handoffs/`. Ideally these were saved as they were produced during the session, not at handoff-write time — by then a chat-only draft may already have scrolled out of context. A handoff that mentions "three wireframes sent to a teammate" without preserving the wireframes themselves leaves the resuming session unable to reason about a later reply like "I like B".

### Step 3: Validate the Handoff

Run the validation script to check completeness and security:

```bash
python scripts/validate_handoff.py <handoff-file>
```

The validator checks:
- [ ] No `[TODO: ...]` placeholders remaining
- [ ] Required sections present and populated
- [ ] No potential secrets detected (API keys, passwords, tokens)
- [ ] Referenced files exist
- [ ] Quality score (0-100)

**Do not finalize a handoff with secrets detected or score below 70.**

### Step 4: Confirm Handoff

Report to user:
- Handoff file location
- Validation score and any warnings
- Summary of captured context
- First action item for next session

## RESUME Workflow

### Step 1: Find Available Handoffs

List handoffs in the current project:

```bash
python scripts/list_handoffs.py
```

This shows all handoffs with dates, titles, and completion status.

### Step 2: Check Staleness

Before loading, check how current the handoff is:

```bash
python scripts/check_staleness.py <handoff-file>
```

Staleness levels:
- **FRESH**: Safe to resume - minimal changes since handoff
- **SLIGHTLY_STALE**: Review changes, then resume
- **STALE**: Verify context carefully before resuming
- **VERY_STALE**: Consider creating a fresh handoff

The script checks:
- Time since handoff was created
- Git commits since handoff
- Files changed since handoff
- Branch divergence
- Missing referenced files

### Step 3: Load the Handoff

Read the relevant handoff document completely before taking any action.

If handoff is part of a chain (has "Continues from" link), also read the linked previous handoff for full context.

### Step 4: Verify Context

Follow the checklist in [references/resume-checklist.md](references/resume-checklist.md):

1. Verify project directory and git branch match
2. Check if blockers have been resolved
3. Validate assumptions still hold
4. Review modified files for conflicts
5. Check environment state

### Step 5: Begin Work

Start with "Immediate Next Steps" item #1 from the handoff document.

Reference these sections as you work:
- "Critical Files" for important locations
- "Key Patterns Discovered" for conventions to follow
- "Potential Gotchas" to avoid known issues

### Step 6: Update or Chain Handoffs

As you work:
- Mark completed items in "Pending Work"
- Add new discoveries to relevant sections
- For long sessions: create a new handoff with `--continues-from` to chain them

## Handoff Chaining

Three distinct relationships a new handoff can declare to prior ones:

| Relationship    | When to use                                                                                                                | Renders as            |
| :-------------- | :------------------------------------------------------------------------------------------------------------------------- | :-------------------- |
| **Continues from** | Linear continuation — this session picked up where a prior handoff left off and the work stayed on that thread.            | `--continues-from`    |
| **Branches from**  | A prior handoff was surfaced this session but not resumed (declined to continue), and the new handoff captures the divergent thread that happened instead. Both threads remain valid. | `--branches-from`     |
| **Supersedes**     | This handoff replaces and invalidates one or more prior handoffs. Filled into the chain section as a list, not via a CLI flag. | (manual list)         |

A typical lineage:

```
handoff-1.md (initial work)
    ↓
handoff-2.md --continues-from handoff-1.md   (same thread)
    ↘
     handoff-3.md --branches-from handoff-2.md   (diverged: surfaced but not resumed)
```

When resuming from a chain, read the most recent handoff first, then reference predecessors as needed. A **Branches from** link signals there's a parallel thread that may still need attention.

### Deciding which flag to use

If the SessionStart hook surfaced a recent handoff this session:
- **Resumed it and continued the work?** → `--continues-from <that-handoff>`
- **Declined to resume and did something different?** → `--branches-from <that-handoff>`
- **No handoff was surfaced, or surfaced one is irrelevant?** → `--no-chain` (or `--continues-from` if you genuinely chose to continue an older one)

## Storage Location

Handoffs are stored in: `.claude/handoffs/`

Naming convention: `YYYY-MM-DD-HHMMSS-[slug].md`

Example: `2024-01-15-143022-implementing-auth.md`

## Resources

The scripts below require a **Python 3.9+** interpreter. They exit with a clear error if invoked on an older version.

### scripts/

| Script | Purpose |
|--------|---------|
| `create_handoff.py [slug] [--continues-from <file> \| --branches-from <file> \| --no-chain]` | Generate new handoff with smart scaffolding |
| `list_handoffs.py [path]` | List available handoffs in a project |
| `validate_handoff.py <file>` | Check completeness, quality, and security |
| `check_staleness.py <file>` | Assess if handoff context is still current |

### references/

- [handoff-template.md](references/handoff-template.md) - Complete template structure with guidance
- [resume-checklist.md](references/resume-checklist.md) - Verification checklist for resuming agents
- [setup.md](references/setup.md) - One-time host setup: recommended permissions and how to run the tests
