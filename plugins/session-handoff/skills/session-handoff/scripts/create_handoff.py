#!/usr/bin/env python3
"""
Smart scaffold generator for handoff documents.

Creates a new handoff document with auto-detected metadata:
- Current timestamp
- Project path
- Git branch (if available)
- Recent git log
- Modified/staged files
- Handoff chain linking

Usage:
    python create_handoff.py [task-slug] [--continues-from <previous-handoff>]
    python create_handoff.py "implementing-auth"
    python create_handoff.py "auth-part-2" --continues-from 2024-01-15-auth.md
    python create_handoff.py  # auto-generates slug from timestamp
"""

from __future__ import annotations

import sys

if sys.version_info < (3, 9):
    sys.exit(
        f"requires Python 3.9+ (running {sys.version_info.major}.{sys.version_info.minor})"
    )

import argparse
import os
import re
from datetime import datetime
from pathlib import Path

from _common import TEXT_IO_KWARGS, run_cmd


TEMPLATE_PATH = Path(__file__).parent.parent / "references" / "handoff-template.md"


def _load_template() -> str:
    """Read the canonical handoff template from references/."""
    if not TEMPLATE_PATH.exists():
        sys.exit(
            f"error: handoff template not found at {TEMPLATE_PATH}. "
            f"Is the session-handoff skill installed correctly?"
        )
    full = TEMPLATE_PATH.read_text(**TEXT_IO_KWARGS)
    # The file has a human-readable header explaining the placeholder
    # conventions. Strip everything before the first `---` separator so
    # the rendered handoff starts at "# Handoff: ..." directly.
    parts = full.split("\n---\n", 1)
    return parts[1].lstrip() if len(parts) == 2 else full


def get_git_info(project_path: str) -> dict:
    """Gather git information from the project."""
    info = {
        "is_git_repo": False,
        "branch": None,
        "recent_commits": [],
        "modified_files": [],
        "staged_files": [],
    }

    # Check if git repo
    rc, _, _ = run_cmd(["git", "rev-parse", "--git-dir"], cwd=project_path)
    if rc != 0:
        return info

    info["is_git_repo"] = True

    # Get current branch
    rc, branch, _ = run_cmd(["git", "branch", "--show-current"], cwd=project_path)
    if rc == 0 and branch:
        info["branch"] = branch

    # Get recent commits (last 5)
    rc, log, _ = run_cmd(
        ["git", "log", "--oneline", "-5", "--no-decorate"],
        cwd=project_path
    )
    if rc == 0 and log:
        info["recent_commits"] = log.split("\n")

    # Get modified files (unstaged)
    rc, modified, _ = run_cmd(
        ["git", "diff", "--name-only"],
        cwd=project_path
    )
    if rc == 0 and modified:
        info["modified_files"] = modified.split("\n")

    # Get staged files
    rc, staged, _ = run_cmd(
        ["git", "diff", "--name-only", "--cached"],
        cwd=project_path
    )
    if rc == 0 and staged:
        info["staged_files"] = staged.split("\n")

    return info


def find_previous_handoffs(project_path: str) -> list[dict]:
    """Find existing handoffs in the project."""
    handoffs_dir = Path(project_path) / ".claude" / "handoffs"
    if not handoffs_dir.exists():
        return []

    handoffs = []
    for filepath in handoffs_dir.glob("*.md"):
        # Extract title from file
        try:
            content = filepath.read_text(**TEXT_IO_KWARGS)
            match = re.search(r'^#\s+(?:Handoff:\s*)?(.+)$', content, re.MULTILINE)
            title = match.group(1).strip() if match else filepath.stem
        except (OSError, UnicodeDecodeError) as e:
            print(f"warning: could not read title from {filepath.name}: {e}", file=sys.stderr)
            title = filepath.stem

        # Parse date from filename
        date_match = re.match(r'(\d{4}-\d{2}-\d{2})-(\d{6})', filepath.name)
        if date_match:
            try:
                date = datetime.strptime(
                    f"{date_match.group(1)} {date_match.group(2)}",
                    "%Y-%m-%d %H%M%S"
                )
            except ValueError:
                date = None
        else:
            date = None

        handoffs.append({
            "filename": filepath.name,
            "path": str(filepath),
            "title": title,
            "date": date,
        })

    # Sort by date, most recent first
    handoffs.sort(key=lambda x: x["date"] or datetime.min, reverse=True)
    return handoffs


