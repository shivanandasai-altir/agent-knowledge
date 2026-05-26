# chip1 — Memory System for chip1-webui

This directory is the **shared memory and reference system** for the chip1-webui monorepo (`apps/crm`, `apps/myChip1`, `packages/*`).

It prevents the "start from zero" problem: agents read past decisions before writing code, and persist new discoveries so they're never learned twice.

---

## Quick Start

```bash
# Sync latest knowledge
cd ~/agent-knowledge && git pull --rebase

# Search for relevant decisions before starting work
python3 chip1/memory-search "PATCH mutation clearing a date field"

# Read a reference doc
cat chip1/docs/architecture-patterns.md

# Persist a new decision
echo '{"action":"add","title":"..."}' | bash chip1/update-memory.sh --push
```

---

## Files

| File | Purpose |
|------|---------|
| `MEMORY.md` | Decision journal: chronological entries with **Memory Index** (categorized) + per-entry **Tags** for search |
| `memory-search` | TF-IDF search tool (zero deps). Finds relevant entries even when phrasing differs. |
| `update-memory.sh` | CRUD script: `add`, `update`, `delete`, `list`. Auto-rebuilds Memory Index on every change. |
| `memory_lib.py` | Python library that parses and renders MEMORY.md tables |
| `pr-memory.sh` | Fetches PR metadata, diffs, comments from GitHub |
| `docs/` | Reference documentation (13 files) mirrored from `chip1-webui/.claude/docs/` |
| `SKILL.md` | pi agent skill definition for the memory system |

---

## How This Connects to chip1-webui

When working in `chip1-webui`, two things drive the memory system:

### 1. CLAUDE.md trigger table

The file `chip1-webui/CLAUDE.md` has a trigger table. Before starting any task, the agent checks this table:

| If you're working on... | The agent reads... |
|---|---|
| A PATCH mutation | `architecture-patterns.md` |
| A Formik form with cascading fields | `formik-patterns.md` |
| TanStack table column definitions | `simple-cells.md` |
| A filter system component | `filter-system.md` |
| NavBar / token refresh | `app-specific-patterns.md` |
| **Anything** | It runs `memory-search "<task>"` first |

### 2. Memory search before starting

CLAUDE.md tells the agent to **search, not read the whole file**:

```bash
~/agent-knowledge/chip1/memory-search "<brief description of the task>"
```

Then read only the matching entries from `MEMORY.md`.

---

## 🗣️ Prompts You Can Use

### Before asking an agent to write code

> "Before you start, run `memory-search` for what I'm about to ask. Read the top matches and apply any relevant patterns."

> "Check the memory journal for decisions about PATCH mutations before implementing this form submit."

### After discovering a pattern during a PR review

> "This review revealed a pattern. Persist it to the memory journal: title '...', context '...', pattern '...', tags 'PATCH, createDiff', source files pointing to the changed file, and push it."

### When extracting from a PR

> "Fetch PR #4099, analyze what pattern or decision emerged, and ask me if I want to persist it."

### When onboarding to an unfamiliar area

> "I need to work with filters. Search the memory journal for filter-related decisions and read the filter-system.md doc first."

### To bulk-check recent work for memory-worthy patterns

> "Look at the last 5 commits in this branch. Identify any new conventions or patterns that should be in the memory journal. Present them to me and ask before persisting."

---

## 🖥️ Commands

### Search the memory

```bash
# Generic search
python3 ~/agent-knowledge/chip1/memory-search "formik cascading fields onChange"

# Tag-based discovery (see what topics exist)
python3 ~/agent-knowledge/chip1/memory-search --list-tags
```

### Cross-project search (inherit patterns from sibling projects)

When starting a new project or exploring unfamiliar patterns, include results from established sibling projects:

```bash
# From chip1-mobile, search your own journal + include chip1 patterns
python3 ~/agent-knowledge/chip1-mobile/memory-search --include chip1 "PATCH mutation"

# Results from chip1 are labeled with "project: chip1"
# Results from the primary project show dates instead

# Include multiple projects
python3 ~/agent-knowledge/chip1-mobile/memory-search \
  --include chip1 --include chip1-analytics "pattern"

# From chip1, search a different primary project
python3 ~/agent-knowledge/chip1/memory-search --project chip1-mobile --include chip1 "API"
```

### Bootstrapping a new project

```bash
bash ~/agent-knowledge/chip1/new-project.sh chip1-mobile
```

Creates the project directory with symlinks to shared scripts. Push it:

```bash
cd ~/agent-knowledge && git add chip1-mobile && git commit -m "chip1-mobile: bootstrap" && git push
```

#### 🗣️ Prompt

> Bootstrap a new project called chip1-mobile in agent-knowledge, then push it. Also add a CLAUDE.md trigger pointing at it.

### Add a decision

```bash
echo '{
  "action": "add",
  "title": "Use createDiff for PATCH mutations",
  "context": "Sending full objects in PATCH causes backend validations on unrelated field groups",
  "pattern": "Use createDiff from @chip1/utils/helpers/diffPatch to compute minimal diffs. Skip mutation when nothing changed.",
  "tags": "PATCH, createDiff, diff, minimal-payload, validations",
  "author": "your-name (via PR #NNNN review)",
  "sourceFiles": ["apps/crm/src/features/AccountDetails/AccountDetailsTab/AccountDetailsIsland.tsx"],
  "relatedDocs": [".claude/docs/architecture-patterns.md"],
  "supersedes": ""
}' | bash ~/agent-knowledge/chip1/update-memory.sh --push

# Or target a different project (future: chip1-mobile)
echo '{
  "project": "chip1-mobile",
  "action": "add",
  ...
}' | bash ~/agent-knowledge/chip1/update-memory.sh --push
```

### List all active entries

```bash
echo '{"action":"list"}' | bash ~/agent-knowledge/chip1/update-memory.sh
```

### Extract decisions from a PR

```bash
bash ~/agent-knowledge/chip1/pr-memory.sh 3925
```

### Read a reference doc

```bash
cat ~/agent-knowledge/chip1/docs/architecture-patterns.md
```

### Sync docs from chip1-webui (when docs are updated upstream)

```bash
cd ~/chip1-webui && bash .agents/skills/memory/sync-docs.sh --push
```

---

## Workflow Summary

```
┌─────────────────────────────────────────┐
│  You tell the agent to do something     │
└──────────┬──────────────────────────────┘
           ▼
┌─────────────────────────────────────────┐
│  Agent runs: memory-search "<task>"     │
│  → finds relevant past decisions        │
│  → reads matching entries from MEMORY.md│
│  → reads trigger-matched doc            │
└──────────┬──────────────────────────────┘
           ▼
┌─────────────────────────────────────────┐
│  Agent writes code applying patterns    │
└──────────┬──────────────────────────────┘
           ▼
┌─────────────────────────────────────────┐
│  If new pattern discovered:             │
│  update-memory.sh add --push            │
│  → auto-rebuilds Memory Index           │
│  → team syncs via git pull              │
└─────────────────────────────────────────┘
```

## Requirements

- `python3` — for memory-search, memory_lib.py, update-memory.sh
- `bash` — script runtime
- `gh` — GitHub CLI (for `pr-memory.sh` only)
- `git` — for pushing decisions
