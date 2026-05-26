# chip1 — Engineering Knowledge Base

This directory is the **shared engineering knowledge** for the [chip1-webui](https://github.com/altirllc/chip1-webui) monorepo (`apps/crm`, `apps/myChip1`, `packages/*`).

It captures conventions, architecture decisions, and patterns so AI agents never start from zero.

---

## Quick Start

```bash
cd ~/agent-knowledge && git pull --rebase
python3 chip1/memory-search "PATCH mutation clearing a date field"
cat chip1/docs/architecture-patterns.md
echo '{"action":"add","title":"..."}' | bash chip1/update-memory.sh --push
```

---

## Files

| File | Purpose |
|------|---------|
| `MEMORY.md` | Decision journal — chronological entries with **Memory Index** + **Tags** for search |
| `memory-search` | TF-IDF search tool (zero deps). Supports `--include` for cross-project search. |
| `update-memory.sh` | CRUD script: `add`, `update`, `delete`, `list`. Auto-rebuilds Memory Index. Supports `project` field. |
| `memory_lib.py` | Python library for parsing / rendering MEMORY.md tables |
| `new-project.sh` | Bootstrap a new project subdirectory with symlinks to shared tooling |
| `pr-memory.sh` | Fetch PR metadata, diffs, comments from GitHub |
| `SKILL.md` | pi agent skill definition |
| `docs/` | Reference documentation (13 files) mirrored from `chip1-webui/.claude/docs/` |

---

## How This Connects to chip1-webui

### CLAUDE.md trigger table

`chip1-webui/CLAUDE.md` maps task types to specific docs:

| If you're working on... | The agent reads... |
|---|---|
| A PATCH mutation | `architecture-patterns.md` |
| A Formik form with cascading fields | `formik-patterns.md` |
| TanStack table columns | `simple-cells.md` |
| A filter component | `filter-system.md` |
| NavBar / token refresh | `app-specific-patterns.md` |
| **Anything** | Runs `memory-search "<task>"` first |

---

## Commands & Prompts

### Search the memory

```bash
# Basic search
python3 ~/agent-knowledge/chip1/memory-search "formik cascading fields onChange"

# Tag-based discovery
python3 ~/agent-knowledge/chip1/memory-search --list-tags

# Search a different project
python3 ~/agent-knowledge/chip1/memory-search --project chip1-mobile "push notification"
```

**🗣️ Tell your AI agent:**

> "Before you start, run `memory-search` for what I'm about to ask. Read the top matches and apply any relevant patterns."

> "Check the memory journal for decisions about PATCH mutations before implementing this form submit."

> "I need to work with filters. Search the memory journal for filter-related decisions and read the filter-system.md doc first."

---

### Cross-project search (inherit patterns from sibling projects)

```bash
# From chip1-mobile, include chip1 patterns
python3 ~/agent-knowledge/chip1-mobile/memory-search --include chip1 "PATCH mutation"

# Include multiple sibling projects
python3 ~/agent-knowledge/chip1-mobile/memory-search \
  --include chip1 --include chip1-analytics "pattern"

# From chip1, search a different primary project
python3 ~/agent-knowledge/chip1/memory-search --project chip1-mobile --include chip1 "API"
```

**🗣️ Tell your AI agent:**

> "I'm new to this codebase. Search the memory journal and include chip1 patterns so I can see what conventions already exist."

> "Run `memory-search --include chip1` for everything I ask until the project builds up its own patterns."

---

### Add a decision

```bash
echo '{
  "action": "add",
  "title": "Use createDiff for PATCH mutations",
  "context": "Sending full objects in PATCH causes backend validations",
  "pattern": "Use createDiff from @chip1/utils/helpers/diffPatch",
  "tags": "PATCH, createDiff, diff, minimal-payload",
  "author": "your-name (via PR #NNNN)",
  "sourceFiles": ["apps/crm/src/features/.../file.tsx"],
  "relatedDocs": [".claude/docs/architecture-patterns.md"]
}' | bash ~/agent-knowledge/chip1/update-memory.sh --push

# Target a different project
echo '{"project":"chip1-mobile","action":"add","title":"..."}' | bash ~/agent-knowledge/chip1/update-memory.sh --push
```

**🗣️ Tell your AI agent:**

> "This review revealed a pattern. Persist it to the memory journal: title '...', context '...', pattern '...', tags 'PATCH, createDiff', source files pointing to the changed file, and push it."

> "Persist this decision to the chip1-mobile project. Include `project: chip1-mobile` in the JSON."

---

### List / Delete

```bash
# List all active entries
echo '{"action":"list"}' | bash ~/agent-knowledge/chip1/update-memory.sh

# List from another project
echo '{"project":"chip1-mobile","action":"list"}' | bash ~/agent-knowledge/chip1/update-memory.sh

# Delete (archives — never truly deleted)
echo '{"project":"chip1-mobile","action":"delete","title":"Old pattern"}' | bash ~/agent-knowledge/chip1/update-memory.sh
```

---

### Extract decisions from a PR

```bash
bash ~/agent-knowledge/chip1/pr-memory.sh 3925
```

**🗣️ Tell your AI agent:**

> "Fetch PR #4099, analyze what pattern or decision emerged, and ask me if I want to persist it."

> "Look at the last 5 commits in this branch. Identify any new conventions or patterns that should be in the memory journal. Present them to me and ask before persisting."

---

### Bootstrap a new project

```bash
cd ~/agent-knowledge
bash chip1/new-project.sh chip1-mobile
git add chip1-mobile
git commit -m "chip1-mobile: bootstrap"
git push
```

Creates `~/agent-knowledge/chip1-mobile/` as a sibling of `chip1/` (not inside it), with symlinks to shared scripts.

**🗣️ Tell your AI agent:**

> "Bootstrap a new project called chip1-mobile in agent-knowledge using new-project.sh, then push it. Also add a CLAUDE.md trigger pointing at it."

---

### Read a reference doc

```bash
cat ~/agent-knowledge/chip1/docs/architecture-patterns.md
```

### Sync docs from chip1-webui

```bash
cd ~/chip1-webui && bash .agents/skills/memory/sync-docs.sh --push
```

---

## Workflow Summary

```
┌─────────────────────────────────────────────┐
│  You tell the agent to do something         │
└──────────┬──────────────────────────────────┘
           ▼
┌─────────────────────────────────────────────┐
│  Agent runs: memory-search "<task>"         │
│  → finds relevant past decisions            │
│  → reads matching entries from MEMORY.md    │
│  → reads trigger-matched doc                │
│  → (optional) --include sibling projects    │
└──────────┬──────────────────────────────────┘
           ▼
┌─────────────────────────────────────────────┐
│  Agent writes code applying patterns        │
└──────────┬──────────────────────────────────┘
           ▼
┌─────────────────────────────────────────────┐
│  If new pattern discovered:                 │
│  update-memory.sh add --push                │
│  → auto-rebuilds Memory Index               │
│  → team syncs via git pull                  │
└─────────────────────────────────────────────┘
```

## Requirements

- `python3` — scripts
- `bash` — runtime
- `gh` — GitHub CLI (for `pr-memory.sh`)
- `git` — pushing decisions
