# Wiki Reference Workflow

**Trigger:** Read this file before answering repository-specific questions, tracing existing code behavior/dependencies, or working in an unfamiliar feature area.

## Purpose

Use `.code-review-graph/wiki/` AND `.agents/skills/memory/MEMORY.md` as the first-stop, on-demand knowledge sources for this repo.

These two sources complement each other:
- **Graph wiki** (`wiki/`) — structural: file dependencies, code communities, function members
- **Memory journal** (`MEMORY.md`) — episodic: project decisions, conventions, architecture patterns

This keeps context small: load only the few files that match the task instead of reading many source files upfront.

## Rules

- Do **not** read the whole wiki folder or MEMORY.md without search.
- Search for the **smallest relevant set** of wiki files AND MEMORY.md entries first.
- Prefer `grep` + `read` for lookup across both sources:
  ```bash
  grep -ril "<keyword>" .code-review-graph/wiki/ .agents/skills/memory/MEMORY.md .claude/docs/
  ```
- Use `ls` when you need to browse file names.
- Do **not** rely on broad recursive file discovery as the primary lookup method here.
- **MEMORY.md** entries with status `superseded` should be skipped — read the superseding entry instead.
- Use wiki files to ground answers, locate source files, and map dependencies.
- **Verify in source files before editing code or making definitive claims** — the wiki is a navigation aid, not the final source of truth.

## Related
- [MCP Tools](mcp-tools.md) — graph tools for deeper code traversal when wiki search is insufficient

## Search Workflow

1. Extract the main task keywords:
   - feature/page/component name
   - API domain
   - hook/function name
   - route/tab/island name
   - app name (`crm`, `myChip1`)
2. Try a **targeted `grep` first** against wiki contents:
   - `File-based community: .*<name>` for files/pages/features
   - exact symbol/function name
   - exact source path fragment
3. Use `ls .code-review-graph/wiki/` only when the normalized wiki file name is obvious and you want to browse nearby matches.
4. Read the top 1-5 most relevant wiki files.
5. Follow the referenced source file paths and dependency sections only where needed.

## What to Prefer

Prefer wiki files that match, in this order:

1. Exact feature/file/function name
2. Exact app area (`apps/crm/...` vs `apps/myChip1/...`)
3. Closely related API/domain/community file
4. Dependency neighbors listed in **Outgoing** / **Incoming**

## Common Search Heuristics

- API questions → `grep` for the source path or service symbol, then prefer `api-*.md`
- Page/feature questions → `grep` `File-based community: .*<FeatureName>`
- Table/column questions → search `columns`, `table`, or the feature name
- Auth/session questions → search `auth`, `provider`, `refresh`, or exact auth component/hook names
- Unknown ownership → start from the closest matching wiki file, then inspect **Members**, **Incoming**, and **Outgoing**

## Practical Examples

- "How does AccountList work in CRM?"
  - search: `File-based community: .*AccountList`
  - read likely matches such as `accountlist-account.md`, `accountlist-query.md`, `accountlist-map.md`
- "How does myChip1 account API work?"
  - search: `src/api/account.ts` or `switchCurrentAccount`
  - read `api-account.md`
- "Explain auth layout in myChip1"
  - search: `AuthLayout.tsx`
  - read `auth-auth.md`

## Expected Agent Behavior

For repo-specific questions or implementation tasks:

- check the relevant wiki file(s) first
- answer from those targeted docs when possible
- open source files only for confirmation or implementation details
- avoid broad exploratory reads unless the wiki search fails

If a question is not repository-specific, no wiki lookup is required.
