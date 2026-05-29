@AGENTS.md

# Frontend Development Guide

## Next.js 16 Breaking Changes

This is NOT standard Next.js. Before writing any code, read the relevant guide in `node_modules/next/dist/docs/`.
Key differences from Next.js 15:
- `error.tsx` uses `unstable_retry()` instead of `reset()`
- Server Components and data fetching patterns may differ
- Always check `node_modules/next/dist/docs/` for the latest API

## Component Architecture

- **Pages** only do data fetching + composition
- **Business logic** goes in `hooks/` (e.g., `use-scoring-edit.ts`)
- **UI components** go in `components/ui/` (reusable across pages)
- **Feature components** go in `components/{feature}/` (e.g., `components/config/`)

## Error Handling Pattern

All SWR calls must handle errors:

```tsx
const { data, error, isLoading, mutate } = useSWR(key, fetcher);
if (error) return <ErrorState onRetry={() => mutate()} />;
```

Global error boundaries: `app/error.tsx` (route-level) + `app/global-error.tsx` (root).

## Server vs Client Components

- **Server Components**: Display-only pages (dashboard) — use `lib/server-api.ts` + Suspense
- **Client Components**: Interactive pages (config, leads, workbench) — use `'use client'` + SWR
- Always add `export const dynamic = "force-dynamic"` to Server Components that call authenticated APIs

## Type Generation

```bash
npm run generate-types       # From Python module (recommended)
npm run generate-types:live  # From running backend at localhost:8000
npm run lint                 # eslint
npm run test                 # vitest
npm run build                # next build
```

Generated types go to `lib/api-types.ts`. Gradually migrate from hand-written `lib/types.ts`.
Runtime validation schemas go to `lib/schemas.ts` (zod).
