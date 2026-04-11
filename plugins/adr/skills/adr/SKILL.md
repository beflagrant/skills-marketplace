---
name: adr
description: Write an Architecture Decision Record (ADR), or advise whether a decision is ADR-worthy. Use when the user says "write an ADR", "record this decision", "document this architecture decision", "is this ADR-worthy?", "should we write an ADR for…", or is making a choice that affects structure, non-functional characteristics, dependencies, interfaces, or construction techniques. Also use when the user wants to backfill historical ADRs for decisions already made.
---

# ADR Writer

An Architecture Decision Record captures **why** a significant decision was made, in the context it was made in. This skill helps author ADRs that are useful to a future reader (often future-them) trying to answer: *Was this a conscious decision? Why is it this way? Can it change?*

## When to write an ADR

Only for **architecturally significant** decisions — ones that affect the structure, non-functional characteristics, dependencies, interfaces, or construction techniques of the system. Not every decision.

Good candidates:
- Choice of framework, runtime, language, or major library
- Data model shape, key schema choices, or migration strategies
- Cross-cutting patterns (auth, background jobs, caching, realtime)
- Integration boundaries with external systems
- Build, deployment, or test infrastructure shifts
- Reversing or superseding an earlier decision

Not ADR-worthy (don't write one):
- A specific bug fix
- A refactor that doesn't change structure
- Routine dependency bumps
- Local implementation details a reader can derive from code

If the user asks for an ADR on something that isn't architecturally significant, push back gently: "This looks more like an implementation detail than an architecture decision — want me to write it anyway, or drop a comment in the code instead?"

## Advisory mode

Sometimes the user isn't asking for a draft — they're asking whether a decision is ADR-worthy in the first place ("Is this ADR-worthy?", "Should we write an ADR for the auth switch?"). Handle these directly instead of jumping to drafting:

1. If the decision isn't clear from context, ask one question: "What's the decision and what made it architecturally significant?"
2. Apply the criteria above. Be specific about *which* criterion matches (or doesn't) — "this changes an integration boundary with an external system" is more useful than "yes, it's significant."
3. Give a plain yes/no with that reasoning.
4. If yes, offer to draft it now. If no, suggest the lighter-weight alternative (a code comment, a commit message, a line in the PR description) and name it specifically.

Advisory mode shares the criteria with the drafting path — don't restate them, point back to them. If the user follows up with "okay, write it," drop into the normal drafting process.

## Where ADRs live

Default locations, in order of preference:
1. `docs/adr/` (most common)
2. `doc/adr/`
3. `architecture/decisions/`
4. Repo root if none of the above exist — but ask first before creating a new directory.

Always check the repo for an existing ADR directory before assuming a path. Use Glob for `**/adr/*.md` or `**/decisions/*.md`.

## Numbering

ADRs are numbered sequentially with a 4-digit zero-padded prefix: `0001-`, `0002-`, etc.

To pick the next number:
1. List the existing ADR directory.
2. Find the highest numeric prefix.
3. Add 1, zero-pad to 4 digits.

**Gotcha:** duplicate numbers happen when branches are merged out of order. If you find two files with the same number already in the tree, note it to the user but don't try to renumber — renumbering breaks inbound links. Just use the next unused number.

## Filename format

`NNNN-kebab-case-title.md` — short, descriptive, derived from the title. Keep it under ~60 characters. Strip articles (`a`, `the`), drop punctuation, lowercase.

Examples:
- `0008-tour-data-sync.md`
- `0015-inventory-calculation-modes.md`
- `0018-product-stats-date-filter-route-date.md`

## Format

Match the style of existing ADRs in the repo if any exist — read one or two first to pick up conventions (heading level for the title, date format, status vocabulary, whether pros/cons are bulleted or prose). The template below is the minimal Nygard-style baseline; conform to the house style when there is one.

```markdown
# ADR NNNN: Title in Title Case

**Date:** YYYY-MM-DD
**Status:** Proposed | Accepted | Superseded by ADR NNNN | Deprecated

## Context

What is the situation that forced this decision? What constraints, prior
decisions, incidents, or requirements apply? What options were considered?
Why did a decision need to be made at all?

Be specific. A reader who has never seen this system should understand
*why you were in the position of needing to decide something*.

## Decision

What did you decide? State it plainly and specifically. Name the thing.
If it's a technical choice, name the version, the library, the pattern.
Avoid hedging language — "we will use X" not "we might consider X".

## Consequences

What does this make easier, harder, or impossible? Separate positive,
neutral, and negative consequences so the trade-offs are visible.

- **Positive:** ...
- **Neutral:** ...
- **Negative:** ...

A decision with no negative consequences is suspicious — keep looking.
If one of the negatives turns out to be unacceptable, that's a signal
to revisit the decision before writing the ADR.
```

Optional sections, only when they carry weight:
- `## Schema changes` — migrations, index additions, column changes
- `## Alternatives considered` — when the road not taken is itself instructive
- `## References` — links to prior ADRs, external docs, incident reports, PRs

## Process

When invoked:

1. **Confirm it's ADR-worthy.** If unsure, ask one question: "What's the decision and what made it architecturally significant?" Skip this if the user has already explained.
2. **Find the ADR directory.** Glob for existing locations. If none exists, ask before creating.
3. **Read 1-2 existing ADRs** from the repo to match house style (heading format, date format, status vocabulary, bullet conventions).
4. **Pick the next number.** Highest existing + 1, zero-padded to 4 digits.
5. **Draft the ADR** with today's date. Fill every section with real content — don't leave placeholders. If you don't know something, ask the user before drafting rather than guessing.
6. **Write the file** at the computed path.
7. **Report back** with the file path and a one-sentence summary of what was decided.
8. **Invoke the `adr-refine` skill** on the file you just wrote. The draft is not done until it has survived a critique pass. Do not move on to implementation work between steps 7 and 8 — refinement comes first.

## Writing quality

The ADR's job is to help a future reader who has *only* the code and the ADR. Write accordingly:

- **Context should survive the decision.** Describe the world as it was, not as it will be. If you write "we use Rails 8" in context, it'll read wrong in five years when Rails 12 is current. Write "at the time we were choosing a framework, we wanted..."
- **Decision should be concrete.** Not "use a background job system" but "use Solid Queue as the Active Job backend, running on a dedicated worker dyno."
- **Consequences should name real trade-offs.** "More complex" is not a consequence. "The worker dyno must be explicitly scaled on Heroku or jobs queue silently" is.
- **Link to prior ADRs** when superseding or building on them. Use relative paths: `[ADR 0011](0011-date-range-picker.md)`.
- **Be willing to be wrong later.** ADRs are a historical record. When a decision is reversed, write a new ADR that supersedes the old one — don't edit the original except to change its status line.

## Backfilling historical ADRs

If the user asks to document a decision that was already made:

- State clearly in the context that this is a historical record written after the fact.
- Use the **original** decision date if known, not today's. If unknown, use the commit date of the change that introduced it, or write "circa YYYY-MM" and say so.
- Be honest about what you don't know. "The reasoning is inferred from the commit history and code shape; original discussion is not available" is better than fabricated context.
- Mark status `Accepted` if the decision is still in force, `Superseded` if not.

## Anti-patterns to avoid

- **Decision logs masquerading as ADRs.** If every minor choice gets an ADR, the signal drowns. Aim for a handful per quarter, not dozens.
- **Restating the code.** Don't describe *what* the code does. Describe *why* it does it that way.
- **Consequence-free decisions.** If you can't name a real negative, you probably haven't thought hard enough.
- **Amending accepted ADRs.** Supersede instead. The historical record matters.
- **Vague status.** "In progress" is not a status. Use Proposed / Accepted / Superseded / Deprecated.