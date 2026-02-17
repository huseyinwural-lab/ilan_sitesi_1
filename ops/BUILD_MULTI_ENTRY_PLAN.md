# BUILD_MULTI_ENTRY_PLAN (CRA + CRACO)

## Hedef
3 portal için ayrı bundle (chunk) üretmek:
- main (public/individual)
- portal-dealer (lazy chunk)
- portal-backoffice (lazy chunk)

## Yaklaşım
- CRA tek entry korunur.
- `React.lazy(() => import('.../DealerPortalApp'))` ve `React.lazy(() => import('.../BackofficePortalApp'))` ile portal chunk split yapılır.
- Ortak dependency’ler webpack’in default splitting davranışı ile shared chunk’lara ayrılır.

## Deployment
- Tek host altında path-based serve:
  - `/dealer/*` ve `/admin/*` aynı SPA origin’den servis edilir.
  - Client-side router ile ilgili chunk’lar gerektiğinde indirilir.

## Cache Policy (öneri)
- `static/js/*.chunk.js` hashed output → long-cache
- `index.html` → no-cache veya short-cache

## Riskler
- Import boundary ihlali portal kodunu main’e sızdırabilir.
  - Önlem: portals/* importlarının App.js dışında kullanılmaması + test plan network assertion.
