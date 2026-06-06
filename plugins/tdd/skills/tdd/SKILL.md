---
name: tdd
description: "TDD via red-green-refactor. Use when implementing features test-first, or asking about mocking strategy, test doubles, stubbing external services, or testable interface design."
allowed-tools: Read, Edit, Write, Glob, Grep, Bash(bundle exec *), Bash(bin/rails *), Bash(npm test*), Bash(npx *), Bash(pytest *)
paths: spec/**, test/**, tests/**, __tests__/**
metadata:
  publish: marketplace
---

# Test-Driven Development

This skill is language-agnostic. Code examples are TypeScript for illustration — translate patterns to your project's language.

For Rails projects, use this skill alongside `rails-test-discipline`. This skill covers general TDD principles (red→green→refactor, vertical slices, mocking boundaries, public interface testing). `rails-test-discipline` handles test-level selection (model vs. system vs. request), factory/fixture guidance, and Rails-specific mechanics.

## Philosophy

**Core principle**: Tests should verify behavior through public interfaces, not implementation details. Code can change entirely; tests shouldn't.

**Good tests** are integration-style: they exercise real code paths through public APIs. They describe _what_ the system does, not _how_ it does it. A good test reads like a specification - "user can checkout with valid cart" tells you exactly what capability exists. These tests survive refactors because they don't care about internal structure.

**Bad tests** are coupled to implementation. They mock internal collaborators, test private methods, or verify state through back-channel means (like a raw SQL query) instead of through the public interface. Note: using a real database is correct — the problem is bypassing the interface to inspect it directly. The warning sign: your test breaks when you refactor, but behavior hasn't changed. If you rename an internal function and tests fail, those tests were testing implementation, not behavior.

See [tests.md](references/tests.md) for examples and [mocking.md](references/mocking.md) for mocking guidelines.

## Never

- **Never mock what you control.** Only mock at system boundaries: external APIs, third-party services, time, randomness. Your own classes, internal collaborators, and the database are not mocking targets — test them for real.
- **Never stub DB reads/writes.** Use a real test database. Stubbing hides real behavior and tests something you own.
- **Never assert on call counts or call order** unless specifically testing protocol compliance or performance. These break on internal refactors without behavior changing.
- **Never test private methods or internal state.** Test through the public interface only. If an internal needs its own test, it belongs on a different object.
- **Never write implementation before a failing test.** No red = no confidence the test would have caught anything.
- **Never batch multiple behaviors into one red step.** One behavior per cycle — batching collapses the discipline.

## Anti-Pattern: Horizontal Slices

**DO NOT write all tests first, then all implementation.** This is "horizontal slicing" - treating RED as "write all tests" and GREEN as "write all code."

This produces **crap tests**:

- Tests written in bulk test _imagined_ behavior, not _actual_ behavior
- You end up testing the _shape_ of things (data structures, function signatures) rather than user-facing behavior
- Tests become insensitive to real changes - they pass when behavior breaks, fail when behavior is fine
- You outrun your headlights, committing to test structure before understanding the implementation

**Correct approach**: Vertical slices via tracer bullets. One test → one implementation → repeat. Each test responds to what you learned from the previous cycle. Because you just wrote the code, you know exactly what behavior matters and how to verify it.

```
WRONG (horizontal):
  RED:   test1, test2, test3, test4, test5
  GREEN: impl1, impl2, impl3, impl4, impl5

RIGHT (vertical):
  RED→GREEN: test1→impl1
  RED→GREEN: test2→impl2
  RED→GREEN: test3→impl3
  ...
```

## Workflow

### 1. Planning

Before writing any code:

- [ ] Confirm with user what interface changes are needed
- [ ] Confirm with user which behaviors to test (prioritize)
- [ ] Identify opportunities for [deep modules](references/deep-modules.md) (small interface, deep implementation)
- [ ] List the behaviors to test (not implementation steps)
- [ ] Get user approval on the plan

**MANDATORY when designing new interfaces**: Load [interface-design.md](references/interface-design.md) before finalizing the interface plan.

Ask: "What should the public interface look like? Which behaviors are most important to test?"

**You can't test everything.** Confirm with the user exactly which behaviors matter most. Focus testing effort on critical paths and complex logic, not every possible edge case.

### 2. Tracer Bullet

**MANDATORY when the path touches external services, APIs, or system boundaries**: Load [mocking.md](references/mocking.md) before writing test setup.

Write ONE test that confirms ONE thing about the system:

```
RED:   Write test for first behavior → test fails
GREEN: Write minimal code to pass → test passes
```

This is your tracer bullet - proves the path works end-to-end.

### 3. Incremental Loop

For each remaining behavior:

```
RED:   Write next test → fails
GREEN: Minimal code to pass → passes
```

Rules:

- One test at a time
- Only enough code to pass current test
- Don't anticipate future tests
- Keep tests focused on observable behavior

### 4. Refactor

After all tests pass, look for [refactor candidates](references/refactoring.md):

- [ ] Deepen modules (move complexity behind simple interfaces)
- [ ] Consider what new code reveals about existing code
- [ ] Run tests after each refactor step

**Never refactor while RED.** Get to GREEN first.

## Checklist Per Cycle

**MANDATORY when unsure whether a test is well-formed**: Load [tests.md](references/tests.md) for good/bad examples.

```
[ ] Test describes behavior, not implementation
[ ] Test uses public interface only
[ ] Test would survive internal refactor
[ ] Code is minimal for this test
[ ] No speculative features added
```

Do NOT load reference files unless a MANDATORY trigger above applies.
