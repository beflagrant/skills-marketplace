"""Shared helpers for the session-handoff scripts.

Keep this module deliberately small: only helpers that are genuinely used
by more than one script, with clear contracts. Anything script-specific
stays in the script that uses it.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


# File I/O conventions — pass these as **TEXT_IO_KWARGS to read_text/write_text.
# Without explicit utf-8, Python falls back to the platform default
# (cp1252 on Windows) which corrupts em-dashes, smart quotes, etc.
TEXT_IO_KWARGS = {"encoding": "utf-8"}


def run_cmd(
    cmd: list[str],
    cwd: str | Path | None = None,
    timeout: int = 10,
) -> tuple[int, str, str]:
    """Run a command and return (returncode, stdout, stderr).

    On exceptions (timeout, missing binary), returncode is -1 and stderr
    contains a description so callers can log a useful failure reason
    instead of collapsing every failure into a single bool.
    """
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(cwd) if cwd is not None else None,
            timeout=timeout,
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", f"timed out after {timeout}s: {' '.join(cmd)}"
    except FileNotFoundError as e:
        return -1, "", str(e)


def log_cmd_failure(cmd: list[str], stderr: str) -> None:
    """Log a failed subprocess invocation to stderr for user visibility."""
    if stderr:
        print(f"warning: `{' '.join(cmd)}` failed: {stderr}", file=sys.stderr)


def infer_project_root(handoff_path: Path) -> Path:
    """Infer the project root from a handoff file's location.

    Standard layout: <project>/.claude/handoffs/<file>.md, in which case
    climb three levels. For handoffs outside that layout (e.g. /tmp/foo.md),
    fall back to the file's parent so relative references resolve sensibly
    rather than against `/`.
    """
    parents = handoff_path.resolve().parents
    if (
        len(parents) >= 3
        and parents[0].name == "handoffs"
        and parents[1].name == ".claude"
    ):
        return parents[2]
    return handoff_path.parent
