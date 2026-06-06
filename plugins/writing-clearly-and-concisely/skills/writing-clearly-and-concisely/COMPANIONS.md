# Companion Infrastructure

What `writing-clearly-and-concisely` depends on beyond the skill directory itself. The skill is fully self-contained — Strunk's rules, the reference files under `elements-of-style/`, and the AI-writing-pattern list all ship in the package, and no host config is required for it to function. What this file covers is the *optional* overlay: user-specific or team-specific writing preferences that personalize the skill's output without forking it.

## Why this file exists

A skill packages as a self-contained directory and can be installed in many ways — a personal config repo, a plugin, a marketplace install. But anything that integrates with the host — rules loaded passively each session, `settings.json` hooks, permission allowlist entries — lives *outside* the skill directory and doesn't ship with the package. This file is the manual half: when you install `writing-clearly-and-concisely` into a new environment, this is what to consider setting up alongside it.

The skill has no host config — no scripts, no hooks, no permission allowlist. The companion is one optional rule.

## 1. Optional companion rule: personal or team writing preferences

The skill teaches what every writer should know — Strunk's elementary rules, AI-writing patterns to avoid, the bias toward active voice and concrete language. What it deliberately doesn't teach is **your voice**: the phrasings that mark prose as yours, the abbreviations you favor, the way you close a piece, the hedges you keep audible vs. throat-clearing you cut.

Those preferences live in a personal or team rule file (loaded passively each session, e.g. `~/.claude/rules/writing.md`) that *supplements* the skill rather than competing with it. Forking the skill to add personal preferences couples two different rates of change: Strunk doesn't update, but your voice and your team's house style do. A supplemental rule file decouples them — the skill stays current with the package, the overlay updates independently.

### What belongs in the overlay

A personal or team writing rule typically captures:

- **Voice register** — the level of formality, the words favored when choosing between near-synonyms, hedges that should stay audible vs. throat-clearing to cut.
- **Distinctive markers** — abbreviations (`&c.` vs `etc.`, `viz.`, `cf.`), idiom preferences (e.g. avoiding violent or military metaphors, avoiding borrowed corporate jargon), preferred labels (e.g. "phase" over "arc").
- **Structural conventions** — how to close a piece (valediction vs. recap-summary), when to use em-dashes vs. parentheses, capitalization of headings.
- **Voice-emulation scope** — when the rule applies (drafts under the user's byline, ghostwritten messages) and when it doesn't (external docs where the personal register would be imposed on readers who didn't ask for it).

### What does NOT belong

- **Anything Strunk already covers** — active voice, concision, concrete language. The skill carries these.
- **Anything in `signs-of-ai-writing.md`** — the AI-pattern list is already in the skill.
- **Project-specific terminology** — that belongs in the project's `CLAUDE.md`, not a personal rule.

### Sample structure

```markdown
# Writing

User-specific writing preferences that supplement the
`writing-clearly-and-concisely` skill.

## Register

[Describe the voice — precise / unhedged / archaic-leaning / etc. Lead with
the *why* behind the register so future readings can judge edge cases.]

## Avoid [category of phrases]

[Specific phrases or categories to avoid, with reasoning. E.g., "violent and
military metaphors" with examples and replacements; "borrowed corporate
jargon" with the plain equivalents.]

## Preferred forms

[Specific forms to use — favored abbreviations, structural conventions,
distinctive markers.]

## Voice-emulation scope

[When the rule applies (drafts under user byline, ghostwritten messages) vs.
when it doesn't (external docs, general audiences). Without this, the
personal register can leak into public docs where it reads as idiosyncratic.]
```

The shape is yours; what matters is that the rule *supplements* the skill rather than duplicating it.

## Adopting these in a new environment

Rough order:

1. The skill works standalone with no setup beyond installing it. If you have no personal or team writing preferences to capture, stop here.
2. If you want a personal voice overlay: draft a rule file (`~/.claude/rules/writing.md` or your equivalent) following the sample structure above. Add only what's specific to *you* or your team — defer everything Strunk covers to the skill.

The skill is the public-knowledge layer; the rule is the personal-knowledge layer. They compose naturally because they cover non-overlapping territory.
