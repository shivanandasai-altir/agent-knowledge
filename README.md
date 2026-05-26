# agent-knowledge

**Shared engineering knowledge** for AI coding agents (pi, Claude Code, Cursor).

Prevents the "start from zero" problem: agents read past decisions before writing code, and persist new discoveries so they're never learned twice.

New projects inherit patterns from established siblings via cross-project search.

---

## Layout

```
agent-knowledge/
├── chip1/                   # chip1-webui knowledge (seed project)
│   ├── MEMORY.md            # decision journal with Memory Index + search tags
│   ├── SKILL.md             # pi agent skill definition
│   ├── memory-search        # TF-IDF search tool (zero dependencies)
│   ├── update-memory.sh     # CRUD script
│   ├── memory_lib.py        # Python library for MEMORY.md tables
│   ├── new-project.sh       # Bootstrap new project directories
│   ├── pr-memory.sh         # Extract decisions from a GitHub PR
│   └── docs/                # Reference documentation (13 files)
├── chip1-mobile/            # Created via new-project.sh
├── chip1-analytics/         # Future projects...
└── README.md
```

---

## Setup

```bash
git clone git@github.com:shivanandasai-altir/agent-knowledge.git ~/agent-knowledge
```

---

## Commands & Prompts

### Search

```bash
# Search a project's knowledge
python3 chip1/memory-search "PATCH mutation clearing a date field"

# Search a different project
python3 chip1/memory-search --project chip1-mobile "push notification"

# Cross-project: search chip1-mobile, also include chip1 patterns
python3 chip1/memory-search --project chip1-mobile --include chip1 "PATCH mutation"

# Include multiple sibling projects
python3 chip1/memory-search --project chip1-mobile \
  --include chip1 --include chip1-analytics "pattern"

# List tags
python3 chip1/memory-search --list-tags
python3 chip1/memory-search --project chip1-mobile --list-tags
```

**🗣️ Tell your AI agent:**

> "Before you start, run `memory-search` for what I'm about to ask. Read the top matches and apply any relevant patterns."

> "I'm new to chip1-mobile. Search its memory journal and include chip1 patterns too."

> "Search chip1-mobile for 'push notification' and include relevant results from chip1."

---

### Add a Decision

```bash
echo '{
  "action": "add",
  "title": "Use createDiff for PATCH mutations",
  "context": "Sending full objects causes backend validations on unrelated field groups",
  "pattern": "Use createDiff from @chip1/utils/helpers/diffPatch to compute minimal diffs",
  "tags": "PATCH, createDiff, diff, minimal-payload",
  "author": "your-name (via PR #NNNN)",
  "sourceFiles": ["apps/crm/src/features/.../file.tsx"],
  "relatedDocs": [".claude/docs/architecture-patterns.md"]
}' | bash chip1/update-memory.sh --push
```

Target a different project:

```bash
echo '{"project":"chip1-mobile","action":"add","title":"..."}' | bash chip1/update-memory.sh --push
```

**🗣️ Tell your AI agent:**

> "This fix reveals a pattern. Persist it to the memory journal: title '...', context '...', pattern '...', tags 'PATCH, createDiff', source files pointing to the changed file, and push it."

> "Extract the key convention or decision from PR #3925 and persist it to the memory journal with `--push`. Include context, pattern, tags, author, source files, and which doc it relates to."

> "Persist this decision to the chip1-mobile project memory journal. Include `project: chip1-mobile` in the JSON."

---

### List / Delete

```bash
echo '{"action":"list"}' | bash chip1/update-memory.sh
echo '{"project":"chip1-mobile","action":"delete","title":"..."}' | bash chip1/update-memory.sh
```

---

### Extract Decisions from a PR

```bash
bash chip1/pr-memory.sh 3925
```

**🗣️ Tell your AI agent:**

> "Fetch PR #3925 and extract any new conventions or architecture decisions from it. For each finding, ask me if I want to persist it. Then `update-memory.sh --push` the confirmed ones with proper context, pattern, tags, and source files."

> "Look through the last 5 merged PRs. Identify patterns worth persisting. Present your findings and ask before pushing."

---

### Bootstrap a New Project

```bash
cd ~/agent-knowledge
bash chip1/new-project.sh chip1-mobile
git add chip1-mobile
git commit -m "chip1-mobile: bootstrap"
git push
```

**🗣️ Tell your AI agent:**

> "Bootstrap a new project called chip1-mobile in agent-knowledge using new-project.sh, then push it. Also add a CLAUDE.md trigger pointing at it."

---

## CRUD Input Fields

| Field | Required | Description |
|-------|----------|-------------|
| `action` | ✅ | `add` \| `update` \| `delete` \| `list` |
| `title` | ✅ | Short unique phrase |
| `context` | ✅ | Why this decision was made |
| `pattern` | ✅ | The actionable convention |
| `project` | | Subdirectory name (default: `chip1`) |
| `tags` | | Comma-separated keywords for search |
| `author` | | Who discovered it |
| `supersedes` | | Exact title this replaces |
| `sourceFiles` | | Array of file paths |
| `relatedDocs` | | Array of doc paths |
| `wikiFiles` | | Array of wiki file names |

## Requirements

- `python3` — scripts
- `bash` — runtime
- `gh` — GitHub CLI (for `pr-memory.sh` only)
- `git` — pushing to the team
