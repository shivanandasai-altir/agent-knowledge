# i18n / Translation Rules

**Trigger:** Read this file when adding or modifying translation namespaces.

## Namespace Usage

- Single namespace: `useTranslation('view')` → keys without prefix: `t('selectView.title')`
- Multiple namespaces: `useTranslation(['view', 'common'])` → keys with prefix: `t('view:selectView.title')`

## Adding a New Translation Namespace

1. Create JSON file in `packages/core/locales/en/[namespace].json`
2. Add import in `packages/core/types/i18n.ts`:
   ```typescript
   import type [namespace] from '../locales/en/[namespace].json'
   ```
3. Add to `TI18nCoreLocales` type:
   ```typescript
   [namespace]: typeof [namespace]
   ```
4. No runtime registration needed — handled automatically by `importCoreLocale`

## Related
- [Architecture Patterns](architecture-patterns.md) — transactional shared types reference i18n for document labels
