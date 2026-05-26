# App-Specific Patterns Reference

**Trigger:** Read this file when modifying `apps/myChip1/src/features/NavBar/`, or when working on token refresh or root loader behavior.

## MC1 Account-Level Nav-Link Access Gate

For pages that require both a feature flag AND a per-tenant capability check:

1. Add `requiresPageAccess?: string` to `TNavLink` in `apps/myChip1/src/features/NavBar/types.ts`, setting the value to the path key returned by `GET /api/transaction/mc1-pages` (e.g., `'warehousing'`)
2. `NavBarLinksPane` fetches permissions via `useSuspenseMC1Pages()` from `apps/myChip1/src/hooks/useMC1Pages.ts` and hides links where `permissions.excludedPaths.includes(link.requiresPageAccess)`
3. The page component itself must also guard with `usePageAccess(path)` — if it returns `false`, render `<Navigate to={INNER_ROUTES.dashboard} replace />`

Both gates are required:

- Feature flag gates route registration (no route = no accidental direct URL access)
- Permissions endpoint restricts access per tenant at runtime

The `mc1Pages` query uses a 5-minute stale time and is automatically refetched on account switch via the existing `refetchQueries({ type: 'active' })` call in `useSwitchCurrentAccountMutation`.

## Token Refresh Pattern

For operations that change user context (account switch, view change):

`PATCH endpoint → tryRefreshAndPersistToken() → update local state → navigate to dashboard → query cleanup/refetch`

Reference: `useSwitchCurrentAccountMutation` in `apps/myChip1/src/hooks/useProfile.ts`.

## Root Loader Pattern for URL-Driven Configuration

Both apps register a `rootLoader` on the root route (`apps/crm/src/pages/rootLoader.ts`, `apps/myChip1/src/pages/rootLoader.ts`). This loader intercepts URL query parameters that configure app-wide state (currently `?theme=light|dark`), applies them via Zustand's `getState()`, strips the parameter, and redirects.

Use this loader — not component-level effects — when a URL parameter must be processed before the app renders and should not persist in the URL.

## Related
- [Architecture Patterns](architecture-patterns.md) — Zustand `getState()` pattern used by root loader
- [Feature Flags](feature-flags.md) — feature flag gates for nav-link access
