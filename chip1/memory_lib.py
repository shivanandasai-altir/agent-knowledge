#!/usr/bin/env python3
"""
memory_lib.py — Memory journal library for chip1.

Two modes of operation (determined by first CLI argument):

╔══════════════════════════════════════════════════════════════════╗
║  MEMORY CRUD (default)                                         ║
║  Reads JSON from stdin, operates on MEMORY.md.                 ║
║    echo '{"action":"add",...}' | python3 memory_lib.py         ║
║    echo '{"action":"list"}'    | python3 memory_lib.py         ║
║                                                                ║
║  Actions: add, update, delete, list, get-fields                ║
╚══════════════════════════════════════════════════════════════════╝

╔══════════════════════════════════════════════════════════════════╗
║  PR FORMATTING (when first arg is a format command)            ║
║  Reads JSON from stdin, outputs formatted text.                ║
║    gh pr view 4099 --json files | python3 memory_lib.py files  ║
║    gh api /repos/.../comments  | python3 memory_lib.py comments║
║                                                                ║
║  Commands: metadata, files, body, comments                     ║
╚══════════════════════════════════════════════════════════════════╝
"""

import sys
import json
import re
from datetime import date as Date
from pathlib import Path

# ============================================================================
# MEMORY CRUD — parse, manipulate, and render MEMORY.md table format
# ============================================================================

# ── Helpers ────────────────────────────────────────────────────────────────


def esc(text: str) -> str:
    """Escape pipe characters for markdown tables."""
    if not text:
        return ""
    return text.replace("|", "\\|")


def split_table_row(row: str) -> list[str]:
    """Split a markdown table row into columns, respecting backtick boundaries."""
    row = row.strip().lstrip("|").rstrip("|")
    cols = []
    cur = ""
    in_bt = False
    for ch in row:
        if ch == "`":
            in_bt = not in_bt
            cur += ch
        elif ch == "|" and not in_bt:
            cols.append(cur.strip())
            cur = ""
        else:
            cur += ch
    if cur.strip():
        cols.append(cur.strip())
    return cols


# ── Parsing ────────────────────────────────────────────────────────────────


def parse_header(lines: list[str]) -> list[str]:
    """Extract header lines (before the first ## section heading)."""
    out = []
    for line in lines:
        if re.match(r"^##\s+(Entries|Active|Archived|Decisions)", line.strip()):
            break
        out.append(line)
    return out


def parse_entries(lines: list[str]) -> list[dict]:
    """Parse table rows into entry dicts.

    Each returned entry::
        {"date": str, "title": str, "fields": dict}
    """
    entries = []
    in_table = False
    for line in lines:
        s = line.strip()
        if s.startswith("|---"):
            in_table = True
            continue
        if in_table and s.startswith("|") and s.endswith("|"):
            cols = split_table_row(s)
            entry = _row_to_entry(cols)
            if entry:
                entries.append(entry)
        elif in_table and not s.startswith("|"):
            in_table = False
    return entries


def _row_to_entry(cols: list[str]) -> dict | None:
    """Convert table columns to an entry dict."""
    if len(cols) < 3:
        return None

    entry: dict = {"date": cols[0].strip(), "fields": {}}
    entry["title"] = re.sub(r"^\*\*|\*\*$", "", cols[1].strip())

    if len(cols) == 4:
        entry["fields"]["Status"] = "active"
        entry["fields"]["Author"] = cols[2].strip()
        _parse_details(cols[3], entry["fields"])
    elif len(cols) == 5:
        entry["fields"]["Status"] = "archived"
        entry["fields"]["Author"] = cols[2].strip()
        entry["fields"]["Archived by"] = cols[3].strip()
        _parse_details(cols[4], entry["fields"])
    else:
        return None

    return entry


