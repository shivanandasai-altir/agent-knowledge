# Selection-Dependent Actions — Use SelectionActionBar, Not FAB

**Trigger:** Read this file when adding or modifying an entity FAB action whose visibility or enabled-state depends on table row selection, or when a FAB checks `useLocation()` / pathname to decide which actions to show on a given tab.

---

## TL;DR

If a bulk action operates on table row selection, render it in a `<SelectionActionBar />` (table footer overlay) — **not** as a FAB item. If a FAB action is only valid on a specific tab, move it into that tab — don't gate it on `useLocation()`.

Canonical reference: PR #3959 (`Tasks list - Move multi-select actions from fab to footer`) — see `apps/crm/src/pages/Inner/Tasks/TasksActionBar.tsx`.

---

## Why not FAB items?

Selection-dependent actions in the FAB have known UX problems:

- **Discoverability.** The user selects rows, but the relevant action is hidden behind a closed FAB menu. They don't know it appeared.
- **Disabled-state confusion.** The FAB item is visible-but-disabled when nothing is selected. The relationship between "select a row" and "this menu item becomes clickable" is not obvious.
- **Cross-tab leakage.** A FAB item that only makes sense on the Lines tab still appears (disabled) on every other tab of the same entity.

The action bar fixes all three: it fades in over the table footer exactly when selection exists, right next to the rows the user just clicked.

---

## The pattern

1. **Selection store** (Zustand) holds `rowSelection: RowSelectionState`, the resolved `selectedX[]`, and a `clearSelection()` that resets both. Provider lives in `features/<EntityList>/`.
2. **Selection provider** exposes the store via `createZustandContext`. Export the hook as `export const useXSelectionContext = useZustandStore;` (not `() => useZustandStore()`) so consumers can pass selectors and avoid whole-state re-renders.
3. **`<XActionBar />`** component reads selection via selectors, renders `<SelectionActionBar count={...} onClear={clearSelection} actions={[...]} />`. Returns `null` early when there are no actions to show (e.g. behind a feature flag).
4. **List/ListView** accepts a `selectionFooter?: ReactNode` prop and renders it as a sibling of the count typography inside the existing `<TableFooter>`. The bar is `position: absolute; inset: 0` and overlays the footer.
5. **Tab/page** mounts `<XActionBar />` via `selectionFooter={...}`. The selection provider stays at the page level so other consumers (FAB, list) still see the same selection.

```tsx
// In the tab that owns the table
<EntityListView
  selectionFooter={<EntityLinesActionBar entity={entity} />}
  // ...
/>
```

The bar overlays the footer when `count > 0` and fades out when cleared. No layout shift.

---

## ❌ Don't gate FAB actions on `pathname`

If a FAB action is only valid on one tab, don't write this:

```tsx
const { pathname } = useLocation();
const isLinesTabActive = pathname.endsWith(`/${ETab.Lines}`);
// ...
{isLinesTabActive && <FabActionItem onClick={...}>Bulk Update</FabActionItem>}
```

Move the action into the tab itself. Tab-specific actions belong to the tab, not to the entity-level FAB. The pathname check is a smell that says "this action doesn't actually belong here."

If the action is selection-dependent, render it via `<SelectionActionBar />` (see above). If it's selection-independent but tab-specific (e.g. an "Add Line" button at the top of the Lines tab), render it inside the tab's `<TabIsland>` or wherever the tab's controls live.

---

## Recipe (proven on Invoices, Tasks, PurchaseOrder Lines)

1. Identify selection-dependent items in the FAB. If the FAB becomes empty after removing them, delete the FAB.
2. Make sure the selection store has `clearSelection()` that resets `rowSelection` and the derived `selected<Entity>[]`.
3. If needed, switch the selection-context export to `useZustandStore` directly so the action bar can use selectors.
4. Create `<Entity>ActionBar.tsx`. Read selection via selectors, render `<SelectionActionBar>` with the actions. Return `null` if no actions are available.
5. Add `selectionFooter?: ReactNode` to the list view and list component. Render it inside the existing `<TableFooter>` next to the row-count typography.
6. Mount `<Entity>ActionBar />` from the tab via the `selectionFooter` prop.
7. Remove the migrated items (and any `useLocation`/pathname gating) from the FAB. Clean up unused imports.
8. `pnpm check:typescript`.

## Related
- [Architecture Patterns](architecture-patterns.md) — Zustand context pattern (`createZustandContext`) for selection stores

---

## Multi-entity backend constraint

The PDF export endpoint rejects multi-entity calls with `400 "Can't process multiple entities or lines/items from multiple entities"`. This applies to **all** generate-PDF actions (Invoice PDF, CRR, Packing Slip). If a candidate action hits this endpoint, either omit it from the action bar or disable it with `tooltipWhenDisabled` when more than one row is selected.
