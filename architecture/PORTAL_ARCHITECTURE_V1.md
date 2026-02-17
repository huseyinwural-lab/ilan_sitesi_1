# PORTAL_ARCHITECTURE_V1

## Amaç
CRA + CRACO bağlamında 3 portal için **layout + bundle (chunk) split** sağlayarak:
- admin shell leakage riskini sıfırlamak
- role/portal izolasyonunu güçlendirmek
- yanlış portal kodunun yanlış kullanıcıya yüklenmesini engellemek

## Yaklaşım: Route-based lazy loading (single entry + chunk split)
- Tek HTML/entry korunur (`src/index.js` → `App`).
- Portal router modülleri `React.lazy(() => import(...))` ile **ayrı chunk** olarak yüklenir.
- Kritik: **pre-layout guard** portal chunk import’u tetiklenmeden önce çalışır.

## Route Namespace’leri
- Public/Individual: `/`, `/search`, `/listing/:id` (mevcutta `/ilan/:id`), `/account/*`, `/login`
- Dealer: `/dealer/*`, `/dealer/login`
- Backoffice: `/admin/*`, `/admin/login`
  - opsiyonel v2: `/moderation/*`, `/support/*` ayrı prefix (bu fazda admin altında kalabilir)

## Entrypoint / Router Şeması
- `App` (main bundle)
  - Public/Individual routes (main)
  - Dealer portal loader (lazy chunk)
  - Backoffice portal loader (lazy chunk)

### Portal modülleri
- `src/portals/public/PublicIndividualRoutes` (main bundle)
- `src/portals/dealer/DealerPortalApp` (chunk: `portal-dealer`)
- `src/portals/backoffice/BackofficePortalApp` (chunk: `portal-backoffice`)

## Ortak Paketler (shared)
- `shared/ui-kit` (shadcn + common components)
- `shared/auth-client` (AuthContext, token helpers)
- `shared/api-client` (axios wrappers)
- `shared/types` (role/portal types)

## Guard Katmanı (pre-layout)
- “pre-layout role gate”: portal layout mount edilmeden önce çalışır.
- Yanlış rolde:
  - **403** + redirect (doğru portal home)
  - admin/dealer chunk import’u **tetiklenmez**

## Post-login redirect matrisi
- `super_admin/country_admin/moderator/finance/support` → `/admin`
- `dealer` → `/dealer`
- `individual` → `/account`

## Kabul Kriteri (ölçülebilir)
1) `/admin/*` kodu **ayrı chunk** olarak yalnız admin portalına girince yüklenir.
2) `/dealer/*` kodu **ayrı chunk** olarak yalnız dealer portalına girince yüklenir.
3) Yanlış rolde bu chunk’lar **indirilmeyecek** (network kanıtı).
4) Admin layout/shell DOM’a **hiç mount olmayacak** (pre-layout guard).
