#!/usr/bin/env bash
# update-memory.sh — Write-time intelligence for the project memory journal.
#
# Reads MEMORY.md, applies CRUD logic (add with supersede, update, delete, list),
# and writes back. Never appends blindly — checks duplicates, handles supersedes.
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
#   wikiFiles   - Array of wiki file names (optional)
#   sourceFiles - Array of source file paths (optional)
#   relatedDocs - Array of doc file paths (optional)
#   author      - Who made the change (optional, for audit trail)
#
# Requires: jq, python3

set -euo pipefail

PUSH="${PUSH:-0}"
for arg in "$@"; do
  [ "$arg" = "--push" ] && PUSH=1
done

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MEMORY_FILE="$SCRIPT_DIR/MEMORY.md"
TODAY=$(date +%Y-%m-%d)

# CI guard — if MEMORY.md doesn't exist, skip silently (CI environments, setup issues)
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

ACTION=$(echo "$INPUT"   | jq -r '.action // ""')
TITLE=$(echo "$INPUT"    | jq -r '.title // ""')
CONTEXT=$(echo "$INPUT"  | jq -r '.context // ""')
PATTERN=$(echo "$INPUT"  | jq -r '.pattern // ""')
SUPERSEDES=$(echo "$INPUT" | jq -r '.supersedes // ""')
WIKI_FILES=$(echo "$INPUT"  | jq -r '( .wikiFiles // [] ) | join(", ")')
SOURCE_FILES=$(echo "$INPUT" | jq -r '( .sourceFiles // [] ) | join(", ")')
RELATED_DOCS=$(echo "$INPUT" | jq -r '( .relatedDocs // [] ) | join(", ")')
AUTHOR=$(echo "$INPUT"   | jq -r '.author // ""')

if [ -z "$ACTION" ]; then
  echo "ERROR: action is required (add | update | delete | list)" >&2
  exit 1
fi

# ── Actions ───────────────────────────────────────────────────────────────
# Each action passes arguments to python3 via:  python3 - <arg>... <<'PYEOF'

cmd_list() {
  python3 - "$MEMORY_FILE" <<'PYEOF'
import sys, re

entries = []
entry_title = None
entry_date = None
entry_status = "active"

with open(sys.argv[1], encoding="utf-8") as f:
  for line in f:
    m = re.match(r"^### (\d{4}-\d{2}-\d{2})\s+[-—–]+\s+(.*)", line)
    if m:
      if entry_title is not None:
        entries.append((entry_title, entry_date, entry_status))
      entry_date = m.group(1)
      entry_title = m.group(2).strip()
      entry_status = "active"
      continue
    m = re.match(r"^Status:\s*(.+)", line)
    if m and entry_title is not None:
      entry_status = m.group(1).strip()

if entry_title is not None:
  entries.append((entry_title, entry_date, entry_status))

active = [(t, d) for t, d, s in entries if s == "active"]
superseded = [(t, d) for t, d, s in entries if s in ("superseded", "suppressed")]
archived = [(t, d) for t, d, s in entries if s == "archived"]

print(f"## Active Entries ({len(active)})")
for t, d in active:
  print(f"  [{d}] {t}")
print()
print(f"## Superseded/Suppressed ({len(superseded)})")
for t, d in superseded:
  print(f"  [{d}] {t}")
print()
print(f"## Archived ({len(archived)})")
for t, d in archived:
  print(f"  [{d}] {t}")
PYEOF
}

