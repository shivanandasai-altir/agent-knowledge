# TypeScript 6 tsconfig Conventions

**Trigger:** Read this file when setting up a new package, or when troubleshooting TypeScript path alias or ambient type errors.

## `types` Array is Required for Ambient Globals

TS6 does not auto-discover installed `@types/*` packages when a `types` array is present. If a package or app uses ambient globals from any `@types/*` package (e.g., `@types/node` for `process.env`, `@types/google-maps` for `google.maps.*`), it must list them explicitly:

- `"types": ["node"]`
- `"types": ["google.maps", "node"]`

Apps with no `types` array still get full auto-discovery. Symptom of a missing entry: `Cannot find name 'process'` or `Cannot find namespace 'google'`.

## `paths` Entries Must Be Relative — No `baseUrl`

`baseUrl` is deprecated in TS6. Path aliases must use explicit relative paths:

- ✅ `"@/*": ["./src/*"]`
- ❌ `"@/*": ["src/*"]` (relied on `baseUrl`)

Do not add `baseUrl` to resolve aliases in new apps or packages.

## `noUncheckedSideEffectImports` Requires CSS Module Declarations

TS6 enables this by default. Any bare side-effect CSS import (`import 'some.css'`) must have a `declare module '*.css'` ambient declaration in the package's `.d.ts` file.

Declarations live in:

- `packages/components/cssModules.d.ts` (for `@chip1/components`)
- `packages/core/types/vendor.d.ts` (for `@chip1/core`)

When adding a new package that imports CSS, add a declaration to that package's ambient `.d.ts`:

```typescript
declare module '*.css' {
  const styles: Record<string, string>;
  export default styles;
}
```

Do not set `noUncheckedSideEffectImports: false` to suppress this.

## `pnpm.overrides` Policy

Use only as a last resort when a transitive dependency cannot be updated directly. Prefer upgrading the direct dependency first. Current overrides: `vite` (pinned to `^8.0.0`) and `@typescript-eslint/*` packages (pinned to exact `8.58.0`).

## `minimumReleaseAgeExclude` in `pnpm-workspace.yaml`

The workspace enforces a 14-day minimum release age as a supply-chain safety control. If a required package version is newer than 14 days, add it to `minimumReleaseAgeExclude`. Remove exclusions once the packages no longer need to bypass the age gate.

## Related
- [Architecture Patterns](architecture-patterns.md) — importing shared types from `@chip1/core/types/transactional.ts`
