# Code Redundancy Guidelines

**Trigger:** Read this file when performing a code review, or before submitting a feature that involves forms, filters, or VM/transformation functions.

## Validation Schema and Initial Values

`FormikForm` casts `initialValues` through the Yup schema before Formik sees them, so schema defaults (`.default('')`, `.default(null)`, `.ensure()`) are applied automatically.

```typescript
// ❌ Redundant — manually setting empties that the schema already provides
const initialValues = {
  name: entity.name ?? '',
  description: entity.description ?? '',
  expires: entity.expires ?? null,
};

// ✅ Clean — pass the entity directly, schema cast handles the rest
const initialValues = entity;
```

## Permission-Based Section Rendering

Avoid multiple array passes — map/filter the same array only once:

```typescript
// ❌ Multiple passes over the same array
const mapped = sections.map(s => ({ ...s, component: getComponent(s) }));
const filtered = mapped.filter(s => hasPermission(s));
const rendered = filtered.map(s => <Component key={s.key} {...s} />);

// ✅ Single pass
{sections.map(key => {
  const permission = permissionsMap[key];
  if (!permission) { return null; }
  return <Component key={key} sectionPermissions={permission} />;
})}
```

## Filter Store Defaults

Don't initialize with explicit nulls:

```typescript
// ❌ Redundant null initialization
const DEFAULT_FILTER: TFilter = {
  searchQuery: undefined,
  accounts: null,
  status: null,
  dateRange: null,
};

// ✅ Minimal — only specify non-null defaults
const DEFAULT_FILTER: TFilter = {
  isActive: true,
};
```

## VM / Transformation Functions

Pass whole objects to VM functions — don't destructure at the call site:

```typescript
// ❌ Fragile — must update all call sites when adding fields
const vm = toShipmentVm({ id: shipment.id, name: shipment.name, status: shipment.status });

// ✅ Flexible — VM function owns the transformation
const vm = toShipmentVm(shipment);
```

## General Principles

1. **Single Source of Truth** — defaults live in one place (schema, constant, or config)
2. **Minimal Initialization** — don't pre-populate state with explicit `null`/`undefined` values
3. **Single Pass** — avoid multiple array iterations when one will do
4. **Forward Whole Objects** — let transformation functions own their input requirements

## Related
- [Formik Patterns](formik-patterns.md) — validation schema defaults for initialValues cleanup
- [Filter System](filter-system.md) — filter store default patterns (explicit nulls)
- [Architecture Patterns](architecture-patterns.md) — VM transformation pattern, helper function usage (getFullName)
