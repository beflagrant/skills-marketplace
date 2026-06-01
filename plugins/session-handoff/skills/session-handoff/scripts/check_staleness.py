#!/usr/bin/env python3
"""
Check staleness of a handoff document compared to current project state.

Analyzes:
- Time since handoff was created
- Git commits since handoff
- Files that changed since handoff
- Branch divergence
- Modified files status

Usage:
    python check_staleness.py <handoff-file>
    python check_staleness.py .claude/handoffs/2024-01-15-143022-auth.md
"""

from __future__ import annotations

import sys

if sys.version_info < (3, 9):
    sys.exit(
        f"requires Python 3.9+ (running {sys.version_info.major}.{sys.version_info.minor})"
    )

import argparse
import re
from datetime import datetime
from pathlib import Path

from _common import (
    TEXT_IO_KWARGS,
    infer_project_root,
    log_cmd_failure,
    run_cmd,
)


def parse_handoff_metadata(filepath: str) -> dict:
    """Extract metadata from a handoff file."""
    content = Path(filepath).read_text(**TEXT_IO_KWARGS)
    metadata = {
        "created": None,
        "branch": None,
        "project_path": None,
        "modified_files": [],
    }

    # Parse Created timestamp
    match = re.search(r'Created:\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})', content)
    if match:
        try:
            metadata["created"] = datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S")
        except ValueError:
            pass

    # Parse Branch
    match = re.search(r'Branch:\s*(\S+)', content)
    if match:
        branch = match.group(1)
        if branch and not branch.startswith('['):
            metadata["branch"] = branch

    # Parse Project path
    match = re.search(r'Project:\s*(.+?)(?:\n|$)', content)
    if match:
        metadata["project_path"] = match.group(1).strip()

    # Parse modified files from table
    table_matches = re.findall(r'\|\s*([a-zA-Z0-9_\-./]+\.[a-zA-Z]+)\s*\|', content)
    for f in table_matches:
        if '/' in f and not f.startswith('['):
            metadata["modified_files"].append(f)

    return metadata


def get_commits_since(timestamp: datetime, project_path: str) -> list[str]:
    """Get list of commits since a given timestamp."""
    if not timestamp:
        return []

    iso_time = timestamp.strftime("%Y-%m-%dT%H:%M:%S")
    cmd = ["git", "log", f"--since={iso_time}", "--oneline", "--no-decorate"]
    rc, output, stderr = run_cmd(cmd, cwd=project_path)

    if rc != 0:
        log_cmd_failure(cmd, stderr)
        return []

    return output.split("\n") if output else []


def get_current_branch(project_path: str) -> str | None:
    """Get current git branch. Returns None on detached HEAD or failure."""
    cmd = ["git", "branch", "--show-current"]
    rc, branch, stderr = run_cmd(cmd, cwd=project_path)
    if rc != 0:
        log_cmd_failure(cmd, stderr)
        return None
    return branch or None


def get_changed_files_since(timestamp: datetime, project_path: str) -> list[str]:
    """Get files changed in commits since timestamp.

    Uses `git log --name-only` since `git diff` has no `--since` flag.
    """
    if not timestamp:
        return []

    iso_time = timestamp.strftime("%Y-%m-%dT%H:%M:%S")
    cmd = ["git", "log", f"--since={iso_time}", "--name-only", "--pretty=format:"]
    rc, output, stderr = run_cmd(cmd, cwd=project_path)

    if rc != 0:
        log_cmd_failure(cmd, stderr)
        return []

    files = [f.strip() for f in output.split("\n") if f.strip()]
    return sorted(set(files))


def check_files_exist(files: list[str], project_path: str) -> tuple[list[str], list[str]]:
    """Check which files from handoff still exist."""
    existing = []
    missing = []

    for f in files:
        full_path = Path(project_path) / f
        if full_path.exists():
            existing.append(f)
        else:
            missing.append(f)

    return existing, missing


