#!/usr/bin/env bash
# SessionStart hook: surface a reminder if a recent handoff exists in the project.
#
# Output is read by the harness as a system reminder. Stays silent when:
#  - .claude/handoffs/ does not exist
#  - no .md files modified in the last 7 days
#
# Pairs with the session-handoff skill — the model can invoke /session-handoff
# to resume from the surfaced handoff.

set -e

HANDOFF_DIR=".claude/handoffs"
[ -d "$HANDOFF_DIR" ] || exit 0

# Most recent .md handoff modified within the last 7 days.
RECENT=$(find "$HANDOFF_DIR" -maxdepth 1 -name "*.md" -mtime -7 -type f 2>/dev/null \
  | sort -r \
  | head -1)

if [ -n "$RECENT" ]; then
  echo "session-handoff: Recent handoff exists at $RECENT (within last 7 days). On the first turn, surface it and ask whether to resume — unless the first message already answers that (e.g. 'resume'/'continue' -> resume directly; an explicit 'start fresh' -> skip). The 'don't judge from the prompt alone' guard is against inferring a decline from an unrelated-looking prompt, not against honoring an explicit instruction."
fi

exit 0
