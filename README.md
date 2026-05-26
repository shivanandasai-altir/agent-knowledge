# agent-knowledge

Shared knowledge repository for AI coding agents (pi, Claude Code, Cursor).

Stores cross-session decision journals (`MEMORY.md`), conventions, and skills that
agents read before starting work and write to when discovering new patterns.

Partitioned per project so a single clone serves the whole organization:

```
agent-knowledge/
├── chip1/                # chip1-webui conventions and patterns
│   ├── MEMORY.md         # decision journal
│   ├── SKILL.md          # agent instructions
│   └── update-memory.sh  # CRUD script (bash + jq + python3)
└── README.md
```

## Setup

```bash
git clone git@github.com:shivanandasai-altir/agent-knowledge.git ~/agent-knowledge
```

## Usage

Each project's SKILL.md contains tool-specific instructions. In general:

```bash
# Before starting work — sync
(cd ~/agent-knowledge && git pull --rebase)

# Read decisions for your project
cat ~/agent-knowledge/chip1/MEMORY.md

# Add a new decision and share with the team
echo '{"action":"add","title":"...","context":"...","pattern":"..."}' \
  | bash ~/agent-knowledge/chip1/update-memory.sh --push
```

## Requirements

- `jq` — JSON parsing
- `python3` — MEMORY.md manipulation (handles UTF-8 reliably on macOS)
- `bash` — script runtime
