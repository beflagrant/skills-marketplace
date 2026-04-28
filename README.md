> **Do not edit this repo directly.** It is auto-published from [beflagrant/skills](https://github.com/beflagrant/skills). Manual edits will be overwritten on the next publish run.

# Flagrant skills marketplace

A private [Claude Code](https://claude.com/product/claude-code) plugin marketplace maintained by [Flagrant](https://beflagrant.com). This repo distributes the skills we use internally to teams and clients we collaborate with.

If you have read access to this repo, you can install these skills into your own Claude Code setup.

## What this is

**Claude Code** is Anthropic's command-line tool for working with Claude on real codebases. It runs in your terminal, reads and edits files, runs commands, and responds to the context of whatever project you're in.

**Skills** are Markdown files that teach Claude when and how to do something — for example, "how Flagrant writes Architecture Decision Records" or "how we decide which RSpec tests to run after a change." A skill is just a directory with a `SKILL.md` file. Claude loads a skill automatically when your request matches its description.

**A plugin marketplace** is a git repository that packages skills (and other Claude Code extensions) so they can be installed with a single command. Marketplaces can be public or private. This one is private — access is controlled by who we've granted read permission on GitHub.

In short: this repo is a catalog of small, opinionated behaviors you can hand to Claude Code, installable in about thirty seconds.

## Prerequisites

1. **Claude Code installed.** See [claude.com/product/claude-code](https://claude.com/product/claude-code) for installation instructions.
2. **Read access to this repo.** If you're reading this, you probably already have it. If not, ask your Flagrant contact.
3. **A working git credential** that can clone from `github.com:beflagrant/skills-marketplace.git`. An SSH key added to your GitHub account is the simplest path. Test it with `git ls-remote git@github.com:beflagrant/skills-marketplace.git`.

## Installing

Inside a Claude Code session, run:

```text
/plugin marketplace add git@github.com:beflagrant/skills-marketplace.git
```

Claude Code clones the repo into its local cache and reads the catalog.

Then install any plugin from the catalog:

```text
/plugin install adr@flagrant
```

The `@flagrant` suffix is the marketplace name (set in `.claude-plugin/marketplace.json`), not a username.

List what's installed:

```text
/plugin list
```

Uninstall:

```text
/plugin uninstall adr@flagrant
```

Update to the latest version published:

```text
/plugin update adr@flagrant
```

## What's in the catalog

Each subdirectory of `plugins/` is one installable plugin. The authoritative list is in [.claude-plugin/marketplace.json](.claude-plugin/marketplace.json).

## How skills get invoked

Once installed, a skill loads automatically when your prompt matches its description. You don't call it explicitly. For example, after installing the `adr` plugin, asking Claude "should we write an ADR for swapping our background job library?" will load the skill and follow its instructions.

Skills are namespaced by the plugin that ships them, so the `adr` skill inside the `adr` plugin is fully qualified as `adr:adr`. This matters mainly if you have two plugins that both define a skill with the same name.

## Contributing or updating a skill

Skills are **authored** in a separate private repo, not here. This repo is the distribution channel — think of it like a build artifact. Edits made directly to files in this repo will be overwritten the next time a skill is published from source.

Flagrant team members: see the `skills` repo README for how to add or update a skill and run the publish tooling.

Clients: if you have feedback on a skill, or want to suggest a new one, get in touch with your Flagrant contact.

## Repo layout

```text
skills-marketplace/
├── .claude-plugin/
│   └── marketplace.json      # catalog of plugins
├── plugins/
│   └── <plugin-name>/
│       ├── .claude-plugin/
│       │   └── plugin.json   # plugin manifest (name, description, version)
│       └── skills/
│           └── <skill-name>/
│               └── SKILL.md  # the skill itself
└── .github/
    └── workflows/            # CI validates marketplace structure on every push
```

## Troubleshooting

**`/plugin marketplace add` fails with a permission error.** Your git credential can't read the repo. Confirm with `git ls-remote git@github.com:beflagrant/skills-marketplace.git`. If that fails, fix your SSH key or GitHub access.

**`/plugin install` reports the plugin doesn't exist.** Double-check the name against [marketplace.json](.claude-plugin/marketplace.json), and make sure you included the `@flagrant` suffix.

**A skill you expect to load isn't loading.** Skills are loaded based on how well your prompt matches the skill's description. Try phrasing the request using the vocabulary in the skill's `SKILL.md` description. You can also ask Claude directly, e.g. "do you have the adr skill loaded?"

**An update didn't take effect.** Run `/plugin update <name>@flagrant`. Claude Code caches installed plugins; updates are not automatic.
