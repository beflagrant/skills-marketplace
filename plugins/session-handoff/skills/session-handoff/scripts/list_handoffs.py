#!/usr/bin/env python3
"""
List available handoff documents in the current project.

Searches for handoff documents in .claude/handoffs/ and displays:
- Filename with date
- Title extracted from document
- Status (if marked complete)

Usage:
    python list_handoffs.py           # List handoffs in current project
    python list_handoffs.py /path     # List handoffs in specified path
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

from _common import TEXT_IO_KWARGS


def extract_title(content: str) -> str:
    """Extract the title from handoff content."""
    match = re.search(r'^#\s+(?:Handoff:\s*)?(.+)$', content, re.MULTILINE)
    if not match:
        return "[Unable to read title]"
    title = match.group(1).strip()
    if title.startswith("[") and title.endswith("]"):
        return "[Untitled - needs completion]"
    return title[:50] + "..." if len(title) > 50 else title


def check_completion_status(content: str) -> str:
    """Classify a handoff by remaining TODO count."""
    todo_count = content.count("[TODO:")
    if todo_count == 0:
        return "Complete"
    if todo_count <= 3:
        return f"In Progress ({todo_count} TODOs)"
    return f"Needs Work ({todo_count} TODOs)"


def parse_date_from_filename(filename: str) -> datetime | None:
    """Extract date from filename like 2024-01-15-143022-slug.md"""
    match = re.match(r'(\d{4}-\d{2}-\d{2})-(\d{6})', filename)
    if match:
        try:
            date_str = match.group(1)
            time_str = match.group(2)
            return datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H%M%S")
        except ValueError:
            pass
    return None


def list_handoffs(project_path: str) -> list[dict]:
    """List all handoff documents in a project."""
    handoffs_dir = Path(project_path) / ".claude" / "handoffs"

    if not handoffs_dir.exists():
        return []

    handoffs = []
    for filepath in handoffs_dir.glob("*.md"):
        try:
            content = filepath.read_text(**TEXT_IO_KWARGS)
        except (OSError, UnicodeDecodeError) as e:
            print(
                f"warning: could not read {filepath.name}: {e}",
                file=sys.stderr,
            )
            title = "[Unable to read]"
            status = "Unknown"
        else:
            title = extract_title(content)
            status = check_completion_status(content)
        handoffs.append({
            "path": str(filepath),
            "filename": filepath.name,
            "title": title,
            "status": status,
            "date": parse_date_from_filename(filepath.name),
            "size": filepath.stat().st_size,
        })

    # Sort by date, most recent first
    handoffs.sort(key=lambda x: x["date"] or datetime.min, reverse=True)

    return handoffs


def format_date(dt: datetime | None) -> str:
    """Format datetime for display."""
    if dt is None:
        return "Unknown date"
    return dt.strftime("%Y-%m-%d %H:%M")


def main():
    parser = argparse.ArgumentParser(
        description="List handoff documents in a project's .claude/handoffs/."
    )
    parser.add_argument(
        "project_path",
        nargs="?",
        default=None,
        help="Project root to scan (defaults to current working directory)",
    )
    args = parser.parse_args()

    project_path = args.project_path or os.getcwd()
    handoffs = list_handoffs(project_path)

    if not handoffs:
        print(f"No handoffs found in {project_path}/.claude/handoffs/")
        print("\nTo create a handoff, run: python create_handoff.py [task-slug]")
        sys.exit(1)

    print(f"Found {len(handoffs)} handoff(s) in {project_path}/.claude/handoffs/\n")
    print("-" * 80)

    for h in handoffs:
        print(f"  Date: {format_date(h['date'])}")
        print(f"  Title: {h['title']}")
        print(f"  Status: {h['status']}")
        print(f"  File: {h['filename']}")
        print("-" * 80)

    print(f"\nTo resume from a handoff, read the document and follow the resume checklist.")
    print(f"Most recent: {handoffs[0]['path']}")


if __name__ == "__main__":
    main()