# Staleness thresholds — bumped to module level so tuning happens in one place.
# Each tuple is (threshold, points_added, optional issue-message format).
AGE_THRESHOLDS_DAYS = (
    (30, 3, "Handoff is {n} days old"),
    (7, 2, "Handoff is {n} days old"),
    (1, 1, None),  # Minor staleness — not worth surfacing as an issue.
)
COMMIT_THRESHOLDS = (
    (50, 3, "{n} commits since handoff - significant changes"),
    (20, 2, "{n} commits since handoff"),
    (5, 1, None),
)
FILES_CHANGED_THRESHOLDS = (
    (20, 2, "{n} files changed since handoff"),
    (5, 1, None),
)
FILES_MISSING_THRESHOLDS = (
    (5, 2, "{n} referenced files no longer exist"),
    (0, 1, "{n} referenced file(s) missing"),
)
BRANCH_MISMATCH_POINTS = 2

# Score to level mapping. Higher score = more stale.
LEVEL_FRESH_MAX = 0
LEVEL_SLIGHT_MAX = 2
LEVEL_STALE_MAX = 4


def _bucket_score(value: float, thresholds, issues: list) -> int:
    """Walk a threshold table (high-to-low) and return the score for `value`.

    Appends a formatted issue message when the matched threshold defines one.
    """
    for threshold, points, message in thresholds:
        if value > threshold:
            if message is not None:
                issues.append(message.format(n=int(value)))
            return points
    return 0


def calculate_staleness_level(
    days_old: float,
    commits_since: int,
    files_changed: int,
    branch_matches: bool,
    files_missing: int,
) -> tuple[str, str, list[str]]:
    """Calculate staleness level and provide recommendations.

    Each factor adds 1-3 points based on severity, summed into a final
    score that maps to FRESH/SLIGHTLY_STALE/STALE/VERY_STALE per the
    LEVEL_*_MAX constants above.
    """
    issues: list[str] = []
    score = 0
    score += _bucket_score(days_old, AGE_THRESHOLDS_DAYS, issues)
    score += _bucket_score(commits_since, COMMIT_THRESHOLDS, issues)
    score += _bucket_score(files_changed, FILES_CHANGED_THRESHOLDS, issues)
    score += _bucket_score(files_missing, FILES_MISSING_THRESHOLDS, issues)
    if not branch_matches:
        score += BRANCH_MISMATCH_POINTS
        issues.append("Current branch differs from handoff branch")

    if score <= LEVEL_FRESH_MAX:
        return (
            "FRESH",
            "Safe to resume - minimal changes since handoff",
            issues,
        )
    if score <= LEVEL_SLIGHT_MAX:
        return (
            "SLIGHTLY_STALE",
            "Generally safe to resume - review changes before continuing",
            issues,
        )
    if score <= LEVEL_STALE_MAX:
        return (
            "STALE",
            "Proceed with caution - significant changes may affect context",
            issues,
        )
    return (
        "VERY_STALE",
        "Consider creating new handoff - too many changes since original",
        issues,
    )


def check_staleness(handoff_path: str) -> dict:
    """Run staleness check on a handoff file."""
    path = Path(handoff_path)

    if not path.exists():
        return {"error": f"Handoff file not found: {handoff_path}"}

    # Parse handoff
    metadata = parse_handoff_metadata(handoff_path)

    # Determine project path
    project_path = metadata.get("project_path")
    if not project_path or not Path(project_path).exists():
        original = project_path
        project_path = str(infer_project_root(path))
        if original:
            print(
                f"warning: handoff Project path '{original}' does not exist; "
                f"falling back to {project_path}",
                file=sys.stderr,
            )
        else:
            print(
                f"warning: handoff has no Project metadata; "
                f"assuming project root at {project_path}",
                file=sys.stderr,
            )

    # Check if git repo
    rc, _, _ = run_cmd(["git", "rev-parse", "--git-dir"], cwd=project_path)
    is_git_repo = rc == 0

    result = {
        "handoff_file": str(path),
        "project_path": project_path,
        "is_git_repo": is_git_repo,
        "created": metadata["created"],
        "handoff_branch": metadata["branch"],
    }

    # Calculate age
    if metadata["created"]:
        age = datetime.now() - metadata["created"]
        result["days_old"] = age.total_seconds() / 86400
        result["hours_old"] = age.total_seconds() / 3600
    else:
        result["days_old"] = None
        result["hours_old"] = None

    if is_git_repo:
        # Git-based checks
        result["current_branch"] = get_current_branch(project_path)
        result["branch_matches"] = (
            result["current_branch"] == metadata["branch"]
            if metadata["branch"] else True
        )

        commits = get_commits_since(metadata["created"], project_path)
        result["commits_since"] = len(commits)
        result["recent_commits"] = commits[:5]  # Show first 5

        changed_files = get_changed_files_since(metadata["created"], project_path)
        result["files_changed_count"] = len(changed_files)
        result["files_changed"] = changed_files[:10]  # Show first 10

        # Check if handoff's modified files still exist
        existing, missing = check_files_exist(metadata["modified_files"], project_path)
        result["referenced_files_exist"] = len(existing)
        result["referenced_files_missing"] = missing

        # Calculate staleness
        level, recommendation, issues = calculate_staleness_level(
            result.get("days_old", 0) or 0,
            result["commits_since"],
            result["files_changed_count"],
            result["branch_matches"],
            len(missing)
        )
        result["staleness_level"] = level
        result["recommendation"] = recommendation
        result["issues"] = issues
    else:
        # Non-git checks (limited)
        result["staleness_level"] = "UNKNOWN"
        result["recommendation"] = "Not a git repo - unable to detect changes"
        result["issues"] = ["Project is not a git repository"]

    return result


