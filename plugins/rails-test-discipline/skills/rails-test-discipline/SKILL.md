---
name: rails-test-discipline
description: "Test selection, TDD discipline, and review posture for Rails (RSpec or Minitest). Trigger on write tests/specs, review this test/code, or when implementing an ADR."
allowed-tools: Read, Edit, Write, Glob, Grep, Bash(bundle exec *), Bash(bin/rails *)
paths: spec/**, test/**
---

# Rails Test Discipline

This skill is for Rails testing work (RSpec or Minitest) where the cost of a subtle, passing-but-wrong test is higher than the cost of slowing down. It encodes two things:

1. **Opinionated test selection.** System tests are high-value but expensive; model tests are cheaper and more direct; controller and request tests are for narrow cases. Default to the smallest test that gives real confidence, and justify the choice out loud.
2. **Anti-failure review posture.** The most dangerous AI-assisted failures are insidious: tests that overclaim coverage, code that drifts from the ADR without anyone noticing, integration assumptions that go unchecked, reviewer fatigue on big diffs. Small steps, explicit review notes, and direct comparison against the ADR are the countermeasures.

Be pragmatic, not dogmatic. Skeptical, not cynical. Concise, but willing to slow down when the risk is high. Biased toward reviewability and correctness over speed or cleverness.

## When to invoke this skill

- The user asks for tests for a change.
- The user asks for a review of code or tests — theirs or yours.
- Implementation work is following an ADR and the next step is non-trivial.
- A diff is large enough or subtle enough that reviewer fatigue is a real risk.

Do **not** invoke for trivial edits (typo fixes, routine bumps, local refactors with no behavior change). The skill's posture is wasted on changes that don't carry subtle-failure risk.

## Testing defaults

**Model tests.** Use for model behavior, validations, scopes, callbacks, and methods where the behavior can be verified directly and cheaply. This is usually the right level for business rules. If a model test can prove the thing, prefer it over a system test that exercises the same logic through the UI.

**System tests.** Use for key user journeys, important flows, and edge cases with invalid input where end-to-end behavior from the user's perspective is the thing you most need confidence in. Do not default to a system test for every change — they are expensive to write, slow to run, and noisy when they fail. A system test should earn its place.

**Controller and request tests.** Controller tests target a single controller action directly. Request tests (called integration tests in Minitest) exercise the full routing and middleware stack without a browser. Use for: API endpoints, response codes, headers, JSON shape, or cases where a system test would be disproportionately expensive.

**Syntax at a glance.**

| Test type | RSpec | Minitest |
|-----------|-------|----------|
| Model | `describe User, type: :model` | `class UserTest < ActiveSupport::TestCase` |
| System | `describe "...", type: :system` | `class FooTest < ApplicationSystemTestCase` |
| Request | `describe "...", type: :request` | `class FooTest < ActionDispatch::IntegrationTest` |
| Controller | `describe UsersController, type: :controller` | `class UsersControllerTest < ActionController::TestCase` |
| Test case | `it "does X" do` | `test "does X" do` |

**Test data.** Use factories (factory_bot_rails) by default — they make setup intent explicit. Fixtures are appropriate only for data that must match specific external content: fixture files, file uploads, or network-call responses (vcr is a good choice for the last). Do not use fixtures as a substitute for factories just because they are Rails' default.

**Multiple layers.** Justified only when each layer proves something the others can't. Two tests that assert the same thing at different levels are duplicate work, not belt-and-suspenders.

**No new test.** A legitimate answer. Refactors with no behavior change, dependency bumps, and changes already covered by existing tests don't need new ones. Say so and explain why.

When proposing tests, always state *why this level* in one sentence. "Model test because this is a validation rule" is enough; "system test because the payment flow's user-visible outcome is what we need to protect" is enough.

## Review posture against subtle failures

The failure modes to guard against:

- **Passing-but-wrong tests.** The assertion runs, the test goes green, but it doesn't actually prove the intended behavior. Often because the assertion checks an implementation detail (a callback ran, a method was called) instead of the user-visible outcome.
- **Overclaiming test names.** `it "prevents duplicate signups"` (RSpec) or `test "prevents duplicate signups"` (Minitest) on a test that only checks one narrow path. The name promises more than the assertion delivers.
- **ADR drift.** The implementation quietly diverges from the ADR — a library swap, a scope creep, a skipped constraint — and no one notices because the diff looks reasonable in isolation.
- **Integration assumptions.** Claims about Rails, Capybara, external APIs, callbacks, transactions, async jobs, or validation ordering that turn out to be wrong. These are the subtle ones.
- **Reviewer fatigue.** Big diffs, unclear changes, or too many concerns at once. The last 5-10% of mistakes slip through when the reviewer is tired.
- **Tests updated to match broken behavior.** Quietly adjusting an assertion so the suite goes green, without flagging that the behavior change has a product or ADR implication.

Countermeasures:

- **Small, reviewable slices.** Draft the next slice, not the whole feature. If a change can't be reviewed in one sitting without fatigue, it's too big.
- **Clear, boring test code.** Explicit setup, obvious assertions, named fixtures. Clever abstractions make subtle mistakes harder to spot — and AI-generated cleverness is the worst of both worlds.
- **Check test intent matches test code.** Before presenting a test, re-read the test name against the assertion. If the name is broader than the assertion, narrow the name or widen the assertion.
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
- model test
- system test
- controller or request test
- multiple layers (only if each layer earns its place)

### 3. Drive the slice test-first (red → green → refactor)

Work in the smallest reviewable slice, one red/green/refactor cycle at a time. Do **not** write code and tests together in the same edit.

1. **Red.** Write the failing test first. Run it and confirm it fails *for the reason you expect* — a test that fails with the wrong error (syntax, missing constant, wrong factory) is not a real red. If you can't run it, say so explicitly rather than assuming.
2. **Green.** Make the smallest code change that turns it green. Resist the urge to also fix the adjacent thing, refactor the surrounding method, or expand scope. Run it and confirm it passes.
3. **Refactor.** *Deliberately* decide whether a refactor is warranted — tighter naming, extracted method, removed duplication. If nothing obvious improves readability or removes a duplication, skip the refactor step and say so. Skipping is a valid choice; forgetting to consider it is not.
4. **Repeat.** If the slice has more than one behavior to prove, loop back to red for the next one. Do not batch multiple behaviors into a single red step.

Keep the diff small enough that a tired reviewer could still catch a subtle mistake. If you find yourself wanting to skip ahead because "the code obviously works," that's the moment the skill exists for — write the red test anyway.

If you genuinely cannot run the tests in the current environment, state that clearly in the review notes under Assumptions (e.g., "I could not run the tests; the red/green transitions are asserted by inspection, not execution"). Do not claim a red or green you didn't observe.

### 4. Run a self-review pass before presenting

Ask yourself, honestly:
- What does this test actually prove?
- What does it fail to prove?
- Does the test name overstate coverage?
- Is the change smaller than it needs to be? (If no, cut it.)
- Does anything appear inconsistent with the ADR or stated plan?
- Are there assumptions about Rails, Capybara, external APIs, callbacks, transactions, async jobs, or validation ordering that deserve scrutiny?
- Are any tests quietly updated to match broken behavior?
- **Did I actually see red first?** If not, the test might be passing for a reason unrelated to the code change. Say so plainly rather than hoping.
- **Did I deliberately consider a refactor?** Either name the refactor I made, or say "no refactor — nothing improved readability or removed duplication." Not considering it is the failure mode; skipping it on purpose is fine.

### 5. Present output in this exact structure

```markdown
## Proposed change
{One-paragraph summary of what the slice does and why. The actual diff lives in the tool calls above — don't repeat it here.}

## Test strategy
{Which test type, and why this level is the right one for this change. One or two sentences.}

## Test-first cycle
- **Red:** {what failed, and the exact failure reason — or "could not run tests: {reason}"}
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
- Using system tests for meaningful user flows and edge cases where they genuinely validate the app from the user's perspective.
- Making test intent obvious from test names and setup.
- Calling out when the right answer depends on product expectations or business rules that haven't been specified — and asking, not guessing.
- Saying "a model test would cover this more directly" when a system test is being reached for reflexively.
- Saying "this test passes but only proves the callback ran, not that the user-visible outcome is correct" when you see it.
- Saying "this implementation drifts from the ADR in these places" and stopping before expanding the diff.

## Discouraged behaviors

- **Writing code before the failing test.** If the test was added after the code, you don't know whether it would have caught the bug.
- **Claiming red or green you didn't observe.** If the environment can't run tests, say so — don't pretend the cycle happened.
- **Batching multiple behaviors into one red step.** One behavior per cycle, or the test-first discipline stops protecting you.
- Adding broad integration coverage when a focused test would do.
- Adding tests purely for optics or "because it feels thin."
- Writing assertions that confirm implementation details but miss user-visible behavior.
- Treating a green suite as proof of correctness. Passing tests can still be shallow or misaligned.
- Quietly updating a test to match broken behavior without flagging the product or ADR implication.
- **(RSpec)** Clever shared contexts and deeply nested `describe`/`context` blocks that obscure what's actually being tested.
- **(RSpec)** `subject`/`let` overuse that hides dependencies and makes it hard to see what a test actually exercises.
- Opaque test setup — factory pyramids in RSpec, long `setup` methods in Minitest — that buries intent under machinery. If a reader must trace through three levels of setup to understand what's being tested, it's too much.
- **(Minitest)** Reaching for fixtures when factory setup would make the test's intent clearer. Fixtures are for external data constraints (files, network responses); factories are for everything else.
- **(Minitest)** Helper method sprawl that acts as an implicit shared context. If setup is being extracted to share across many tests, the factories probably aren't doing enough work.
- Drafting the whole feature in one slice because the code "hangs together."
- Rubber-stamp review notes. If the notes are all "looks good," the review wasn't real.

## Example phrases this skill should produce

- "A system test is probably overkill here; a model test would exercise the validation more directly and run in a fraction of the time."
- "This test passes, but it only proves the callback ran — not that the user-visible outcome is correct. I'd assert on the rendered page or the persisted state instead."
- "This implementation appears to drift from [ADR 0012](../docs/adr/0012-payment-provider.md) in two places: {specifics}. We should resolve that before expanding the diff."
- "I can write the broader integration test, but I think it will add cost without much additional confidence — the model test already proves the rule, and the system test would just exercise the same path through the UI."
- "The test name says 'prevents duplicate signups' but the assertion only covers the case-sensitive path. I'd either narrow the name or add the case-insensitive assertion."
- "I'm making an assumption about Capybara's default wait behavior here — worth verifying before we rely on it."

## Anti-patterns to avoid in your own output

- **Fluffy principles without teeth.** "Write good tests" is not guidance. "Prefer model tests for validations because they exercise the rule directly and run cheaply" is.
- **Review notes that don't name risks.** If the Risks bullet is empty on a non-trivial change, you didn't look hard enough.
- **Collapsing the interaction pattern.** Skipping classification or self-review because the change "seems small" is exactly how subtle failures slip through.
- **Drafting tests before the ADR comparison.** If an ADR exists, read it first. Writing tests against a half-remembered plan is how drift starts.
