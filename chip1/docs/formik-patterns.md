# Formik Patterns Reference

**Trigger:** Read this file before writing any Formik form with cascading fields, or when using FormikCheckbox, FormikAutocomplete, FormikMultiEmailTagInput, or the currency hook.

## Core Invariant: No Field Changes Without User Action

**No form field value must change without a direct user action.** Forms can be open for 5–10 minutes while users verify data or switch tabs. React Query's background refetching periodically returns new object references — any pattern that reacts to those will silently overwrite user-entered data.

## onChange Handlers over useEffect for Field Cascading

When a field change should update other fields (e.g., selecting an account auto-fills billing address), use the field's `onChange` handler — NOT a `useEffect`. `useEffect` with query-derived deps re-fires on every React Query background refetch and overwrites user edits.

- ✅ Async `onChange`: fetch related data with `ensureSafeQueryData` from `@chip1/utils/safeQueryClient`, then `setFieldValue` for dependents
- ❌ `useEffect(() => { setFieldValue(...) }, [someQueryData])` — fires on refetch, not just user action
- ❌ `useEffect(() => { setValues(...) }, [someQueryData])` — same problem, broader damage
- ❌ `useEffect(() => { resetForm(...) }, [someQueryData])` — resets the entire form on refetch
- ❌ `queryClient.fetchQuery(...)` or `queryClient.ensureQueryData(...)` directly — use `ensureSafeQueryData`/`fetchSafeQuery` wrappers from `@chip1/utils/safeQueryClient` instead for correct TypeScript inference
- Pure math from user-typed values (e.g., `totalCost = unitPrice * qty`) is safe as `useEffect` since there's no query dependency

### `ensureSafeQueryData` vs `fetchSafeQuery`

- `ensureSafeQueryData` — returns cached data if fresh. Use when the field may re-select the same value (avoids redundant network requests)
- `fetchSafeQuery` — always fetches fresh. Use when staleness matters more than cache reuse (e.g., part details that change frequently)

### Stale-Response Guard

When `await`-ing inside an async `onChange`, the user may change the field again before the first fetch resolves. Guard with a `useRef` tracking the latest selection:

```typescript
latestIdRef.current = id;
const data = await ensureSafeQueryData(...);
if (latestIdRef.current !== id) { return; }
```

### Reference Implementation

`useAccountFieldsSync` in `apps/crm/src/features/CreateSalesOrderForm/useAccountFieldsSync.ts` — hook returns `onAccountChange` async handler; call sites pass it to the account autocomplete's `onChange`. Accepts `syncShippingInfo` and `syncPaymentTermsAndTaxRate` boolean options.

### Pre-Selected Fields

When a form opens with a field already populated (disabled), the `onChange` handler never fires. **Prefer computing defaults before the form renders** — pass them in `initialValues` so the form snapshot is complete on mount and no post-mount mutation is needed:

- (a) **Preferred:** Pre-populate derived fields in `initialValues` directly (use when data is available as props, e.g. `TAccountDetails`)
- (b) Use a single-fire `useEffect` with empty deps `[]` that calls the handler once on mount (use only when data must be fetched and cannot be available before render)

Option (b) is acceptable because the `useEffect` with `[]` deps fires exactly once and never reacts to refetches.

## FormikCheckbox onChange for Cascading

Pass `onChange?: (event: SyntheticEvent, checked: boolean) => void` to `FormikCheckbox` to run side effects when a checkbox changes (e.g., auto-filling `approvedBy`/`approvedOn`). Fires after the field value is set, so `setFieldValue` for dependent fields is safe inside it.

## FormikAutocomplete onChange — Suppressing Default setValue

`FormikAutocomplete` calls the external `onChange` prop first, then calls `helpers.setValue(rawValue)` unless `onChange` returns `true`. If your handler sets a patched value via `setFieldValue`, return `true` to prevent the raw value from overwriting your patch:

```typescript
onChange={(_event, newValue) => {
  void setFieldValue('field', patch(newValue));
  return true; // prevents FormikAutocomplete from calling helpers.setValue(rawValue)
}}
```

## FormikForm enableReinitialize

`FormikForm` defaults to `enableReinitialize={false}`. Do NOT add `enableReinitialize={true}` — React Query refetches return new object references, which Formik treats as changed `initialValues` and reinitializes the entire form, silently discarding user edits.

If a form must reinitialize when its entity _changes_ (e.g., navigating between records), key the component on the entity ID instead — React unmounts/remounts the form only when the ID actually changes:

```typescript
<FormikForm key={entity.id} initialValues={...} />
```

## Multi-Email Tag Input

For `string[]` Formik fields collecting email addresses, use `FormikMultiEmailTagInput` from `@chip1/core/components/formik/FormikMultiEmailTagInput`. It handles Enter/comma/semicolon key triggers, paste splitting, blur-to-add, email deduplication, and touched-state marking. Do NOT re-implement with a raw `FieldArray` + text input pattern.

```typescript
import { FormikMultiEmailTagInput } from '@chip1/core/components/formik/FormikMultiEmailTagInput';

<FormikMultiEmailTagInput name="invoicePreference.email" label={t('invoiceEmail')} disabled={isReadOnly} />
```

## Currency Hook (CRM)

To get the current user's currency in a CRM component, use `useSuspenseUserCurrency()` from `@/hooks/useRegions` (requires a Suspense boundary). Do not inline the 3-line pattern:

```typescript
// ❌ Don't inline
const user = useSuspenseProfile();
const regionCurrency = useSuspenseRegionCurrency(user.regionIdStr);
const currency = regionCurrency ?? DEFAULT_CURRENCY;

// ✅ Use the hook
const currency = useSuspenseUserCurrency();
```

## Related
- [Architecture Patterns](architecture-patterns.md) — PATCH diff for form payloads, `ensureSafeQueryData` from `@chip1/utils/safeQueryClient`
- [Code Redundancy](code-redundancy.md) — validation schema defaults for initialValues
- [Filter System](filter-system.md) — `FormikCheckbox` onChange shared pattern
