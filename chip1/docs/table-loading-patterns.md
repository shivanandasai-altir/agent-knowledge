# Table Loading Patterns

**Trigger:** Read this file before creating a new list/table component, or when changing the initial loading UX for a TanStack table that uses `TableCommunication` / `InfiniteTableCommunication`.

## Default Rule

New list/table screens should show a table skeleton on the **initial load**.

- Use `MuiTableSkeleton` from `@chip1/components/skeletons/primitives`
- For grouped sourcing-style tables, use `MuiGroupedTableSkeleton` when the grouped layout is enabled
- Compute a boolean with `useShouldShowInitialTableSkeleton(query)` from `@chip1/components/table/useShouldShowInitialTableSkeleton`
- Do **not** replace already-rendered data with the full skeleton during refetches / filter changes / next-page loading

## Standard Pattern

```tsx
import { MuiTableSkeleton } from '@chip1/components/skeletons/primitives';
import { useShouldShowInitialTableSkeleton } from '@chip1/components/table/useShouldShowInitialTableSkeleton';

const shouldShowInitialTableSkeleton = useShouldShowInitialTableSkeleton(query);

if (shouldShowInitialTableSkeleton) {
  return <MuiTableSkeleton />;
}

return (
  <TableViewport>
    <ResizableTableContainer reactTable={table}>
      <BasicReactTable reactTable={table} />
    </ResizableTableContainer>
    <InfiniteTableCommunication
      query={query}
      length={query.data?.totalCount}
      emptyMessage={<EmptyMessage />}
    />
  </TableViewport>
);
```

## Grouped Table Pattern

```tsx
import { MuiGroupedTableSkeleton, MuiTableSkeleton } from '@chip1/components/skeletons/primitives';
import { useShouldShowInitialTableSkeleton } from '@chip1/components/table/useShouldShowInitialTableSkeleton';

const shouldShowInitialTableSkeleton = useShouldShowInitialTableSkeleton(query);

if (shouldShowInitialTableSkeleton) {
  return groupByEntity ? <MuiGroupedTableSkeleton /> : <MuiTableSkeleton />;
}
```

## When to Use This Hook vs Route-Level Suspense

If the list screen has a **route-level loader**, prefer `DataRouterTableSuspense` from `@chip1/core/features/routes/nonBlockingRouteLoader` so the request starts in the loader and the skeleton is shown via Suspense:

```tsx
import { DataRouterTableSuspense } from '@chip1/core/features/routes/nonBlockingRouteLoader';
import { myListLoader } from './myListLoader';

// In page component:
<DataRouterTableSuspense select={myListLoader.selectors.promise}>
  <MyListTable />
</DataRouterTableSuspense>;
```

**Use `useShouldShowInitialTableSkeleton`** only for tables that live under:

- Tabs (e.g. `AllActivityTableTab`, `CustomerRmaSelectLines`)
- Modals
- Filter-driven sub-views
- Pages **without** a route loader / `DataRouterTableSuspense`

If the page already has a blocking route loader that calls `ensureInfiniteQueryData` but no `DataRouterTableSuspense` wrapper, consider converting to a non-blocking loader + `DataRouterTableSuspense` to show a skeleton during load.

## Placement Rules

- Keep persistent chrome like filters, tabs, or surrounding cards visible when that matches the existing screen structure
- Keep empty/error messaging in `TableCommunication` / `InfiniteTableCommunication`; the skeleton only covers the initial loading state
- Prefer an early return for full-screen table views
- If the table lives inside a larger layout/card, render the skeleton only in the table content area

## References

- `apps/crm/src/features/OrdersList/components/OrdersList.tsx`
- `apps/crm/src/features/CampaignDetails/CampaignContactsTable.tsx`
- `apps/crm/src/features/SourcingStock/StockList.tsx`
- `packages/components/skeletons/primitives.tsx`

## Related
- [Simple Cells](simple-cells.md) — both about TanStack table patterns
- [MCP Tools](mcp-tools.md) — graph tools useful for tracing table component dependencies