def _parse_details(details: str, fields: dict) -> None:
    """Parse the Details column (<br>-separated) into fields."""
    for part in re.split(r"<br>", details):
        part = part.strip()
        if not part:
            continue

        m = re.match(r"<sup>Supersedes:\s*(.*?)</sup>", part)
        if m:
            fields["Supersedes"] = m.group(1).strip()
            continue

        m = re.match(r"<sup>Superseded by:\s*(.*?)</sup>", part)
        if m:
            fields["Superseded by"] = m.group(1).strip()
            continue

        m = re.match(r"\*\*Context:\*\*\s*(.*)", part)
        if m:
            fields["Context"] = m.group(1).strip()
            continue

        m = re.match(r"\*\*Pattern:\*\*\s*(.*)", part)
        if m:
            fields["Pattern"] = m.group(1).strip()
            continue

        m = re.match(r"<sup>Source:\s*`(.*?)`</sup>", part)
        if m:
            fields["Source files"] = m.group(1).strip()
            continue

        m = re.match(r"<sup>Docs:\s*(.*?)</sup>", part)
        if m:
            fields["Related docs"] = m.group(1).strip()
            continue

        m = re.match(r"<sup>Wiki:\s*(.*?)</sup>", part)
        if m:
            fields["Wiki files"] = m.group(1).strip()
            continue


# ── Rendering ──────────────────────────────────────────────────────────────


def format_details(entry: dict) -> str:
    """Build the Details column content for a table row."""
    f = entry["fields"]
    parts: list[str] = []

    if f.get("Supersedes"):
        parts.append(f"<sup>Supersedes: {esc(f['Supersedes'])}</sup>")
    if f.get("Superseded by"):
        parts.append(f"<sup>Superseded by: {esc(f['Superseded by'])}</sup>")
    if f.get("Context"):
        parts.append(f"**Context:** {esc(f['Context'])}")
    if f.get("Pattern"):
        parts.append(f"**Pattern:** {esc(f['Pattern'])}")
    if f.get("Source files"):
        parts.append(f"<sup>Source: `{esc(f['Source files'])}`</sup>")
    if f.get("Related docs"):
        parts.append(f"<sup>Docs: {esc(f['Related docs'])}</sup>")
    if f.get("Wiki files"):
        parts.append(f"<sup>Wiki: {esc(f['Wiki files'])}</sup>")

    return "<br>".join(parts)


def render_file(header: list[str], entries: list[dict]) -> str:
    """Render the full MEMORY.md content as two tables."""
    lines = list(header)
    if lines and lines[-1].strip():
        lines.append("")

    active = [e for e in entries if e["fields"].get("Status", "active") != "archived"]
    archived = [e for e in entries if e["fields"].get("Status") == "archived"]

    # Active table
    lines.append("## Active Decisions")
    lines.append("")
    lines.append("| Date | Title | Author | Details |")
    lines.append("|------|-------|--------|---------|")
    for e in active:
        lines.append(
            f"| {e['date']} | **{esc(e['title'])}** | {esc(e['fields'].get('Author', ''))} | {format_details(e)} |"
        )

    if archived:
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## Archived Decisions")
        lines.append("")
        lines.append("| Date | Title | Author | Archived by | Details |")
        lines.append("|------|-------|--------|-------------|---------|")
        for e in archived:
            lines.append(
                f"| {e['date']} | **{esc(e['title'])}** | {esc(e['fields'].get('Author', ''))} | {esc(e['fields'].get('Archived by', ''))} | {format_details(e)} |"
            )

    lines.append("")
    return "\n".join(lines)


# ── Entry helpers ─────────────────────────────────────────────────────────


def find_active(entries: list[dict], title: str) -> tuple[int | None, dict | None]:
    """Find an active entry by exact title match."""
    for i, e in enumerate(entries):
        if e["title"] == title and e["fields"].get("Status") == "active":
            return i, e
    return None, None


def handle_supersede(entries: list[dict], old_title: str, new_title: str) -> bool:
    """Mark *old_title* as superseded by *new_title*."""
    for e in entries:
        if e["title"] == old_title and e["fields"].get("Status") == "active":
            e["fields"]["Status"] = "superseded"
            e["fields"]["Superseded by"] = new_title
            return True
    return False


# ── CRUD Actions ───────────────────────────────────────────────────────────


def _read_entries(filepath: str) -> tuple[list[str], list[dict]]:
    """Read and parse MEMORY.md, returning (header, entries)."""
    fp = Path(filepath)
    lines = fp.read_text(encoding="utf-8").split("\n")
    return parse_header(lines), parse_entries(lines)


