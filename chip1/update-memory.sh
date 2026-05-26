#!/usr/bin/env bash
# update-memory.sh — Write-time intelligence for the project memory journal.
#
# Reads JSON from stdin, applies CRUD to MEMORY.md (table format).
# Usage:
#   echo '{"action":"add","title":"...","context":"...","pattern":"..."}' \
#     | bash update-memory.sh [--push]
#
# --push : commit and push changes to the shared agent-knowledge repo.
#
# Input JSON fields:
#   action      - "add" | "update" | "delete" | "list"
#   title       - Entry title (unique identifier)
#   context     - Why this decision was made
#   pattern     - The actionable convention/rule
#   supersedes  - Title to mark as superseded (optional)
#   author      - Who made the change (optional, for audit trail)
#   wikiFiles   - Array of wiki file names (optional)
#   sourceFiles - Array of source file paths (optional)
#   relatedDocs - Array of doc file paths (optional)
#
# Requires: python3

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MEMORY_FILE="$SCRIPT_DIR/MEMORY.md"
MEMORY_LIB="$SCRIPT_DIR/memory_lib.py"

# ── Read stdin ─────────────────────────────────────────────────────────────

INPUT=$(cat) || { echo "ERROR: no input" >&2; exit 1; }

# ── Parse action / title / author (one Python call, no jq) ─────────────────

# Use \x1f (unit separator) as delimiter — safe for arbitrary text.
IFS=$'\x1f' read -r ACTION TITLE AUTHOR < <(
  echo "$INPUT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(d.get('action',''), d.get('title',''), d.get('author',''), sep='\x1f')
"
)

[ -n "$ACTION" ] || { echo "ERROR: action is required (add|update|delete|list)" >&2; exit 1; }

# ── Check push flag ───────────────────────────────────────────────────────

PUSH=0
for arg in "$@"; do
  [ "$arg" = "--push" ] && PUSH=1
done

# ── CI guard ───────────────────────────────────────────────────────────────

if [ ! -f "$MEMORY_FILE" ]; then
  echo "SKIP: $MEMORY_FILE not found. Clone agent-knowledge repo first:"
  echo "  git clone git@github.com:shivanandasai-altir/agent-knowledge.git ~/agent-knowledge"
  exit 0
fi

# ── Run CRUD via Python library ────────────────────────────────────────────

echo "$INPUT" | python3 "$MEMORY_LIB"

# ── Rebuild Memory Index ───────────────────────────────────────────────────

"$SCRIPT_DIR/memory-search" --rebuild-index 2>/dev/null || true

# ── Push (optional) ───────────────────────────────────────────────────────

if [ "$PUSH" = "1" ] && [ "$ACTION" != "list" ]; then
  cd "$SCRIPT_DIR/.."
  git add chip1/MEMORY.md 2>/dev/null || true

  if git diff --cached --quiet 2>/dev/null; then
    exit 0  # nothing to commit
  fi

  author_msg=""
  [ -n "$AUTHOR" ] && author_msg=" (by $AUTHOR)"
  git commit -m "chip1: $ACTION $TITLE$author_msg" 2>/dev/null || true

  if git push 2>/dev/null; then
    echo "  (pushed to agent-knowledge)"
  else
    echo "  (push skipped — no remote configured or offline)"
  fi
fi
