---
name: adr-refine
description: Critique a draft Architecture Decision Record: surface unclear context, missing tradeoffs, and codebase inconsistencies. Auto-invoked by the adr skill; also use when the user says "review this ADR", "refine this ADR", or "is this ADR good enough to commit?"
allowed-tools: Read, Grep, Glob
---

# ADR Refiner

An ADR draft is not done when it's written — it's done when it survives a critique pass. This skill runs that pass. Its job is to make a future reader's life easier by catching the problems the author couldn't see while drafting.

This skill is the refinement half of the ADR workflow. The `adr` skill writes the draft; this skill interrogates it. Implementation work should not begin until both have run and the user has accepted the refined ADR.

## When this skill runs

- **Automatically after `adr`.** The `adr` skill's final step invokes this one on the file it just wrote. No user action required.
- **On explicit request.** "Review this ADR", "refine ADR NNNN", "is this ADR good enough to commit?", or any pointer to an existing ADR file paired with a request for critique.
- **Not for already-committed, accepted ADRs.** If the status is `Accepted` and the file is in git history, don't refine — propose a superseding ADR instead. The historical record matters.

## What to do

1. **Read the ADR file in full.** Don't skim. Note the title, status, date, and every section.
2. **Read the surrounding codebase where the ADR makes claims.** If the ADR says "we currently use X" or "the existing Y pattern", verify it. Use Grep and Read. An ADR that misdescribes the current state is worse than no ADR.
3. **Read 1-2 neighboring ADRs** if any exist, to check for contradictions, supersession gaps, or unlinked prior decisions that should be referenced.
4. **Produce structured review notes** (format below) and print them to the chat. Do not edit the file yet.
5. **Wait for the user's responses** to the questions and proposed edits. Do not apply anything until they answer.
6. **Apply accepted edits** once the user has responded. Skip or revise the ones they rejected or modified. Re-run a lighter pass if the edits were substantial.

## Review notes format

Print review notes in this exact structure. Omit a section only if it has genuinely nothing to flag — prefer saying "nothing flagged here" over silently dropping a heading, so the user knows you looked.

```markdown
## Review notes for ADR NNNN: {title}

### Unclear context
- {thing a future reader with only the code + ADR won't understand, and why}

### Missing tradeoffs
- {alternative not considered, or consequence not named, with a pointer to what's missing}

### Hand-wavy language
- {quoted phrase} → {why it's vague and what concrete version would look like}

### Codebase inconsistencies
- {claim in the ADR} vs {what the code actually shows, with file:line reference}

### Questions for you
1. {direct question about an ambiguity — do not guess}
2. ...

### Suggested edits
{concrete diffs or revised sections for the smaller fixes — not vague advice}

### Overall
{one or two sentences: is this close to commit-ready, or does it need a structural rework? Be direct.}
```

## What to look for

**Unclear context.** Will a reader five years from now, who has only the code and this ADR, understand *why a decision had to be made at all*? Context that describes the world as it will be ("we use Rails 8") rather than the world as it was ("at the time, we were choosing a framework") ages badly.

**Missing tradeoffs.** A decision with no negative consequences is suspicious. So is a decision that names only one alternative. Push on: what did we *not* pick, and why? What does this make harder or impossible?

**Hand-wavy language.** Flag hedging ("we might", "consider", "probably"), vague decisions ("use a background job system" without naming the library), and non-consequences ("more complex", "some risk"). Quote the phrase and suggest a concrete replacement.

**Codebase inconsistencies.** This is the highest-value check and the one most likely to be skipped. If the ADR says "the existing auth middleware does X", actually read the middleware. If it says "there are no background jobs today", actually grep for `ActiveJob` and `perform_later`. An ADR built on a wrong premise is worse than no ADR.

**Questions you shouldn't paper over.** If something is ambiguous, ask. Do not guess and do not fabricate context. A short list of direct questions is more valuable than a long draft that hides its assumptions.

**Link hygiene.** If this ADR supersedes or builds on a prior one, is it linked? If another ADR in the repo covers overlapping ground, flag the overlap.

## Applying edits after the user responds

- Only apply edits the user accepted. If they revised your suggestion, use their version.
- Preserve the repo's existing ADR house style (heading levels, date format, status vocabulary) — don't let your edits drift from neighboring ADRs.
- Do not silently change the status line. Status changes are a decision the user makes.
- After applying, report back with a brief summary: what changed, what was left open, and whether any of the questions are still unanswered.

## Anti-patterns to avoid

- **Rubber-stamping.** If the review notes are all "looks good", you didn't look hard enough. There is almost always a missing tradeoff or an unverified claim.
- **Rewriting the ADR unprompted.** The user drafted it (possibly via the `adr` skill) for a reason. Critique and propose — don't overwrite.
- **Fabricating codebase claims.** If you didn't actually read the file, don't say "the existing X does Y". Say "I didn't verify this — can you confirm?"
- **Burying the lede.** If the ADR has a structural problem (wrong decision, wrong framing, wrong scope), say so in **Overall** first. Don't hide it under line-level nitpicks.
- **Infinite refinement.** One good pass is the goal. If after a round of edits the ADR is still not close, say so plainly and suggest a rethink rather than a third pass.