def _write_entries(filepath: str, header: list[str], entries: list[dict]) -> None:
    """Render and write entries to MEMORY.md."""
    Path(filepath).write_text(render_file(header, entries), encoding="utf-8")


def action_add(data: dict) -> int:
    fp = data["filepath"]
    title = data.get("title", "").strip()
    if not title:
        print("ERROR: title is required", file=sys.stderr)
        return 1

    context = data.get("context", "")
    pattern = data.get("pattern", "")
    supersedes = data.get("supersedes", "").strip()
    author = data.get("author", "")
    today = data.get("today", "")
    wiki_files = data.get("wikiFiles", [])
    source_files = data.get("sourceFiles", [])
    related_docs = data.get("relatedDocs", [])

    header, entries = _read_entries(fp)

    # Check for existing active entry with same title
    idx, existing = find_active(entries, title)
    if existing is not None:
        existing_pattern = existing["fields"].get("Pattern", "")
        if existing_pattern == pattern:
            print(f'NOOP: Entry "{title}" already exists with same pattern.')
            return 0
        if context:
            existing["fields"]["Context"] = context
        if pattern:
            existing["fields"]["Pattern"] = pattern
        if author:
            existing["fields"]["Author"] = author
        _write_entries(fp, header, entries)
        print(f'UPDATED: "{title}" (same title, pattern refined).')
        return 0

    # Handle supersede chain
    if supersedes:
        handle_supersede(entries, supersedes, title)

    # Build new entry
    entry: dict = {
        "date": today,
        "title": title,
        "fields": {"Status": "active", "Context": context, "Pattern": pattern},
    }
    if author:
        entry["fields"]["Author"] = author
    if wiki_files:
        entry["fields"]["Wiki files"] = ", ".join(wiki_files) if isinstance(wiki_files, list) else str(wiki_files)
    if source_files:
        entry["fields"]["Source files"] = ", ".join(source_files) if isinstance(source_files, list) else str(source_files)
    if related_docs:
        entry["fields"]["Related docs"] = ", ".join(related_docs) if isinstance(related_docs, list) else str(related_docs)
    if supersedes:
        entry["fields"]["Supersedes"] = supersedes

    entries.insert(0, entry)
    _write_entries(fp, header, entries)

    msg = f'ADDED: "{title}"'
    if supersedes:
        msg += f' (supersedes "{supersedes}")'
    print(msg)
    return 0


def action_update(data: dict) -> int:
    fp = data["filepath"]
    title = data.get("title", "").strip()
    context = data.get("context", "")
    pattern = data.get("pattern", "")
    author = data.get("author", "")

    header, entries = _read_entries(fp)

    found = False
    for e in entries:
        if e["title"] == title:
            if context:
                e["fields"]["Context"] = context
                found = True
            if pattern:
                e["fields"]["Pattern"] = pattern
                found = True
            if author:
                e["fields"]["Author"] = author
                found = True

    if found:
        _write_entries(fp, header, entries)
        print(f'UPDATED: "{title}".')
    else:
        print(f'ERROR: Entry "{title}" not found.', file=sys.stderr)
        return 1
    return 0


def action_delete(data: dict) -> int:
    fp = data["filepath"]
    title = data.get("title", "").strip()
    author = data.get("author", "")

    header, entries = _read_entries(fp)

    found = False
    for e in entries:
        if e["title"] == title:
            e["fields"]["Status"] = "archived"
            if author:
                e["fields"]["Archived by"] = author
            found = True
            break

    if found:
        _write_entries(fp, header, entries)
        print(f'ARCHIVED: "{title}". Entry kept in journal for history.')
    else:
        print(f'ERROR: Entry "{title}" not found.', file=sys.stderr)
        return 1
    return 0


def action_list(data: dict) -> int:
    _, entries = _read_entries(data["filepath"])

    active = [(e["title"], e["date"]) for e in entries if e["fields"].get("Status", "active") == "active"]
    superseded = [(e["title"], e["date"]) for e in entries if e["fields"].get("Status") == "superseded"]
    archived = [(e["title"], e["date"]) for e in entries if e["fields"].get("Status") == "archived"]

    print(f"## Active Entries ({len(active)})")
    for t, d in active:
        print(f"  [{d}] {t}")
    print()
    print(f"## Superseded/Suppressed ({len(superseded)})")
    for t, d in superseded:
        print(f"  [{d}] {t}")
    print()
    print(f"## Archived ({len(archived)})")
    for t, d in archived:
        print(f"  [{d}] {t}")
    return 0


