# Architecture Patterns Reference

**Trigger:** Read this file before writing a PATCH mutation, API service factory, infinite query, column reordering feature, Zustand context store, or displaying user/contact names.

## Minimal PATCH Payloads with `createDiff`

When sending PATCH requests, use `createDiff` from `@chip1/utils/helpers/diffPatch` to send only changed fields. This prevents the backend from running validations on unrelated field groups.

```typescript
import { createDiff } from '@chip1/utils/helpers/diffPatch';

const diff = createDiff(originalAccount, updatedFields);
// { changed: { phone: '...' }, unset: ['parentAccount'] }

if (Object.keys(diff.changed).length === 0 && !diff.unset?.length) {
  return; // nothing changed — skip the mutation entirely
}

await mutateAsync({ ...diff.changed, ...(diff.unset?.length ? { unset: diff.unset } : {}) });
```

Key behaviors:

- Only keys present in `updated` are compared (PATCH semantics — absent keys are ignored)
- `null`, `undefined`, `''` → field goes to `unset` array (backend clears the field)
- Nested objects are compared atomically — any sub-field change includes the whole nested object
- `normalizeLookups: true` (default) — lookups with matching `key` are treated as equal even if other fields differ
- **Write-only fields** (`timelineNote`, `reason`): not returned by the server — always pass them outside the diff: `{ ...diff.changed, ...(reason ? { reason } : {}) }`
- **`unset` convention field**: some form islands pass an `unset` key alongside form data to explicitly clear fields; strip it before diffing and merge with `diff.unset`

**`createItemDiff`**: same as `createDiff` but preserves `id` — use for items in collections (e.g., order lines, contacts).

Reference: `buildAccountPatchPayload` in `apps/crm/src/features/AccountDetails/AccountDetailsTab/AccountDetailsIsland.tsx`

## Zustand Context Pattern

Use `createZustandContext` from `@chip1/utils/zustandContext` to create context-based Zustand stores:

```typescript
export const {
  ZustandProvider: MyStoreProvider,
  useZustandStore: useMyStore,
  useZustandStoreContext: useMyStoreContext,
} = createZustandContext<TMyStore>();

<MyStoreProvider createStore={() => createMyStore()} dependencies={[dep1, dep2]}>
  {children}
</MyStoreProvider>

const value = useMyStore((state) => state.value); // Hook with selector
const store = useMyStoreContext(); // Direct store access for subscriptions
```

- `ZustandProvider` accepts `createStore` function and optional `dependencies` array
- Store is created once and recreated when dependencies change
- `useZustandStore` for selecting state with selectors
- `useZustandStoreContext` for direct store access (e.g., subscriptions)

## Sorting Pattern with Zustand

Use `bindSortProvider<TSortEnum>(storageKey, defaultSort)` for persistent sorting. Use specific storage keys: `'orders'`, `'accounts'`, `'contacts'`, `'tasks'`, `'partActivity'`, `'parts'`. When different APIs serve similar data, use separate sort providers with different keys.

## Column Reordering Pattern

Use TanStack Table's `state.columnOrder` with `useColumnOrder()` hook from `@chip1/core/features/table/columnsMenu/ColumnVisibilityProvider`. All columns need explicit `id` properties. Define `PINNED_COLUMNS` and `ALL_PINNED_COLUMNS` in the columns definition file. Use `ColumnsMenuWithReorderingTrigger` with `pinnedColumns={ALL_PINNED_COLUMNS}`. Reference: `apps/crm/src/pages/Inner/AccountList/Components/`.

## Shared API Service Factory Pattern

When an API domain must be used by more than one app, implement it as a factory in `packages/core/api/<domain>.ts`. The factory accepts `{ privateInterceptors, handleErrorInterceptor }` and returns bound service methods. Each app instantiates the factory in `apps/<app>/src/api/<domain>.ts` and re-exports only the methods it needs (MC1 exposes only read operations; CRM exposes all). Reference implementations: `packages/core/api/stock.ts` and `packages/core/api/orders.ts`. Do NOT add cross-app API logic directly to an app's `src/api/` — extract it to `@chip1/core` first.

## Shared Infinite Query Factory Pattern

When an infinite-scroll list query must work across apps with different service instances, wrap it in a factory exported from `@chip1/core/features/<domain>/`. The factory accepts the bound API function and returns `{ <domain>ListInfiniteQueryOptions }`. Apps call the factory at module level with their own service function. Export `<DOMAIN>_LIST_BASE_KEY` from the same file for cache invalidation. Reference: `packages/core/features/stock/stockListQuery.ts`.

**`@tanstack/query/exhaustive-deps` suppression for factory-closure bindings:** When a query's `queryFn` receives its API function via a factory-closure, suppress with an inline comment: `// eslint-disable-next-line @tanstack/query/exhaustive-deps -- getStockDetails is a stable factory-closure binding; all variable params are captured in queryKey`. Never suppress without this comment.

## Transactional Shared Types

Common shapes for users, contacts, and part attributes that appear on transactional documents live in `packages/core/types/transactional.ts`: `TTransactionalAccountUser<R>`, `TTransactionalAccountContact`, `TCommonPartAttributes`. Do not re-declare these in app-level `types/common.ts` — import from `@chip1/core/types/transactional`.

## Utility Helpers

**Prefer existing helper functions over inline patterns.** When a utility exists for a common operation, use it instead of reimplementing logic inline.

### `getFullName`

Use `getFullName` from `@chip1/utils/helpers/getFullName` to combine `firstName` and `lastName`. Handles null/undefined and whitespace sanitization automatically.

```typescript
import { getFullName } from '@chip1/utils/helpers/getFullName';

// ❌ Don't concatenate manually
const name = joinWith([contact.firstName, contact.lastName], ' ');
const name = contact.firstName + ' ' + contact.lastName;

// ✅ Use getFullName
const name = getFullName(contact);
```

Returns `null` when both fields are undefined/null — always provide a fallback:

```typescript
const name = getFullName(contact) || dash;
const name = getFullName(user) || user.name || dash;
```

- Use `getFullName(contact)` when you have a `{ firstName, lastName }` object
- Use `contact.name` when the name is already available as a single property

## Related
- [Formik Patterns](formik-patterns.md) — PATCH diffs for form submissions, `ensureSafeQueryData`
- [Filter System](filter-system.md) — Zustand context stores for filter state
- [Simple Cells](simple-cells.md) — column reordering and TanStack table patterns
- [Selection Action Bar](selection-action-bar.md) — Zustand context pattern for action bars
- [Code Redundancy](code-redundancy.md) — VM transformation functions, helper function usage
- [Table Loading Patterns](table-loading-patterns.md) — shared infinite query factory for list tables
