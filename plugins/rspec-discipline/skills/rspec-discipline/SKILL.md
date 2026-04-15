---
name: rspec-discipline
description: RSpec test selection and code review for Rails + ADR workflows. Trigger on "write specs", "review this test", "review this code", or when implementing an ADR.
---

# Spec Review

This skill is for Rails + RSpec work where the cost of a subtle, passing-but-wrong test is higher than the cost of slowing down. It encodes two things:

1. **Opinionated test selection.** System specs are high-value but expensive; model specs are cheaper and more direct; request specs are for narrow cases. Default to the smallest test that gives real confidence, and justify the choice out loud.
2. **Anti-failure review posture.** The most dangerous AI-assisted failures are insidious: tests that overclaim coverage, code that drifts from the ADR without anyone noticing, integration assumptions that go unchecked, reviewer fatigue on big diffs. Small steps, explicit review notes, and direct comparison against the ADR are the countermeasures.

Be pragmatic, not dogmatic. Skeptical, not cynical. Concise, but willing to slow down when the risk is high. Biased toward reviewability and correctness over speed or cleverness.

## When to invoke this skill

- The user asks for tests for a change.
- The user asks for a review of code or tests — theirs or yours.
- Implementation work is following an ADR and the next step is non-trivial.
- A diff is large enough or subtle enough that reviewer fatigue is a real risk.

Do **not** invoke for trivial edits (typo fixes, routine bumps, local refactors with no behavior change). The skill's posture is wasted on changes that don't carry subtle-failure risk.

## Testing defaults

**System specs.** Use for key user journeys, important flows, and edge cases with invalid input where end-to-end behavior from the user's perspective is the thing you most need confidence in. Do not default to a system spec for every change — they are expensive to write, slow to run, and noisy when they fail. A system spec should earn its place.

**Model specs.** Use for model behavior, validations, scopes, callbacks, and methods where the behavior can be verified directly and cheaply. This is usually the right level for business rules. If a model spec can prove the thing, prefer it over a system spec that exercises the same logic through the UI.

**Request specs.** Use mainly for: legacy fat controllers, API-only apps, or cases where a system spec would be awkward or disproportionately expensive (e.g., verifying response codes, headers, or JSON shape without needing a browser).

**Multiple layers.** Justified only when each layer proves something the others can't. Two tests that assert the same thing at different levels are duplicate work, not belt-and-suspenders.

**No new test.** A legitimate answer. Refactors with no behavior change, dependency bumps, and changes already covered by existing specs don't need new ones. Say so and explain why.

When proposing tests, always state *why this level* in one sentence. "Model spec because this is a validation rule" is enough; "system spec because the payment flow's user-visible outcome is what we need to protect" is enough.

## Review posture against subtle failures

The failure modes to guard against:

- **Passing-but-wrong tests.** The assertion runs, the test goes green, but it doesn't actually prove the intended behavior. Often because the assertion checks an implementation detail (a callback ran, a method was called) instead of the user-visible outcome.
- **Overclaiming descriptions.** `it "prevents duplicate signups"` on a test that only checks one narrow path. The name promises more than the assertion delivers.
- **ADR drift.** The implementation quietly diverges from the ADR — a library swap, a scope creep, a skipped constraint — and no one notices because the diff looks reasonable in isolation.
- **Integration assumptions.** Claims about Rails, Capybara, external APIs, callbacks, transactions, async jobs, or validation ordering that turn out to be wrong. These are the subtle ones.
- **Reviewer fatigue.** Big diffs, unclear changes, or too many concerns at once. The last 5-10% of mistakes slip through when the reviewer is tired.
- **Tests updated to match broken behavior.** Quietly adjusting an assertion so the suite goes green, without flagging that the behavior change has a product or ADR implication.

Countermeasures:

- **Small, reviewable slices.** Draft the next slice, not the whole feature. If a change can't be reviewed in one sitting without fatigue, it's too big.
- **Clear, boring test code.** Explicit setup, obvious assertions, named fixtures. Clever abstractions make subtle mistakes harder to spot — and AI-generated cleverness is the worst of both worlds.
- **Check test intent matches test code.** Before presenting a test, re-read the `it` description against the assertion. If the description is broader than the assertion, narrow the description or widen the assertion.
- **Compare implementation against the ADR.** If an ADR exists for this work, read it before implementing and again before presenting. Name the ADR sections the change implements. If you find drift, **stop and surface it** — do not paper over it.
- **Name assumptions out loud.** In the review notes, list the framework/library/integration assumptions the change depends on. If any of them are load-bearing and unverified, say so.

## Interaction pattern

When this skill is active, respond in this order. Do not skip steps, and do not collapse them.

### 1. Classify the change

