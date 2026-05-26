#!/usr/bin/env python3
"""
memory_lib.py — Parse, manipulate, and render the chip1 MEMORY.md table format.

Reads JSON from stdin with action + fields, operates on MEMORY.md in the same
directory, and writes back in the two-table format (Active / Archived).

Usage (called from update-memory.sh):
  echo '{"action":"add","title":"...","author":"...","context":"...","pattern":"..."}' \\
    | python3 path/to/memory_lib.py
"""

import sys
import json
import re
from datetime import date as Date
from pathlib import Path


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

    # Title (strip **bold** markers)
    entry["title"] = re.sub(r"^\*\*|\*\*$", "", cols[1].strip())

    if len(cols) == 4:
        # Active table: date | title | author | details
        entry["fields"]["Status"] = "active"
        entry["fields"]["Author"] = cols[2].strip()
        _parse_details(cols[3], entry["fields"])
    elif len(cols) == 5:
        # Archived table: date | title | author | archived_by | details
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

    # Ensure header ends with blank line
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


# ── Actions ────────────────────────────────────────────────────────────────

def action_add(data: dict) -> int:
    fp = Path(data["filepath"])
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

    lines = fp.read_text(encoding="utf-8").split("\n")
    header = parse_header(lines)
    entries = parse_entries(lines)

    # Check for existing active entry with same title
    idx, existing = find_active(entries, title)
    if existing is not None:
        existing_pattern = existing["fields"].get("Pattern", "")
        if existing_pattern == pattern:
            print(f'NOOP: Entry "{title}" already exists with same pattern.')
            return 0
        # Update in place
        if context:
            existing["fields"]["Context"] = context
        if pattern:
            existing["fields"]["Pattern"] = pattern
        if author:
            existing["fields"]["Author"] = author
        fp.write_text(render_file(header, entries), encoding="utf-8")
        print(f'UPDATED: "{title}" (same title, pattern refined).')
        return 0

    # Handle supersede chain
    if supersedes:
        handle_supersede(entries, supersedes, title)

    # Build new entry
    entry: dict = {
        "date": today,
        "title": title,
        "fields": {
            "Status": "active",
            "Context": context,
            "Pattern": pattern,
        },
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
    fp.write_text(render_file(header, entries), encoding="utf-8")

    msg = f'ADDED: "{title}"'
    if supersedes:
        msg += f' (supersedes "{supersedes}")'
    print(msg)
    return 0


def action_update(data: dict) -> int:
    fp = Path(data["filepath"])
    title = data.get("title", "").strip()
    context = data.get("context", "")
    pattern = data.get("pattern", "")
    author = data.get("author", "")

    lines = fp.read_text(encoding="utf-8").split("\n")
    header = parse_header(lines)
    entries = parse_entries(lines)

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
        fp.write_text(render_file(header, entries), encoding="utf-8")
        print(f'UPDATED: "{title}".')
    else:
        print(f'ERROR: Entry "{title}" not found.', file=sys.stderr)
        return 1
    return 0


def action_delete(data: dict) -> int:
    fp = Path(data["filepath"])
    title = data.get("title", "").strip()
    author = data.get("author", "")

    lines = fp.read_text(encoding="utf-8").split("\n")
    header = parse_header(lines)
    entries = parse_entries(lines)

    found = False
    for e in entries:
        if e["title"] == title:
            e["fields"]["Status"] = "archived"
            if author:
                e["fields"]["Archived by"] = author
            found = True
            break

    if found:
        fp.write_text(render_file(header, entries), encoding="utf-8")
        print(f'ARCHIVED: "{title}". Entry kept in journal for history.')
    else:
        print(f'ERROR: Entry "{title}" not found.', file=sys.stderr)
        return 1
    return 0


def action_list(data: dict) -> int:
    fp = Path(data["filepath"])
    lines = fp.read_text(encoding="utf-8").split("\n")
    entries = parse_entries(lines)

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


# ── Dispatch ───────────────────────────────────────────────────────────────

ACTIONS = {
    "add": action_add,
    "update": action_update,
    "delete": action_delete,
    "list": action_list,
}


def main() -> int:
    raw = sys.stdin.read()
    if not raw.strip():
        print("ERROR: no input", file=sys.stderr)
        return 1

    data = json.loads(raw)
    action = data.get("action", "")
    handler = ACTIONS.get(action)
    if not handler:
        print(f'ERROR: Unknown action "{action}"', file=sys.stderr)
        return 1

    # Resolve filepath relative to this script
    script_dir = Path(__file__).resolve().parent
    data["filepath"] = str(script_dir / "MEMORY.md")
    data["today"] = Date.today().strftime("%Y-%m-%d")

    return handler(data)


if __name__ == "__main__":
    sys.exit(main())
