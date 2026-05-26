# MCP Tools: code-review-graph

**Trigger:** Read this file when using MCP graph tools for architecture questions, impact analysis, or code review.

**Note:** These tools require the MCP server to be running. Fall back to Grep/Glob/Read whenever the server is unavailable.

## When to Prefer Graph Tools

- **Exploring code**: `semantic_search_nodes` or `query_graph` for structural context (callers, dependents) that Grep cannot easily provide
- **Understanding impact**: `get_impact_radius` instead of manually tracing imports
- **Code review**: `detect_changes` + `get_review_context` for risk-scored analysis and token-efficient context
- **Finding relationships**: `query_graph` with callers_of/callees_of/imports_of/tests_for
- **Architecture questions**: `get_architecture_overview` + `list_communities`

For simple targeted lookups (finding a specific file or function by exact name), standard Grep/Glob/Read tools are faster and always available.

## Key Tools

| Tool                        | Use when                                               |
| --------------------------- | ------------------------------------------------------ |
| `detect_changes`            | Reviewing code changes — gives risk-scored analysis    |
| `get_review_context`        | Need source snippets for review — token-efficient      |
| `get_impact_radius`         | Understanding blast radius of a change                 |
| `get_affected_flows`        | Finding which execution paths are impacted             |
| `query_graph`               | Tracing callers, callees, imports, tests, dependencies |
| `semantic_search_nodes`     | Finding functions/classes by name or keyword           |
| `get_architecture_overview` | Understanding high-level codebase structure            |
| `refactor_tool`             | Planning renames, finding dead code                    |

## Workflow

1. The graph auto-updates on file changes (via hooks)
2. Use `detect_changes` for code review
3. Use `get_affected_flows` to understand impact
4. Use `query_graph` pattern="tests_for" to check coverage

## Related
- [Wiki Reference](wiki-reference.md) — both serve as codebase navigation aids; prefer wiki for first-stop search, graph for deep traversal
- [Table Loading Patterns](table-loading-patterns.md) — graph tools useful for tracing table component dependencies