State which of these the change is, in one line:
- **behavior change** (new or changed user-visible behavior)
- **bug fix** (restoring intended behavior)
- **refactor** (no behavior change)
- **integration change** (touching an external service, framework boundary, or library)
- **architectural change** (should have an ADR; if it doesn't, say so)

A change can be two of these at once — e.g., "bug fix + integration change." Say both.

### 2. Recommend the test level

Pick one (or a justified combination) and explain why in one sentence:
- no new test
- model spec
- system spec
- request spec
- multiple layers (only if each layer earns its place)

### 3. Drive the slice test-first (red → green → refactor)

Work in the smallest reviewable slice, one red/green/refactor cycle at a time. Do **not** write code and tests together in the same edit.

1. **Red.** Write the failing spec first. Run it and confirm it fails *for the reason you expect* — a test that fails with the wrong error (syntax, missing constant, wrong factory) is not a real red. If you can't run the spec, say so explicitly rather than assuming.
2. **Green.** Make the smallest code change that turns the spec green. Resist the urge to also fix the adjacent thing, refactor the surrounding method, or expand scope. Run the spec and confirm it passes.
3. **Refactor.** *Deliberately* decide whether a refactor is warranted — tighter naming, extracted method, removed duplication. If nothing obvious improves readability or removes a duplication, skip the refactor step and say so. Skipping is a valid choice; forgetting to consider it is not.
4. **Repeat.** If the slice has more than one behavior to prove, loop back to red for the next one. Do not batch multiple behaviors into a single red step.

Keep the diff small enough that a tired reviewer could still catch a subtle mistake. If you find yourself wanting to skip ahead because "the code obviously works," that's the moment the skill exists for — write the red test anyway.

If you genuinely cannot run the specs in the current environment, state that clearly in the review notes under Assumptions (e.g., "I could not run the spec; the red/green transitions are asserted by inspection, not execution"). Do not claim a red or green you didn't observe.

### 4. Run a self-review pass before presenting

Ask yourself, honestly:
- What does this test actually prove?
- What does it fail to prove?
- Does the `it` description overstate coverage?
- Is the change smaller than it needs to be? (If no, cut it.)
- Does anything appear inconsistent with the ADR or stated plan?
- Are there assumptions about Rails, Capybara, external APIs, callbacks, transactions, async jobs, or validation ordering that deserve scrutiny?
- Are any tests quietly updated to match broken behavior?
- **Did I actually see red first?** If not, the spec might be passing for a reason unrelated to the code change. Say so plainly rather than hoping.
- **Did I deliberately consider a refactor?** Either name the refactor I made, or say "no refactor — nothing improved readability or removed duplication." Not considering it is the failure mode; skipping it on purpose is fine.

### 5. Present output in this exact structure

```markdown
## Proposed change
{One-paragraph summary of what the slice does and why. The actual diff lives in the tool calls above — don't repeat it here.}

## Test strategy
{Which spec type, and why this level is the right one for this change. One or two sentences.}

## Test-first cycle
- **Red:** {what failed, and the exact failure reason — or "could not run specs: {reason}"}
- **Green:** {what change made it pass}
- **Refactor:** {what was tightened, or "skipped — nothing obvious to improve"}

## Review notes
- **Assumptions:** {framework/library/integration assumptions this depends on}
- **What the tests prove:** {the actual coverage, narrowly stated}
- **What the tests don't prove:** {the gaps — be honest}
- **ADR alignment:** {which ADR section this maps to, or "no ADR drift detected," or "drift found: {specifics}"}
- **Risks:** {places the change could be subtly wrong}

## Open questions
1. {direct question about an ambiguity — do not guess the answer}
2. ...
```

If there are no open questions, say "None" — don't fabricate some for shape.

## Encouraged behaviors

- **Test-driven:** red first, then green, then a deliberate refactor decision. One behavior per cycle.
- Writing the smallest set of tests that give real confidence.
- Using system specs for meaningful user flows and edge cases where they genuinely validate the app from the user's perspective.
- Making test intent obvious from example names and setup.
- Calling out when the right answer depends on product expectations or business rules that haven't been specified — and asking, not guessing.
- Saying "a model spec would cover this more directly" when a system spec is being reached for reflexively.
- Saying "this test passes but only proves the callback ran, not that the user-visible outcome is correct" when you see it.
- Saying "this implementation drifts from the ADR in these places" and stopping before expanding the diff.

## Discouraged behaviors

- **Writing code before the failing spec.** If the test was added after the code, you don't know whether it would have caught the bug.
- **Claiming red or green you didn't observe.** If the environment can't run specs, say so — don't pretend the cycle happened.
- **Batching multiple behaviors into one red step.** One behavior per cycle, or the test-first discipline stops protecting you.
- Adding broad integration coverage when a focused test would do.
- Adding tests purely for optics or "because it feels thin."
- Writing assertions that confirm implementation details but miss user-visible behavior.
- Treating a green suite as proof of correctness. Passing tests can still be shallow or misaligned.
- Quietly updating a test to match broken behavior without flagging the product or ADR implication.
- Clever shared contexts, deeply nested `describe` blocks, and factory pyramids that obscure what's actually being tested.
- Drafting the whole feature in one slice because the code "hangs together."
- Rubber-stamp review notes. If the notes are all "looks good," the review wasn't real.

## Example phrases this skill should produce

- "A system spec is probably overkill here; a model spec would exercise the validation more directly and run in a fraction of the time."
- "This test passes, but it only proves the callback ran — not that the user-visible outcome is correct. I'd assert on the rendered page or the persisted state instead."
- "This implementation appears to drift from [ADR 0012](../docs/adr/0012-payment-provider.md) in two places: {specifics}. We should resolve that before expanding the diff."
- "I can write the broader integration spec, but I think it will add cost without much additional confidence — the model spec already proves the rule, and the system spec would just exercise the same path through the UI."
- "The `it` description says 'prevents duplicate signups' but the assertion only covers the case-sensitive path. I'd either narrow the description or add the case-insensitive assertion."
- "I'm making an assumption about Capybara's default wait behavior here — worth verifying before we rely on it."

## Anti-patterns to avoid in your own output

- **Fluffy principles without teeth.** "Write good tests" is not guidance. "Prefer model specs for validations because they exercise the rule directly and run cheaply" is.
- **Review notes that don't name risks.** If the Risks bullet is empty on a non-trivial change, you didn't look hard enough.
- **Collapsing the interaction pattern.** Skipping classification or self-review because the change "seems small" is exactly how subtle failures slip through.
- **Drafting tests before the ADR comparison.** If an ADR exists, read it first. Writing tests against a half-remembered plan is how drift starts.
