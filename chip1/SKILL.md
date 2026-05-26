---
name: chip1-memory
description: Shared project memory for chip1-webui. Read MEMORY.md before starting work; call update-memory.sh when discovering new conventions or decisions. Prevents the "Delhi vs Bangalore" append-only contradiction problem.
---

# Memory Journal — chip1

This is the skill definition for the chip1 project memory journal located at `~/agent-knowledge/chip1/`.

It works with **pi**, **Claude Code**, and **Cursor** — all three read the same `MEMORY.md` and call the same `update-memory.sh`.

## The Three Layers

| Layer | File | Description |
|-------|------|-------------|
| **Episodic** | `chip1/MEMORY.md` | Chronological decision journal. Each entry has status (`active`, `superseded`, `suppressed`, `archived`), context, pattern, and optional links to code. |
| **Structural** | `.code-review-graph/wiki/` (in chip1-webui) | Auto-generated map of source files, dependencies, code communities. Grounds decisions in actual code. |
| **Operational** | `chip1/update-memory.sh` | CRUD script — checks duplicates, handles supersedes gracefully, never produces contradictory entries. |

## Before Starting Work

```bash
# 1. Sync shared knowledge
(cd ~/agent-knowledge && git pull --rebase)

# 2. Read the journal
cat ~/agent-knowledge/chip1/MEMORY.md

# 3. Also search the graph wiki (inside chip1-webui)
grep -ril "<feature>" ~/agent-knowledge/chip1/MEMORY.md .code-review-graph/wiki/
```

## When Discovering a New Convention or Decision

```bash
# Add a decision and push for the team
echo '{
  "action":"add",
  "title":"Use createDiff for PATCH mutations",
  "context":"Prevents backend validations on unrelated field groups",
  "pattern":"Use createDiff from @chip1/utils/helpers/diffPatch to compute minimal PATCH diffs",
  "supersedes":"Manual field-by-field comparison",
  "wikiFiles":["accountdetails-account.md"],
  "relatedDocs":[".claude/docs/architecture-patterns.md"]
}' | bash ~/agent-knowledge/chip1/update-memory.sh --push
```

### Operations

| Operation | Description |
|-----------|-------------|
| `add` | Adds entry. If `supersedes` matches an active entry, marks old as `superseded`. If exact title+pattern exists, NOOPs. |
| `update` | Updates context/pattern/wikiFiles/sourceFiles/relatedDocs of an existing entry. |
| `delete` | Marks entry as `archived` (kept in journal for history). |
| `list` | Lists all entries grouped by status. |

### Flags

| Flag | Description |
|------|-------------|
| `--push` | After writing, auto-commit and push to the agent-knowledge repo. Use for team sharing. |
| (none) | Write locally only. Use when offline or testing. |

## CRUD Rules

1. **NOOP on duplicate** — Same title + same pattern = ignored.
2. **Supersede on contradiction** — New fact contradicts an old one? Old marked `superseded`, linked to new.
3. **Never append blindly** — Always checks existing entries first.
4. **Never delete** — Mark as `archived` instead, preserving history for temporal queries.
5. **Link to structure** — Include `wikiFiles` and `sourceFiles` when adding, to ground decisions in code.

## MEMORY.md Format

```markdown
### YYYY-MM-DD — Title
Status: active|superseded|suppressed|archived
Context: Why this decision was made
Pattern: The actionable convention or rule
Supersedes: Exact title of the entry this replaces (optional)
Superseded by: Exact title of the entry that replaced this (optional)
Wiki files: accountdetails-account.md (optional)
Source files: apps/crm/src/features/AccountDetails/... (optional)
Related docs: .claude/docs/architecture-patterns.md (optional)
```
