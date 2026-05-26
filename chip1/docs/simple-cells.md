# Simple Cells — Table Cell Shortcuts

**Trigger:** Read this file when writing or modifying TanStack table column definitions (`columnsDefs.tsx`, `*Columns.tsx`) or any file under `packages/components/table/`.

---

## TL;DR

For plain data cells in TanStack column definitions, use `getSimpleCells<TRow>()` shortcuts instead of writing raw `TableCell` / `SingleLineCell` manually. These shortcuts wire up `cssVarId`, the dash fallback, and correct flex layout automatically.

---

## How to instantiate

```typescript
import { getSimpleCells } from '@chip1/components/table/getSimpleCells';

const simpleCells = getSimpleCells<TMyRowType>();
```

Declare at module scope alongside `columnHelper` — one per row type per file.

---

## Available shortcuts

| Shortcut                                    | Use when                                                                                                                   |
| ------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| `simpleCells.singleLine`                    | Plain text, left-aligned. Covers most data cells.                                                                          |
| `simpleCells.singleLineWithCopy`            | Text with a hover copy button. Value type: `string \| null \| undefined`.                                                  |
| `simpleCells.singleLineFormatted(fn)`       | Text with a value formatter (e.g. `formatDate`, `formatCurrency`). Curried — `cell` maps to type `V \| null \| undefined`. |
| `simpleCells.singleLineRight`               | Plain text, right-aligned. For numeric/currency values.                                                                    |
| `simpleCells.singleLineCenter`              | Plain text, center-aligned.                                                                                                |
| `simpleCells.singleLineRightFormatted(fn)`  | Right-aligned with formatter. Curried.                                                                                     |
| `simpleCells.singleLineCenterFormatted(fn)` | Center-aligned with formatter. Curried.                                                                                    |
| `simpleCells.link`                          | External link (opens new tab). Value: `string URL` or `{ href, label? }`.                                                  |
| `simpleCells.linkWithCopy`                  | External link + hover copy of the href. Same value type as `link`.                                                         |
| `simpleCells.routerLink`                    | Internal React Router link. Value: `{ to: To, label? }`.                                                                   |

All shortcuts:

- set `cssVarId={cell.column.id}` automatically (required for column resizing)
- fall back to `dash` when the value is null/undefined
- apply the correct flex container via `SingleLineCell`

---

## Usage examples

```typescript
// Simple text
columnHelper.accessor('partNumber', {
  cell: simpleCells.singleLine,
  ...
});

// Copy button
columnHelper.accessor('xCrmId', {
  cell: simpleCells.singleLineWithCopy,
  ...
});

// Formatted date (right-aligned)
columnHelper.accessor('createdAt', {
  cell: simpleCells.singleLineRightFormatted((v) => formatDate(v, DATE_FORMAT)),
  ...
});

// Internal router link
columnHelper.accessor('orderId', {
  cell: simpleCells.routerLink,
  // supply value as: { to: generatePath(...), label: order.orderNumber }
  ...
});
```

---

## Header / container cell style

Use `getColumnStyle` (not `getCellStyle` with manual width) for the `style` prop on `<TableCell>` containers:

```typescript
import { getColumnStyle } from '@chip1/components/table/getCellStyle';

// ✅
<TableCell style={getColumnStyle(column)}>...</TableCell>

// ❌ — don't pass a raw pixel width
<TableCell style={{ width: 120, minWidth: 120, maxWidth: 120 }}>...</TableCell>
```

---

## Multi-element custom cells — use `CellWrapper`

When a cell contains more than one element (e.g. text + icon + tooltip) and you are **not** using a `simpleCells` shortcut, wrap the content in `CellWrapper` instead of a custom `Box`/`div` to get consistent flex layout:

```typescript
import { CellWrapper } from '@chip1/components/table/CellWrapper';

<SingleLineCell cssVarId={cell.column.id}>
  <CellWrapper>
    <span>{value}</span>
    <LockIcon fontSize="small" />
  </CellWrapper>
</SingleLineCell>
```

---

## What NOT to do

```typescript
// ❌ Manual dash fallback — simpleCells handles this
<SingleLineCell cssVarId={cell.column.id}>{value || dash}</SingleLineCell>

// ❌ Hardcoded width in cell style — breaks column resizing
<TableCell style={{ width: 150 }}>...</TableCell>

// ❌ Missing cssVarId — column won't resize correctly
<SingleLineCell>{value}</SingleLineCell>

// ❌ Raw div wrapper instead of CellWrapper
<div style={{ display: 'flex', gap: 4 }}>...</div>
```

## Related
- [Architecture Patterns](architecture-patterns.md) — column reordering pattern with `useColumnOrder()`
- [Table Loading Patterns](table-loading-patterns.md) — TanStack table initial loading UX