cmd_add() {
  if [ -z "$TITLE" ]; then
    echo "ERROR: title is required" >&2
    exit 1
  fi

  python3 - "$MEMORY_FILE" "$TITLE" "$CONTEXT" "$PATTERN" "$SUPERSEDES" "$TODAY" \
           "$WIKI_FILES" "$SOURCE_FILES" "$RELATED_DOCS" "$AUTHOR" <<'PYEOF'
import sys, re

filepath = sys.argv[1]
target_title = sys.argv[2].strip()
new_context = sys.argv[3] if len(sys.argv) > 3 else ""
new_pattern = sys.argv[4] if len(sys.argv) > 4 else ""
supersedes_title = sys.argv[5].strip() if len(sys.argv) > 5 and sys.argv[5] else ""
today = sys.argv[6]
wiki_files = sys.argv[7] if len(sys.argv) > 7 else ""
source_files = sys.argv[8] if len(sys.argv) > 8 else ""
related_docs = sys.argv[9] if len(sys.argv) > 9 else ""
author = sys.argv[10] if len(sys.argv) > 10 else ""

with open(filepath, "r", encoding="utf-8") as f:
  lines = f.read().split("\n")

# Parse entries
entries = []
i = 0
n = len(lines)
while i < n:
  m = re.match(r"^### (\d{4}-\d{2}-\d{2})\s+[-—–]+\s+(.*)", lines[i])
  if m:
    start = i
    title = m.group(2).strip()
    status = "active"
    pattern = ""
    i += 1
    while i < n and not re.match(r"^### ", lines[i]):
      sm = re.match(r"^Status:\s*(.+)", lines[i])
      if sm: status = sm.group(1).strip()
      pm = re.match(r"^Pattern:\s*(.*)", lines[i])
      if pm: pattern = pm.group(1).strip()
      i += 1
    entries.append((start, i - 1, title, status, pattern))
  else:
    i += 1

# Check for existing active entry with same title
found = None
for idx, (s, e, t, st, p) in enumerate(entries):
  if t == target_title and st == "active":
    found = (idx, s, e, p)
    break

if found is not None:
  idx, start, end, existing_pattern = found
  if existing_pattern == new_pattern:
    print(f"NOOP: Entry \"{target_title}\" already exists with same pattern.")
    sys.exit(0)
  # Update in place
  for line_no in range(start, end + 1):
    if re.match(r"^Context:\s", lines[line_no]) and new_context:
      lines[line_no] = f"Context: {new_context}"
    if re.match(r"^Pattern:\s", lines[line_no]) and new_pattern:
      lines[line_no] = f"Pattern: {new_pattern}"
  with open(filepath, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
  print(f"UPDATED: \"{target_title}\" (same title, pattern refined).")
  sys.exit(0)

# New entry — handle supersedes
if supersedes_title:
  marker = re.compile(
    r"^### \d{4}-\d{2}-\d{2}\s+[-—–]+\s+" + re.escape(supersedes_title) + r"\s*$"
  )
  for i, line in enumerate(lines):
    if marker.match(line):
      for j in range(i, min(i + 10, len(lines))):
        if re.match(r"^Status:\s+active", lines[j]):
          lines[j] = "Status: superseded"
          after = lines[j + 1:]
          lines = lines[:j + 1] + [f"Superseded by: {target_title}"] + after
          break
      break

# Append the new entry block
block = f"### {today} — {target_title}"
block += f"\nStatus: active"
if author:
    block += f"\nAuthor: {author}"
block += f"\nContext: {new_context}"
block += f"\nPattern: {new_pattern}"
if supersedes_title:
  block += f"\nSupersedes: {supersedes_title}"
if wiki_files:
  block += f"\nWiki files: {wiki_files}"
if source_files:
  block += f"\nSource files: {source_files}"
if related_docs:
  block += f"\nRelated docs: {related_docs}"

lines.append("")
lines.append(block)

with open(filepath, "w", encoding="utf-8") as f:
  f.write("\n".join(lines))

msg = f"ADDED: \"{target_title}\""
if supersedes_title:
  msg += f" (supersedes \"{supersedes_title}\")"
msg += "."
print(msg)
PYEOF
}

cmd_update() {
  python3 - "$MEMORY_FILE" "$TITLE" "$CONTEXT" "$PATTERN" "$AUTHOR" <<'PYEOF'
import sys, re

filepath = sys.argv[1]
target_title = sys.argv[2].strip()
new_context = sys.argv[3] if len(sys.argv) > 3 else ""
new_pattern = sys.argv[4] if len(sys.argv) > 4 else ""
author = sys.argv[5] if len(sys.argv) > 5 else ""

with open(filepath, "r", encoding="utf-8") as f:
  lines = f.read().split("\n")

found = False
in_entry = False
for i, line in enumerate(lines):
  m = re.match(r"^### (\d{4}-\d{2}-\d{2})\s+[-—–]+\s+(.*)", line)
  if m:
    in_entry = m.group(2).strip() == target_title
    continue
  if in_entry:
    if re.match(r"^Context:\s", line) and new_context:
      lines[i] = f"Context: {new_context}"
      found = True
    if re.match(r"^Pattern:\s", line) and new_pattern:
      lines[i] = f"Pattern: {new_pattern}"
      found = True
    if re.match(r"^Author:\s", line) and author:
      lines[i] = f"Author: {author}"
      found = True

if found:
  with open(filepath, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
  print(f"UPDATED: \"{target_title}\".")
else:
  print(f"ERROR: Entry \"{target_title}\" not found.")
PYEOF
}

cmd_delete() {
  python3 - "$MEMORY_FILE" "$TITLE" "$AUTHOR" <<'PYEOF'
import sys, re

filepath = sys.argv[1]
target_title = sys.argv[2].strip()
author = sys.argv[3] if len(sys.argv) > 3 else ""

with open(filepath, "r", encoding="utf-8") as f:
  lines = f.read().split("\n")

found = False
in_entry = False
for i, line in enumerate(lines):
  m = re.match(r"^### (\d{4}-\d{2}-\d{2})\s+[-—–]+\s+(.*)", line)
  if m:
    in_entry = m.group(2).strip() == target_title
    continue
  if in_entry and re.match(r"^Status:\s", line):
    lines[i] = "Status: archived"
    if author:
      lines.insert(i + 1, f"Archived by: {author}")
    found = True
    break

if found:
  with open(filepath, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
  print(f"ARCHIVED: \"{target_title}\". Entry kept in journal for history.")
else:
  print(f"ERROR: Entry \"{target_title}\" not found.")
PYEOF
}

# ── Push ──────────────────────────────────────────────────────────────────

do_push() {
  local repo_root
  repo_root="$(cd "$SCRIPT_DIR/.." && pwd)"
  cd "$repo_root"
  if git diff --quiet -- chip1/MEMORY.md 2>/dev/null; then
    # If MEMORY.md wasn't the file changed, try --all
    if git diff --quiet 2>/dev/null; then
      return 0
    fi
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
}

# ── Dispatch ──────────────────────────────────────────────────────────────

case "$ACTION" in
  list)   cmd_list ;;
  add)    cmd_add ;;
  update) cmd_update ;;
  delete) cmd_delete ;;
  *)
    echo "ERROR: Unknown action \"$ACTION\"" >&2
    exit 1
    ;;
esac

# ── Post-write: push if requested ─────────────────────────────────────────

if [ "$PUSH" = "1" ] && [ "$ACTION" != "list" ]; then
  do_push
fi