def action_get_fields(data: dict) -> int:
    """Extract action/title/author from JSON — replaces `jq` in shell scripts.

    Outputs tab-separated values for easy parsing: action\ttitle\tauthor
    """
    action = data.get("action", "")
    title = data.get("title", "")
    author = data.get("author", "")
    # Use \x1f (unit separator) as delimiter — safe for any text content
    print(f"{action}\x1f{title}\x1f{author}")
    return 0


MEMORY_ACTIONS = {
    "add": action_add,
    "update": action_update,
    "delete": action_delete,
    "list": action_list,
    "get-fields": action_get_fields,
}


def run_memory_crud(data: dict) -> int:
    """Dispatch a memory CRUD operation."""
    action = data.get("action", "")
    handler = MEMORY_ACTIONS.get(action)
    if not handler:
        print(f'ERROR: Unknown action "{action}"', file=sys.stderr)
        return 1
    return handler(data)


# ============================================================================
# PR FORMATTING — format GitHub API output for human reading
# ============================================================================


def pr_metadata(data: dict) -> str:
    """Format PR metadata as-is (JSON dump)."""
    return json.dumps(data, indent=2)


def pr_files(data: dict) -> str:
    """Format PR files list as human-readable lines."""
    out = []
    for f in data.get("files", []):
        out.append(f"  {f['path']}  (+{f['additions']}/-{f['deletions']})")
    return "\n".join(out) if out else "  (none)"


def pr_body(data: dict) -> str:
    """Format PR description, stripping images and truncating."""
    body = data.get("body", "") or ""
    body = re.sub(r"!\[.*?\]\(.*?\)", "[image]", body)
    body = re.sub(r"<img[^>]*>", "[image]", body)
    if len(body) > 3000:
        body = body[:3000] + "\n...(truncated)"
    return body or "  (empty)"


def pr_comments(data: list | dict) -> str:
    """Format PR review or conversation comments."""
    if not isinstance(data, list):
        return "  (unexpected format)"
    if not data:
        return "  (none)"
    out = []
    for c in data:
        user = c.get("user", {}).get("login", "?")
        body = c.get("body", "") or ""
        body = " ".join(body.split())
        if len(body) > 500:
            body = body[:500] + "...(truncated)"
        out.append(f"  [{user}] {body}")
    return "\n".join(out)


PR_FORMATTERS = {
    "metadata": pr_metadata,
    "files": pr_files,
    "body": pr_body,
    "comments": pr_comments,
}


def run_pr_format(args: list[str]) -> int:
    """Format PR JSON from stdin using the named formatter."""
    if not args:
        print("ERROR: format command required (metadata|files|body|comments)", file=sys.stderr)
        return 1

    cmd = args[0]
    handler = PR_FORMATTERS.get(cmd)
    if not handler:
        print(f"ERROR: Unknown format command '{cmd}'", file=sys.stderr)
        return 1

    raw = sys.stdin.read().strip()
    if not raw:
        print("  (no data)")
        return 0

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        print("  (parse error)")
        return 0

    print(handler(data))
    return 0


# ============================================================================
# Main dispatch
# ============================================================================


def main() -> int:
    # If first CLI arg matches a PR format command, run that
    if len(sys.argv) > 1 and sys.argv[1] in PR_FORMATTERS:
        return run_pr_format(sys.argv[1:])

    # Otherwise, run memory CRUD from stdin JSON
    raw = sys.stdin.read().strip()
    if not raw:
        print("ERROR: no input", file=sys.stderr)
        return 1

    data = json.loads(raw)
    action = data.get("action", "")

    # Shortcut: get-fields doesn't need filepath/today
    if action == "get-fields":
        return action_get_fields(data)

    # Inject context for CRUD actions
    script_dir = Path(__file__).resolve().parent
    data["filepath"] = str(script_dir / "MEMORY.md")
    data["today"] = Date.today().strftime("%Y-%m-%d")

    return run_memory_crud(data)


if __name__ == "__main__":
    sys.exit(main())
