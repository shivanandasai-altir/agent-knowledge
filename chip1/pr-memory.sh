#!/usr/bin/env bash
# pr-memory.sh — Extract conventions and decisions from a GitHub PR.
#
# Fetches PR description, changed files, and review comments so the agent
# can identify new conventions, decisions, and patterns to persist.
#
# Usage:
#   bash pr-memory.sh 3959                        # auto-detect repo
#   bash pr-memory.sh 3959 --repo=altirllc/chip1-webui
#
# Requires: gh (GitHub CLI), python3

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MEMORY_LIB="$SCRIPT_DIR/memory_lib.py"

format() {
  # Usage: format <command> [gh args...]
  # Runs gh, pipes JSON to memory_lib.py for formatting.
  local cmd="$1"; shift
  gh "$@" 2>/dev/null | python3 "$MEMORY_LIB" "$cmd" || echo "  (could not fetch)"
}

# ── Parse args ─────────────────────────────────────────────────────────────

PR_NUMBER=""
REPO=""

for arg in "$@"; do
  case "$arg" in
    --repo=*) REPO="${arg#--repo=}" ;;
    --repo)   echo "ERROR: --repo requires a value" >&2; exit 1 ;;
    *)        PR_NUMBER="$arg" ;;
  esac
done

[ -n "$PR_NUMBER" ] || { echo "Usage: bash pr-memory.sh <PR-NUMBER> [--repo=org/repo]" >&2; exit 1; }

# ── Auto-detect repo from git remote ───────────────────────────────────────

if [ -z "$REPO" ]; then
  REMOTE=$(git remote get-url origin 2>/dev/null || echo "")
  REPO=$(echo "$REMOTE" | sed -n 's/.*[:/]\([^/]*\/[^/]*\)\.git.*/\1/p')
fi

GH_ARGS=""
[ -n "$REPO" ] && GH_ARGS="-R $REPO"

# ── Header ─────────────────────────────────────────────────────────────────

echo "========================================================================="
echo " PR #$PR_NUMBER${REPO:+ ($REPO)} — Memory Extraction"
echo "========================================================================="
echo ""

# ── PR metadata ────────────────────────────────────────────────────────────

echo ">>> METADATA"
if ! gh $GH_ARGS pr view "$PR_NUMBER" \
  --json title,body,author,state,mergedBy,labels,createdAt,mergedAt,baseRefName,headRefName \
  2>/dev/null | python3 "$MEMORY_LIB" metadata; then
  echo "ERROR: Could not fetch PR #$PR_NUMBER." >&2
  exit 1
fi
echo ""

# ── Files changed ──────────────────────────────────────────────────────────

echo ">>> FILES CHANGED"
format files pr view $GH_ARGS "$PR_NUMBER" --json files
echo ""

# ── PR description ─────────────────────────────────────────────────────────

echo ">>> DESCRIPTION"
format body pr view $GH_ARGS "$PR_NUMBER" --json body
echo ""

# ── Review comments (on diff) ──────────────────────────────────────────────

echo ">>> REVIEW COMMENTS (on code)"
format comments api "/repos/$REPO/pulls/$PR_NUMBER/comments"
echo ""

# ── Issue/PR conversation comments ─────────────────────────────────────────

echo ">>> CONVERSATION COMMENTS"
format comments api "/repos/$REPO/issues/$PR_NUMBER/comments"
echo ""

# ── Instructions ───────────────────────────────────────────────────────────

echo "========================================================================="
echo " INSTRUCTIONS"
echo "========================================================================="
echo " 1. Read the PR description, files, and comments above"
echo " 2. Look for:"
echo "    - New conventions or patterns introduced"
echo "    - Architecture decisions discussed or decided"
echo "    - Deprecated patterns — what this PR moves away from"
echo "    - Important constraints discovered"
echo " 3. Present findings to the user, ask which to persist"
echo " 4. For each confirmed item:"
echo "    echo '{\"action\":\"add\",...}' | bash $SCRIPT_DIR/update-memory.sh --push"
echo "========================================================================="