def get_previous_handoff_info(
    handoffs: list[dict],
    continues_from: str | None = None,
    branches_from: str | None = None,
) -> dict:
    """Get information about the previous handoff for chaining.

    Takes the already-scanned handoffs list so the caller can reuse it
    rather than re-scanning the directory.

    `relationship` is "continues" or "branches" when an explicit target was
    given, or None when the result is an auto-suggestion of the most recent
    handoff (caller decides how to render that case).
    """
    target = continues_from or branches_from
    relationship = "continues" if continues_from else ("branches" if branches_from else None)

    if target:
        for h in handoffs:
            if target in h["filename"]:
                return {
                    "exists": True,
                    "relationship": relationship,
                    "filename": h["filename"],
                    "title": h["title"],
                }
        return {
            "exists": False,
            "relationship": relationship,
            "filename": target,
            "title": "Not found",
        }

    if handoffs:
        most_recent = handoffs[0]
        return {
            "exists": True,
            "relationship": None,
            "filename": most_recent["filename"],
            "title": most_recent["title"],
            "suggested": True,
        }

    return {"exists": False, "relationship": None}


def render_chain_section(prev_handoff: dict, no_chain: bool = False) -> str:
    """Render the Handoff Chain section based on the relationship to a prior handoff.

    Three explicit relationships are supported:
    - "continues": linear continuation of the prior thread
    - "branches": diverged from a prior handoff (both threads remain valid)
    - supersedes: handled as a separate list field, populated by the human/agent

    When `no_chain` is True, render an "independent work" section. When the
    relationship is None but a prior handoff was found, render an auto-suggested
    continuation with a note pointing at the override flags.
    """
    if no_chain:
        return (
            "## Handoff Chain\n\n"
            "- **Continues from**: None (independent work)\n"
            "- **Supersedes**: None"
        )

    if not prev_handoff.get("exists"):
        return (
            "## Handoff Chain\n\n"
            "- **Continues from**: None (fresh start)\n"
            "- **Supersedes**: None\n\n"
            "> This is the first handoff for this task."
        )

    filename = prev_handoff["filename"]
    title = prev_handoff.get("title", "Unknown")
    relationship = prev_handoff.get("relationship")

    if relationship == "branches":
        label = "Branches from"
        note = (
            "> The prior handoff was not resumed this session. This handoff "
            "captures a divergent thread; the prior one remains valid."
        )
    else:
        label = "Continues from"
        note = "> Review the previous handoff for full context before filling this one."

    lines = [
        "## Handoff Chain",
        "",
        f"- **{label}**: [{filename}](./{filename})",
        f"  - Previous title: {title}",
        '- **Supersedes**: [list any older handoffs this replaces, or "None"]',
        "",
        note,
    ]

    if prev_handoff.get("suggested"):
        lines.append("")
        lines.append(
            "> *Auto-suggested most-recent handoff as continuation. If this work "
            "diverged from a declined handoff use `--branches-from`; if it's "
            "unrelated use `--no-chain`.*"
        )

    return "\n".join(lines)


