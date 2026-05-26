#!/usr/bin/env bash
# update-memory.sh — Write-time intelligence for the project memory journal.
#
# Reads MEMORY.md, applies CRUD logic (add with supersede, update, delete, list),
# and writes back in table format (Active / Archived sections).
# Never appends blindly — checks duplicates, handles supersedes.
#
# Usage:
#   echo '{"action":"add","title":"...","context":"...","pattern":"..."}' \
#     | bash update-memory.sh
#   echo '{"action":"add","title":"...","context":"...","pattern":"..."}' \
#     | bash update-memory.sh --push
#
# --push : after writing, commit and push to the shared agent-knowledge repo.
#
# Input JSON fields:
#   action      - "add" | "update" | "delete" | "list"
#   title       - Entry title (unique identifier)
#   context     - Why this decision was made
#   pattern     - The actionable convention/rule
#   supersedes  - Title of entry this replaces (optional)
#   author      - Who made the change (optional, for audit trail)
#   wikiFiles   - Array of wiki file names (optional)
#   sourceFiles - Array of source file paths (optional)
#   relatedDocs - Array of doc file paths (optional)
#
# Requires: python3, jq

set -euo pipefail

PUSH="${PUSH:-0}"
for arg in "$@"; do
  [ "$arg" = "--push" ] && PUSH=1
done

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MEMORY_FILE="$SCRIPT_DIR/MEMORY.md"
MEMORY_LIB="$SCRIPT_DIR/memory_lib.py"

# CI guard — if MEMORY.md doesn't exist, skip silently
if [ ! -f "$MEMORY_FILE" ]; then
  echo "SKIP: $MEMORY_FILE not found. Clone agent-knowledge repo first:"
  echo "  git clone git@github.com:shivanandasai-altir/agent-knowledge.git ~/agent-knowledge"
  exit 0
fi

# ── Parse JSON input ──────────────────────────────────────────────────────

if ! INPUT=$(cat); then
  echo "ERROR: no input" >&2
  exit 1
fi

ACTION=$(echo "$INPUT" | jq -r '.action // ""')
TITLE=$(echo "$INPUT" | jq -r '.title // ""')
AUTHOR=$(echo "$INPUT" | jq -r '.author // ""')

if [ -z "$ACTION" ]; then
  echo "ERROR: action is required (add | update | delete | list)" >&2
  exit 1
fi

# ── Delegate to Python library ─────────────────────────────────────────────

echo "$INPUT" | python3 "$MEMORY_LIB"

# ── Push ──────────────────────────────────────────────────────────────────

if [ "$PUSH" = "1" ] && [ "$ACTION" != "list" ]; then
  (
    cd "$SCRIPT_DIR/.."
    if git diff --quiet -- chip1/MEMORY.md 2>/dev/null && git diff --quiet 2>/dev/null; then
      exit 0
    fi
    git add chip1/MEMORY.md
    local author_msg=""
    [ -n "$AUTHOR" ] && author_msg=" (by $AUTHOR)"
    git commit -m "chip1: $ACTION $TITLE$author_msg" 2>/dev/null || true
    if git push 2>/dev/null; then
      echo "  (pushed to agent-knowledge)"
    else
      echo "  (push skipped — no remote configured or offline)"
    fi
  )
fi
