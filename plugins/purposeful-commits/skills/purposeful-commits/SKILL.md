---
name: purposeful-commits
description: "Structure staged and unstaged changes into purposeful, logical commits. TRIGGER when: working tree contains changes spanning multiple concerns, or user asks to commit, structure commits, or organize changes. DO NOT trigger when the work is a single logical change — use commit-message-guide alone in that case."
allowed-tools: Bash(git *)
metadata:
  publish: marketplace
---

# Purposeful Commits

Structure Git history as a clear, coherent story of how the codebase evolved — not a development diary, not a single squashed blob. Each commit is a **logical step forward** with a singular purpose.

This skill implements the approach described in Chris Arcand's "Purposeful Commits": break work into the smallest commits that each represent a complete, meaningful change. Follow Kent Beck's principle: *make the change easy (which may be hard), then make the easy change.*

## When this skill runs

- The user asks to commit, structure commits, or organize changes
- The user has completed work that spans multiple concerns (refactoring + feature + config, etc.)
- The user says "purposeful commits" or asks to break changes into logical commits

If `commit-message-guide` is also active, this skill runs first to structure the work into logical commits; `commit-message-guide` then applies to each individual commit message.

## The commit taxonomy

Changes almost always fall into these categories. Each category should be its own commit:

1. **Refactoring** — structural changes that prepare the codebase for new work without changing behavior. Extracts interfaces, moves files, renames, simplifies. These come *first*.
2. **Feature / fix** — the actual new behavior or bug fix. Should be simpler because the refactoring already happened.
3. **Supporting changes** — configuration, dependency, timeout, or policy changes driven by the feature. Isolate these with clear rationale in the commit message explaining *why*.

Not every PR needs all three. Most PRs yield **1–3 commits**, occasionally up to 10 for larger changes.

## Process

When invoked:

1. **Assess the working tree.** Run `git diff --stat` and `git diff --cached --stat` to see all staged and unstaged changes. Also run `git status` to find untracked files. Read the changed files to understand what each change does.

2. **Classify each change.** Group the changes by purpose:
   - Refactoring (structural prep, no behavior change)
   - Feature or fix (new behavior, bug fix)
   - Supporting (config, deps, policy changes driven by the feature)
   - Tests (group with the commit they verify — tests for the refactor go with the refactor commit, tests for the feature go with the feature commit)
   - Cleanup (formatting, typos, dead code removal — only if unrelated to the main work)

3. **Propose a commit plan.** Present the user with an ordered list of commits, each with:
   - A draft commit message (subject + body)
   - The files (or hunks) that belong in that commit
   - Why this is a separate commit

   Print the plan and **wait for the user to approve or adjust** before executing anything.

4. **Execute the plan.** For each approved commit, stage the relevant files and create the commit. Use `git add <specific-files>` — never `git add -A` or `git add .`. If changes within a single file need to be split across commits, use `git add -p` or explain to the user which hunks to stage.

5. **Verify.** After all commits, run `git log --oneline -n <count>` to show the result.

## Commit message quality

Every commit message should explain **why**, not just **what**. The diff already shows what changed.

**Subject line:**
- Imperative mood ("Extract authenticator interface", not "Extracted" or "Extracts")
- Under 72 characters
- No trailing period
- Conventional commit prefixes (`feat:`, `fix:`, `refactor:`, `chore:`, `docs:`, `test:`) are compatible but optional — follow the repo's existing convention. Check `git log --oneline -20` for the project's style.

**Body (when needed):**
- Blank line after subject
- Wrap at 72 characters
- Explain the *motivation* — why this change was made separately, what it enables, what constraint or decision drove it
- For supporting changes especially, document the rationale ("Increase session timeout to 120 minutes because Google OAuth token refresh requires longer-lived sessions")

**Bad commit messages to avoid:**
- "WIP", "wip", "work in progress"
- "oops", "fix", "fix tests", "forgot this file"
- "misc changes", "updates", "stuff"
- Auto-generated squash messages that just list prior commits

## Rules

- **Tests must pass at each commit.** Every commit should leave the codebase in a working state. Don't commit a refactor that breaks tests and then fix them in the next commit.
- **Don't mix concerns.** A refactoring commit should not sneak in new behavior. A feature commit should not reorganize unrelated code.
- **Order matters.** Refactoring comes before the feature it enables. Supporting changes come after the feature they support.
- **Smaller is better, but not artificially small.** A commit should be the smallest unit that is *complete and meaningful*. Don't split a single logical change across commits just to hit a count.
- **Before proposing to combine commits, check what they actually touch.** Run `git show --stat <hash>` on each commit. Two commits with similar messages may span different files and different scopes — making them wrong to combine. Conversely, two commits touching different files may still be part of the same logical change. If the file list isn't conclusive, read the actual diffs. **This only applies to local, unpublished commits** — never restructure history that has already been pushed.
- **Respect the project's existing conventions.** Check `git log` for commit message style, prefixes, and patterns before proposing something different.

## What this skill does NOT do

- **Force a specific number of commits.** If the work is genuinely one logical change, one commit is correct.
- **Rewrite history that's already pushed.** This skill structures *new* commits from working tree changes. It does not rebase or amend published history unless the user explicitly asks.
- **Squash or merge.** This is the opposite of squashing. If the user wants to squash, that's a different request.

## Example

A user has been working on adding Google OAuth support. Their working tree has:

- Extracted an `Authenticator` interface from the existing auth code (refactoring)
- Implemented Google OAuth using the new interface (feature)
- Increased session timeout from 30 to 120 minutes (supporting change)
- Added tests for all of the above

The skill would propose three commits:

```
1. refactor: Extract pluggable Authenticator interface

   Separate the authentication logic into a pluggable interface so that
   new providers can be added without modifying the core auth flow.

   Files: app/auth/authenticator.rb, app/auth/password_provider.rb,
          test/auth/authenticator_test.rb

2. feat: Add Google OAuth provider

   Implement Google OAuth as a new authentication provider using the
   Authenticator interface extracted in the previous commit.

   Files: app/auth/google_provider.rb, config/oauth.yml,
          test/auth/google_provider_test.rb

3. chore: Increase session timeout to 120 minutes

   Google OAuth token refresh requires longer-lived sessions. The
   previous 30-minute timeout caused users to be logged out before
   their OAuth token could be refreshed, resulting in a broken
   re-authentication flow.

   Files: config/session.yml
```
