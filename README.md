# agent-knowledge

Shared knowledge repository for AI coding agents (pi, Claude Code, Cursor).

Stores cross-session decision journals, reference documentation, conventions,
and skills that agents read before starting work and write to when discovering
new patterns. Prevents the "Delhi vs Bangalore" problem — no blind appends,
duplicates are NOOP'd, outdated entries are superseded, not deleted.

Partitioned per project so a single clone serves the whole organization:

```
agent-knowledge/
├── chip1/                   # chip1-webui conventions, docs, and scripts
│   ├── MEMORY.md            # decision journal (17 seed entries)
│   ├── SKILL.md             # full agent instructions
│   ├── update-memory.sh     # CRUD script (bash + jq + python3)
│   ├── pr-memory.sh         # extract decisions from a GitHub PR
│   └── docs/                # reference documentation (13 files)
│       ├── architecture-patterns.md
│       ├── formik-patterns.md
│       ├── filter-system.md
│       ├── simple-cells.md
│       ├── table-loading-patterns.md
│       ├── selection-action-bar.md
│       ├── code-redundancy.md
│       ├── app-specific-patterns.md
│       ├── i18n-rules.md
│       ├── ts6-conventions.md
│       ├── feature-flags.md
│       ├── mcp-tools.md
│       └── wiki-reference.md
├── chip1-mobile/            # future project
└── README.md
```

## Setup

```bash
git clone git@github.com:shivanandasai-altir/agent-knowledge.git ~/agent-knowledge
```

## Usage

### Daily workflow

```bash
# Before starting work — sync shared knowledge
(cd ~/agent-knowledge && git pull --rebase)

# Read decisions for your project
cat ~/agent-knowledge/chip1/MEMORY.md

# Read reference docs when needed
cat ~/agent-knowledge/chip1/docs/architecture-patterns.md
```

### Adding a new decision

When an agent discovers a new convention, pattern, or architecture decision:

```bash
echo '{"action":"add","title":"Use createDiff for PATCH mutations","context":"Prevents backend validations on unrelated field groups","pattern":"Use createDiff from @chip1/utils/helpers/diffPatch to compute minimal diffs"}' \
  | bash ~/agent-knowledge/chip1/update-memory.sh --push
```

The `--push` flag commits and pushes for the team. Without it, writes locally.

### Extracting decisions from a GitHub PR

PR descriptions and review comments often contain valuable decisions that get lost.
Pass a PR number to extract them:

```bash
bash ~/agent-knowledge/chip1/pr-memory.sh 3959
```

The script fetches the PR title, description, files changed, review comments,
and conversation comments. An agent can then analyze the output, identify
conventions/decisions, and persist them via `update-memory.sh --push`.

### Syncing reference docs

Reference docs in `chip1/docs/` are mirrored from the source project
(e.g., `chip1-webui/.claude/docs/`). When docs are modified upstream, sync:

```bash
# From the source project directory
bash .agents/skills/memory/sync-docs.sh --push
```

## CRUD Operations

| Operation | Description |
|-----------|-------------|
| `add` | Adds entry. If `supersedes` matches an active entry, marks old as `superseded`. Exact duplicates are NOOP'd. |
| `update` | Updates context/pattern/wikiFiles/sourceFiles/relatedDocs of an existing entry. |
| `delete` | Marks entry as `archived` (kept in journal for history). |
| `list` | Lists all entries grouped by status. |

## Requirements

- `jq` — JSON parsing
- `python3` — MEMORY.md manipulation (handles UTF-8 reliably on macOS)
- `bash` — script runtime
- `gh` — GitHub CLI (for `pr-memory.sh` only)