def print_report(result: dict):
    """Print staleness report."""
    if "error" in result:
        print(f"Error: {result['error']}")
        return

    print(f"\n{'='*60}")
    print(f"Handoff Staleness Report")
    print(f"{'='*60}")
    print(f"File: {result['handoff_file']}")
    print(f"Project: {result['project_path']}")

    if result["created"]:
        print(f"Created: {result['created'].strftime('%Y-%m-%d %H:%M:%S')}")
        if result["days_old"] is not None:
            if result["days_old"] < 1:
                print(f"Age: {result['hours_old']:.1f} hours")
            else:
                print(f"Age: {result['days_old']:.1f} days")

    print(f"\n{'='*60}")
    print(f"Staleness Level: {result['staleness_level']}")
    print(f"{'='*60}")
    print(f"\nRecommendation: {result['recommendation']}")

    if result.get("issues"):
        print(f"\nIssues detected:")
        for issue in result["issues"]:
            print(f"  - {issue}")

    if result.get("is_git_repo"):
        print(f"\n--- Git Status ---")
        print(f"Handoff branch: {result.get('handoff_branch', 'Unknown')}")
        print(f"Current branch: {result.get('current_branch', 'Unknown')}")
        print(f"Branch matches: {'Yes' if result.get('branch_matches') else 'No'}")
        print(f"Commits since handoff: {result.get('commits_since', 0)}")
        print(f"Files changed: {result.get('files_changed_count', 0)}")

        if result.get("recent_commits"):
            print(f"\nRecent commits:")
            for commit in result["recent_commits"][:5]:
                print(f"  {commit}")

        if result.get("referenced_files_missing"):
            print(f"\nMissing referenced files:")
            for f in result["referenced_files_missing"][:5]:
                print(f"  - {f}")

    print(f"\n{'='*60}")

    # Color-coded verdict (using text indicators)
    level = result.get("staleness_level", "UNKNOWN")
    if level == "FRESH":
        print("Verdict: [OK] Safe to resume")
    elif level == "SLIGHTLY_STALE":
        print("Verdict: [OK] Review changes, then resume")
    elif level == "STALE":
        print("Verdict: [CAUTION] Verify context before resuming")
    elif level == "VERY_STALE":
        print("Verdict: [WARNING] Consider creating fresh handoff")
    else:
        print("Verdict: [UNKNOWN] Manual verification needed")


def main():
    parser = argparse.ArgumentParser(
        description="Check whether a handoff document is still current.",
    )
    parser.add_argument(
        "handoff_file",
        help="Path to the handoff markdown file to check.",
    )
    args = parser.parse_args()

    result = check_staleness(args.handoff_file)
    print_report(result)

    # Exit code reflects the staleness gradient and separates the
    # "tooling couldn't inspect" case from "context is genuinely stale":
    #   0 = FRESH / SLIGHTLY_STALE        safe to resume
    #   1 = STALE                         user should review before resuming
    #   2 = VERY_STALE                    handoff likely needs to be redone
    #   3 = UNKNOWN                       inspection failed (e.g. not a git repo)
    level = result.get("staleness_level", "UNKNOWN")
    sys.exit(
        {"FRESH": 0, "SLIGHTLY_STALE": 0, "STALE": 1, "VERY_STALE": 2}.get(level, 3)
    )


if __name__ == "__main__":
    main()
