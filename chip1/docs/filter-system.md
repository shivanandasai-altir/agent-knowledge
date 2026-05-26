# Filter System Reference

**Trigger:** Read this file before modifying any file under `apps/crm/src/features/filters/` or when implementing new filters anywhere in the CRM.

## Core Components

`GenericFiltersModal`, `FiltersModal` (shared in `core/`), `useFilters` hook, `createFilterConfig`, `createFilterBarWrapper` factory.

## FilterBarWrapper Factory Pattern

Use `createFilterBarWrapper(useFilterHook)` at module level to create wrapper components with stable hook references. Never create wrappers during render. For dynamic hook arguments (e.g., view-dependent filters), create separate hook wrappers with stable references for each variant.

## Modal Integration

- All filter modals use the shared `FiltersModal` from `apps/crm/src/features/filters/core/FiltersModal.tsx`
- The modal is registered in `apps/crm/src/config/modals.ts` with key `'filters.modal'`
- **DO NOT create entity-specific FiltersModal files** — use the core one for all entities
- The `useFilters` hook automatically opens this modal via `openModal('filters.modal', { config })`

## Filter Definition Requirements

Each definition implements `getValue()`, `applyValue()`, `getDisplayValue()`, and either `getOptions()` (for all types except `infinite-autocomplete`) or `useQuery` (for `infinite-autocomplete`). Store must be Zustand with `actions.apply()`.

## Filter Types

- `text` — text input (single value)
- `dateRange` — date range picker
- `period` — period dropdown + date picker for custom ranges (must include "Custom" option)
- `enum` — multi-select (array of strings)
- `single-enum` — single select (string)
- `boolean` — boolean filter (true/false/null)
- `autocomplete` — entity search with `{ id, label, model? }` format. Use `createUserFilterTransformations()` for user filters.
- `infinite-autocomplete` — paginated entity search backed by a dedicated backend autocomplete endpoint. Requires `useQuery: (q: string) => UseInfiniteQueryResult` instead of `getOptions`. The section extraction is done inside the hook's `select` transform — no `sectionKey` on the definition. Component: `InfiniteAutocompleteFilterSelector`. Used for Warehouse Stock MPN and Manufacturer filters. Use `TInfiniteAutocompleteFilterDefinition<TFilterStore>` from `@chip1/filtering` as the narrowed type.

**Per-item chip deletion:** Filter types that store array values and support individual chip removal (`enum`, `autocomplete`, `infinite-autocomplete`) must be listed in the type-guard branches in both `packages/filtering/FilterBarWrapper.tsx` and `packages/filtering/FilterRow.tsx`. When adding a new array-valued filter type, update both files.

**Autocomplete filter hook placement:** Infinite query hooks backing `infinite-autocomplete` filters cannot live in `packages/core/hooks/` because they need app-level service instances. Create them at `apps/<app>/src/hooks/use<Domain>Autocomplete.ts` for each app. See `apps/crm/src/hooks/useStockPartsAutocomplete.ts` as the reference.

## Filter Helper Functions

From `apps/crm/src/features/filters/core/filterDefinitions.ts`:

- `createGetDisplayValue(options)` — for enum filters (maps option IDs to labels)
- `createGetDisplayValueForAutocomplete(options)` — for autocomplete filters with options
- `createGetDisplayValueForEntityAutocomplete()` — for entity autocomplete filters
- `createGetDisplayValueForUserAutocomplete()` — for user autocomplete filters
- `formatDateRangeDisplay(from, to)` — formats date ranges with i18n support (uses `summarizeDateRange` from `@chip1/core/utils/summarizeDateRange`)
- `createGetDisplayValueForDateRange()` — for dateRange filters (uses `formatDateRangeDisplay` internally)
- `createGetDisplayValueForPeriod(options, customPeriodId)` — for period filters with custom date range
- `createUserFilterTransformations()` — for user-type autocomplete filters (extractIds + transformValue)

## Date Range Formatting

Always use `formatDateRangeDisplay()` or `createGetDisplayValueForDateRange()` for date range filters:

- Use i18n translations (`filters.dateRange.after` and `filters.dateRange.before` from `common` namespace)
- Reuse `summarizeDateRange` from `@chip1/core` for consistent formatting
- Use `DATE_INPUT_FORMAT_DEFAULT` (`dd/MM/yyyy`) or `DATE_INPUT_FORMAT_US` (`MM/dd/yyyy`) from `@chip1/config/time`; for locale-aware format use `getLocaleDateInputFormat(regionShortName)` or the `useDateInputFormat()` hook in CRM (`apps/crm/src/hooks/useDateInputFormat.ts`)
- Handle invalid dates gracefully

## Context-Aware Filters

For features with multiple views (e.g., trips/visits), create separate stable hook wrappers:

```typescript
const useVisitsFilters = () => useEntityFilters(false);
const useTripsFilters = () => useEntityFilters(true);
const VisitsWrapper = createFilterBarWrapper(useVisitsFilters);
const TripsWrapper = createFilterBarWrapper(useTripsFilters);
```

## Migration Steps

1. Create filter definitions in `apps/crm/src/features/filters/[entity]/filterDefinitions.ts`
2. Create `use[Entity]Filters` hook in `apps/crm/src/features/filters/[entity]/use[Entity]Filters.ts`
3. Export from `apps/crm/src/features/filters/[entity]/index.ts`
4. Create stable filter wrapper(s) using `createFilterBarWrapper`
5. Use the shared `FiltersModal` from core (no entity-specific modal needed)

**Enum TypeScript Fix:** Cast string values to enum types when comparing in `getDisplayValue()`: `o.id === (v as ERfqStatusKey)`.

## Filter Store Defaults

Don't initialize with explicit nulls:

```typescript
// ❌ Redundant
const DEFAULT_FILTER: TFilter = {
  searchQuery: undefined,
  accounts: null,
  status: null,
  dateRange: null,
};

// ✅ Minimal — only specify non-null defaults
const DEFAULT_FILTER: TFilter = { isActive: true };
```

## Reference Implementations

- Simple: Account List in `apps/crm/src/features/filters/account/`
- Context-aware: Visits/Trips in `apps/crm/src/features/filters/visit/`

## Related
- [Architecture Patterns](architecture-patterns.md) — Zustand context pattern for filter stores
- [Formik Patterns](formik-patterns.md) — `FormikCheckbox` onChange pattern
- [Code Redundancy](code-redundancy.md) — filter store default initialization patterns