def generate_handoff(
    project_path: str,
    slug: str | None = None,
    continues_from: str | None = None,
    branches_from: str | None = None,
    no_chain: bool = False,
    prev_handoffs: list[dict] | None = None,
) -> str:
    """Generate a handoff document with pre-filled metadata.

    If `prev_handoffs` is provided (already scanned by the caller), it
    is used directly to avoid a second pass over the handoffs directory.

    `continues_from` and `branches_from` are mutually exclusive — when both
    are set, `continues_from` wins. `no_chain` forces an "independent work"
    chain section regardless of any prior handoffs.
    """

    # Generate timestamp and filename
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    file_timestamp = now.strftime("%Y-%m-%d-%H%M%S")

    if not slug:
        slug = "handoff"

    # Sanitize slug: lowercase, normalize separators, strip remaining specials.
    # Branch names like "feature/auth" must become "feature-auth", not "featureauth".
    slug = slug.lower()
    for ch in (" ", "_", "/", "\\"):
        slug = slug.replace(ch, "-")
    slug = "".join(c for c in slug if c.isalnum() or c == "-")

    filename = f"{file_timestamp}-{slug}.md"

    # Create handoffs directory
    handoffs_dir = Path(project_path) / ".claude" / "handoffs"
    handoffs_dir.mkdir(parents=True, exist_ok=True)

    filepath = handoffs_dir / filename

    # Refuse to clobber an existing handoff at the same timestamp+slug.
    # Two `create_handoff.py` calls in the same second with the same slug
    # would otherwise silently overwrite the first one.
    if filepath.exists():
        sys.exit(
            f"error: refusing to overwrite existing handoff at {filepath}. "
            f"Wait a second or pass a different slug."
        )

    # Gather git info
    git_info = get_git_info(project_path)

    # Get previous handoff info for chaining (scan only if caller didn't)
    if prev_handoffs is None:
        prev_handoffs = find_previous_handoffs(project_path)
    prev_handoff = get_previous_handoff_info(
        prev_handoffs, continues_from, branches_from
    )

    # Build pre-filled sections
    branch_line = git_info["branch"] if git_info["branch"] else "[not a git repo or detached HEAD]"

    # Recent commits section
    if git_info["recent_commits"]:
        commits_section = "\n".join(f"  - {c}" for c in git_info["recent_commits"])
    else:
        commits_section = "  - [no recent commits or not a git repo]"

    # Modified files section
    all_modified = list(set(git_info["modified_files"] + git_info["staged_files"]))
    if all_modified:
        modified_section = "\n".join(f"| {f} | [describe changes] | [why changed] |" for f in all_modified[:10])
        if len(all_modified) > 10:
            modified_section += f"\n| ... and {len(all_modified) - 10} more files | | |"
    else:
        modified_section = "| [no modified files detected] | | |"

    # Handoff chain section
    chain_section = render_chain_section(prev_handoff, no_chain=no_chain)

    # Render the document from the canonical references/ template.
    content = _load_template().format(
        timestamp=timestamp,
        project_path=project_path,
        branch_line=branch_line,
        commits_section=commits_section,
        chain_section=chain_section,
        modified_section=modified_section,
    )

    filepath.write_text(content, **TEXT_IO_KWARGS)

    return str(filepath)


def main():
    parser = argparse.ArgumentParser(
        description="Create a new handoff document with smart scaffolding"
    )
    parser.add_argument(
        "slug",
        nargs="?",
        default=None,
        help="Short identifier for the handoff (e.g., 'implementing-auth')"
    )
    chain_group = parser.add_mutually_exclusive_group()
    chain_group.add_argument(
        "--continues-from",
        dest="continues_from",
        help="Filename of previous handoff this continues from (same thread)"
    )
    chain_group.add_argument(
        "--branches-from",
        dest="branches_from",
        help="Filename of previous handoff this diverged from (different thread; "
             "use when the prior handoff was surfaced but not resumed this session)"
    )
    chain_group.add_argument(
        "--no-chain",
        dest="no_chain",
        action="store_true",
        help="Mark this handoff as unrelated to any prior handoff (independent work)"
    )

    args = parser.parse_args()

    # Get project path (current working directory)
    project_path = os.getcwd()

    # Single scan of the handoffs directory; reused by generate_handoff.
    prev_handoffs = find_previous_handoffs(project_path)

    no_explicit_chain = not (args.continues_from or args.branches_from or args.no_chain)
    if no_explicit_chain and prev_handoffs:
        print(f"Found {len(prev_handoffs)} existing handoff(s).")
        print(f"Most recent: {prev_handoffs[0]['filename']}")
        print(
            "No relationship specified — defaulting to a suggested continuation. "
            "Pass --continues-from / --branches-from / --no-chain to be explicit.\n"
        )

    # Generate handoff
    filepath = generate_handoff(
        project_path,
        args.slug,
        continues_from=args.continues_from,
        branches_from=args.branches_from,
        no_chain=args.no_chain,
        prev_handoffs=prev_handoffs,
    )

    print(f"Created handoff document: {filepath}")
    print(f"\nNext steps:")
    print(f"1. Open {filepath}")
    print(f"2. Replace [TODO: ...] placeholders with actual content")
    print(f"3. Focus especially on 'Important Context' and 'Immediate Next Steps'")
    print(f"4. Run: python scripts/validate_handoff.py {filepath}")
    print(f"   (Checks for completeness and accidental secrets)")

    return filepath


if __name__ == "__main__":
    main()
