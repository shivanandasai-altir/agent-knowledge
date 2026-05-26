# Roadmap

Future directions for the agent-knowledge system. Ideas are ordered by priority within each phase. Not committing to any — this is a thinking document.

---

## Phase 1 — Polish the Core (Next)

Small changes that improve daily DX without architectural changes.

### 1.1 Zero-result tag suggestions

When `memory-search` finds nothing, suggest existing tags to guide the user:

```
$ python3 chip1/memory-search "zzzzz"
  (no matches found)
  Try these existing tags: PATCH, createDiff, Formik, Zustand, Table, filters
```

~10 lines in `memory-search`. The tag list is already available via `--list-tags`.

### 1.2 Memory health check

A `memory-check` script that reports journal quality:

```bash
$ bash chip1/memory-check
✓ 24 active entries
✓ All entries have tags
⚠ 3 entries missing source files
✓ Index is up to date
✓ No cross-project duplicates detected
```

Useful for maintenance as the journal grows past 50 entries. Checks for:
- Missing tags
- Missing source files / related docs
- Entries with identical patterns (potential duplicates)
- Stale/superseded entries that could be archived

### 1.3 Search result limit flag

`memory-search --top 10` to override the default 5 results. Useful for broad queries like searching a whole project's patterns.

---

## Phase 2 — Cross-Project Intelligence

### 2.1 Cross-project `relatedEntries` links

A `relatedEntries` field in the add JSON that accepts entry titles from any project:

```bash
echo '{
  "action": "add",
  "title": "Mobile push notification retry logic",
  "relatedEntries": [
    {"project": "chip1", "title": "useQuery enabled for optional relationships"}
  ]
}' | bash chip1-mobile/update-memory.sh --push
```

The Memory Index would show these links so you can navigate from a chip1 result to related chip1-mobile entries.

### 2.2 `--include` with relevance boost

When searching with `--include`, cross-project results that are directly linked via `relatedEntries` get a score boost so they rank higher.

---

## Phase 3 — Automated PR Extraction

### 3.1 The vision (user's idea)

Whenever a PR is approved and merged in chip1-webui, if it has a specific label (e.g., `memory-pattern`), automatically extract key information and persist it to the memory journal.

**Workflow:**

```
1. Developer opens PR in chip1-webui
2. Reviewer adds label `memory-pattern` during review
3. PR is merged
4. GitHub Action triggers on merge + label
5. Action fetches PR title, description, files changed, review comments
6. Creates a memory entry with:
   - Title ← PR title
   - Context ← PR description summary
   - Pattern ← extracted from review comments / description
   - Tags ← from PR labels
   - Source files ← files changed in the PR
   - Author ← PR author
7. Opens a PR against agent-knowledge with the proposed entry
8. Team reviews the memory PR, edits as needed, merges
```

**Key design questions:**

| Question | Options |
|----------|---------|
| When does it trigger? | On merge with label `memory-pattern` |
| Who reviews the extracted entry? | A PR is opened in agent-knowledge — human reviews and edits before merging |
| What if the extraction is low quality? | The memory PR can be rejected or edited. Over time, the extraction prompt can be tuned. |
| Multiple labels? | Could use `memory:*` convention — `memory:pattern`, `memory:decision`, `memory:deprecation` |
| What about sensitive info? | Only public PR metadata — no code content |

### 3.2 Technical sketch

A GitHub Action workflow in chip1-webui:

```yaml
# .github/workflows/extract-memory.yml
on:
  pull_request:
    types: [closed]

jobs:
  extract:
    if: github.event.pull_request.merged && contains(github.event.pull_request.labels.*.name, 'memory-pattern')
    steps:
      - uses: actions/checkout@v4
      - run: bash .agents/skills/memory/pr-memory.sh ${{ github.event.number }} > /tmp/pr-data.txt
      - uses: actions/github-script@v7
        with:
          script: |
            // Read PR data, construct JSON for update-memory.sh
            // Open a PR against agent-knowledge repo
```

The heavy lifting is already done (`pr-memory.sh` + `update-memory.sh`). The missing piece is:
- The GitHub Action wiring
- A prompt/LLM call to distill PR data into a good memory entry
- The PR-against-agent-knowledge workflow

### 3.3 Simpler alternative: periodic sweep

Instead of per-PR automation, a weekly scheduled action:

```yaml
on:
  schedule:
    - cron: "0 9 * * 1"  # Monday morning
```

Fetches all PRs merged in the last week with label `memory-pattern`, groups them, and opens a single PR against agent-knowledge with batch entries. Less noise, easier to review.

### 3.4 Even simpler: developer-driven CLI

A developer runs a command after merging:

```bash
bash .agents/skills/memory/pr-memory.sh 3925 --extract
```

This fetches the PR, opens an interactive editor to refine the entry, then calls `update-memory.sh --push`. No CI/CD changes needed.

---

## Phase 4 — Quality & Scale

### 4.1 Template system for entries

Pre-defined templates for common entry types to ensure consistent quality:

```bash
echo '{"action":"add","template":"bug-fix","title":"..."}' | bash update-memory.sh --push
```

Templates provide structured hints:
- **`bug-fix`**: Emphasizes root cause, the incorrect assumption, and the fix pattern
- **`decision`**: Architecture decision record style — context, options considered, chosen approach
- **`convention`**: Coding standard — when to apply, example, anti-pattern
- **`deprecation`**: What's being replaced, migration path, timeline

### 4.2 Auto-suggest tags on add

When adding an entry, `update-memory.sh` compares the title+context against existing entries and suggests tags:

```
Suggested tags based on your entry: "PATCH, createDiff, unset, payload"
Accept? [Y/n]: Y
```

Prevents tag drift (e.g., "patch" vs "PATCH" vs "Patching").

### 4.3 Stale entry detection

If a MEMORY.md entry's source files have been deleted or heavily modified in the main repo, flag it for review. Requires cross-repo awareness — complex.

---

## Phase 5 — Embedding-Based Search

When the journal exceeds 500+ entries, TF-IDF starts losing precision. Switch to embedding search:

- Use a small local model (e.g., `all-MiniLM-L6-v2` via `sentence-transformers`)
- Pre-compute embeddings on `--rebuild-index`
- Search becomes cosine similarity in embedding space
- Catches genuinely semantic matches that TF-IDF misses

No action needed now. TF-IDF is sufficient for the current scale (<100 entries).

---

## Summary by Effort

| Effort | Ideas |
|--------|-------|
| **~1 hour** | Zero-result tag suggestions, search result limit flag, developer-driven PR extraction CLI |
| **~2-3 hours** | Memory health check, auto-suggest tags, template system |
| **~1 day** | Cross-project relatedEntries, GitHub Action for automated PR extraction |
| **~1 week** | Embedding-based search, stale entry detection |
