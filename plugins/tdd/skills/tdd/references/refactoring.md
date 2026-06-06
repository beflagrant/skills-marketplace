# Refactor Candidates

After all tests pass, check for:

- **Shallow modules** — deepen by moving complexity behind a simpler interface (see [deep-modules.md](deep-modules.md))
- **What the new code reveals** — implementing a slice often exposes problems in adjacent existing code that weren't visible before; those may justify their own slice
- **Tests still on the public interface** — if a refactor broke a test without changing behavior, the test was testing implementation, not behavior
