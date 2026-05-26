#!/usr/bin/env bash
# pr-memory.sh — Extract conventions and decisions from a GitHub PR.
#
# Fetches PR description, changed files, and review comments so the agent
# can identify new conventions, decisions, and patterns to persist in MEMORY.md.
#
# Usage:
#   bash pr-memory.sh 3959                        # auto-detect repo
#   bash pr-memory.sh 3959 --repo=altirllc/chip1-webui

set -euo pipefail

PR_NUMBER=""
REPO=""

for arg in "$@"; do
  case "$arg" in
    --repo=*) REPO="${arg#--repo=}" ;;
    --repo) echo "ERROR: --repo requires a value" >&2; exit 1 ;;
    *) PR_NUMBER="$arg" ;;
  esac
done

[ -n "$PR_NUMBER" ] || { echo "Usage: bash pr-memory.sh <PR-NUMBER> [--repo=org/repo]"; exit 1; }

GH_ARGS=""
[ -n "$REPO" ] && GH_ARGS="-R $REPO"

# Auto-detect repo
if [ -z "$REPO" ]; then
  REMOTE=$(git remote get-url origin 2>/dev/null || echo "")
  REPO=$(echo "$REMOTE" | sed -n 's/.*[:/]\([^/]*\/[^/]*\)\.git.*/\1/p')
  [ -n "$REPO" ] && GH_ARGS="-R $REPO"
fi

# Helper: pretty-print a JSON array of comments
format_comments() {
  python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
except:
    print('  (parse error)')
    sys.exit(0)
if not isinstance(data, list):
    print('  (unexpected format)')
    sys.exit(0)
if not data:
    print('  (none)')
    sys.exit(0)
for c in data:
    user = c.get('user', {}).get('login', '?')
    body = c.get('body', '') or ''
    # Strip excessive whitespace
    body = ' '.join(body.split())
    if len(body) > 500:
        body = body[:500] + '...(truncated)'
    print(f'  [{user}] {body}')
"
}

echo "========================================================================"
echo " PR #$PR_NUMBER${REPO:+ ($REPO)} — Memory Extraction"
echo "========================================================================"
echo ""

# ── PR metadata ────────────────────────────────────────────────────────────
echo ">>> METADATA"
gh $GH_ARGS pr view "$PR_NUMBER" --json title,body,author,state,mergedBy,labels,createdAt,mergedAt,baseRefName,headRefName 2>/dev/null || {
  echo "ERROR: Could not fetch PR #$PR_NUMBER."
  exit 1
}
echo ""

# ── Files changed ──────────────────────────────────────────────────────────
echo ">>> FILES CHANGED"
gh $GH_ARGS pr view "$PR_NUMBER" --json files 2>/dev/null | python3 -c "
import sys, json
data = json.load(sys.stdin)
for f in data.get('files', []):
    print(f\"  {f['path']}  (+{f['additions']}/-{f['deletions']})\")
" 2>/dev/null || echo "  (could not fetch)"
echo ""

# ── PR description ─────────────────────────────────────────────────────────
echo ">>> DESCRIPTION"
gh $GH_ARGS pr view "$PR_NUMBER" --json body 2>/dev/null | python3 -c "
import sys, json, re
body = json.load(sys.stdin).get('body', '') or ''
body = re.sub(r'!\[.*?\]\(.*?\)', '[image]', body)
body = re.sub(r'<img[^>]*>', '[image]', body)
print(body[:3000])
if len(body) > 3000: print('...(truncated)')
" 2>/dev/null || echo "  (empty)"
echo ""

# ── Review comments (on diff) ──────────────────────────────────────────────
echo ">>> REVIEW COMMENTS (on code)"
gh api "/repos/$REPO/pulls/$PR_NUMBER/comments" 2>/dev/null | format_comments || echo "  (could not fetch)"
echo ""

# ── Issue/PR conversation comments ─────────────────────────────────────────
echo ">>> CONVERSATION COMMENTS"
gh api "/repos/$REPO/issues/$PR_NUMBER/comments" 2>/dev/null | format_comments || echo "  (could not fetch)"
echo ""

echo "========================================================================"
echo " INSTRUCTIONS"
echo "========================================================================"
echo " 1. Read the PR description, files, and comments above"
echo " 2. Look for:"
echo "    - New conventions or patterns introduced"
echo "    - Architecture decisions discussed or decided"
echo "    - Deprecated patterns — what this PR moves away from"
echo "    - Important constraints discovered"
echo " 3. Present findings to the user, ask which to persist"
echo " 4. For each confirmed item:"
echo "    echo '{\"action\":\"add\",...}' | bash ~/agent-knowledge/chip1/update-memory.sh --push"
echo "========================================================================"
