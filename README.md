# agent-knowledge

**Shared knowledge repository** for AI coding agents (pi, Claude Code, Cursor).

Prevents the "start from zero every time" problem: agents read past decisions before writing code, and persist new discoveries so they're never learned twice.

Partitioned per project:

```
agent-knowledge/
├── chip1/                   # chip1-webui conventions, docs, and scripts
│   ├── MEMORY.md            # decision journal with Memory Index + search tags
│   ├── SKILL.md             # full agent instructions
│   ├── memory-search        # TF-IDF search tool (zero dependencies)
│   ├── update-memory.sh     # CRUD script
│   ├── pr-memory.sh         # extract decisions from a GitHub PR
│   └── docs/                # reference documentation (13 files)
├── chip1-mobile/            # future
└── README.md
```

---

## Setup — One Time

```bash
git clone git@github.com:shivanandasai-altir/agent-knowledge.git ~/agent-knowledge
```

Then point your project's CLAUDE.md / .cursorrules at it (see chip1-webui for an example).

---

## How to Use This (Prompts + Commands)

### 🧑‍💻 For Humans — Before Asking an Agent

When you're about to ask an agent to do something, first check what's already known:

```bash
# 1. Sync
cd ~/agent-knowledge && git pull --rebase

# 2. Search the memory journal
python3 chip1/memory-search "PATCH mutations clearing a date field"

# Sample output:
#   [1] PATCH mutations must forward diff.unset for cleared fields
#       score: 0.33  date: 2026-05-27
#       tags: PATCH, createDiff, unset, payload, mutation, clearing-fields
#       why: createDiff was called but diff.unset was never sent to the API...
#       how: Forward diff.unset alongside diff.changed...
```

Other useful searches:

```bash
# Finding form-related decisions
python3 chip1/memory-search "formik cascading fields onChange"

# Finding table patterns
python3 chip1/memory-search "table column definitions getSimpleCells"

# Listing all tags (to discover what's covered)
python3 chip1/memory-search --list-tags
```

### 🤖 For Agents — Before Writing Code

Your CLAUDE.md should instruct you to do this:

```bash
# 1. Sync
(cd ~/agent-knowledge && git pull --rebase)

# 2. Search — not read the whole file
~/agent-knowledge/chip1/memory-search "<brief description of the task>"

# 3. Read the top matches
# (output includes the context and pattern snippet)
```

**Embed this directly in your CLAUDE.md** (see chip1-webui for the exact format).

### 📝 Adding a New Decision

When you discover a convention, pattern, or architecture rule:

```bash
echo '{
  "action": "add",
  "title": "Use createDiff for PATCH mutations",
  "context": "Prevents backend validations on unrelated field groups",
  "pattern": "Use createDiff from @chip1/utils/helpers/diffPatch to compute minimal diffs",
  "tags": "PATCH, createDiff, diff, minimal-payload",
  "author": "your-name (via PR #NNNN review)",
  "sourceFiles": ["apps/crm/src/features/AccountDetails/AccountDetailsTab/AccountDetailsIsland.tsx"],
  "relatedDocs": [".claude/docs/architecture-patterns.md"],
  "supersedes": "Manual field-by-field comparison"
}' | bash ~/agent-knowledge/chip1/update-memory.sh --push
```

The `--push` flag commits and pushes for the team. Without it, writes locally.

### 📤 Extracting Decisions from a GitHub PR

PR descriptions and review comments often contain valuable context.

```bash
bash ~/agent-knowledge/chip1/pr-memory.sh 3925
```

Analyze the output, identify conventions, then persist them with `update-memory.sh --push`.

### 📖 Reading Reference Docs by Trigger

**CLAUDE.md** has a trigger table that maps task types to specific docs:

| If your task is... | Then read... |
|---|---|
| PATCH mutation | `architecture-patterns.md` |
| Formik form with cascading fields | `formik-patterns.md` |
| TanStack table column definitions | `simple-cells.md` |
| Filter system component | `filter-system.md` |
| NavBar / token refresh | `app-specific-patterns.md` |

---

## Files

| File | Purpose |
|------|---------|
| `chip1/MEMORY.md` | Decision journal with **Memory Index** (categorized overview) + per-entry **Tags** for search |
| `chip1/memory-search` | Zero-dependency TF-IDF search — finds relevant entries even when task phrasing differs from the original decision wording |
| `chip1/update-memory.sh` | CRUD script — `add`, `update`, `delete`, `list`. Auto-rebuilds Memory Index after every change. |
| `chip1/pr-memory.sh` | Fetches PR metadata, diffs, comments from GitHub for decision extraction |
| `chip1/memory_lib.py` | Python library for parsing/rendering MEMORY.md tables |
| `chip1/SKILL.md` | Full agent instructions (pi skill definition) |
| `chip1/docs/` | Reference docs mirrored from source project |

## CRUD Operations (update-memory.sh)

| Operation | Description |
|-----------|-------------|
| `add` | Adds entry. Checks for duplicates (NOOP). Supports `supersedes`, `tags`, `sourceFiles`, `relatedDocs`, `wikiFiles`. |
| `update` | Updates context/pattern/tags/author of an existing entry. |
| `delete` | Marks `archived` — never truly deleted, preserved for history. |
| `list` | Lists all entries grouped by status (active / superseded / archived). |

### Input Fields

| Field | Required | Description |
|-------|----------|-------------|
| `action` | ✅ | `add` \| `update` \| `delete` \| `list` |
| `title` | ✅ | Short, unique phrase (becomes the bold link) |
| `context` | ✅ | Why this decision was made |
| `pattern` | ✅ | The actionable convention or rule |
| `tags` | | Comma-separated keywords for `memory-search`, e.g. `"PATCH, createDiff, unset"` |
| `author` | | Who discovered it, e.g. `"your-name (via PR #3925)"` |
| `supersedes` | | Exact title of the entry this replaces |
| `sourceFiles` | | Array of source file paths |
| `relatedDocs` | | Array of doc paths |
| `wikiFiles` | | Array of wiki/ADR file names |

## Requirements

- `python3` — for memory-search, memory_lib.py, and update-memory.sh
- `bash` — script runtime
- `gh` — GitHub CLI (for `pr-memory.sh` only)
- `git` — for pushing decisions to the team
