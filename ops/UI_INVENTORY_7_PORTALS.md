# UI_INVENTORY_7_PORTALS

Bu doküman repo içindeki mevcut yapıyı baz alarak 7 arayüz için **route + entrypoint** envanterini çıkarır.

> Not: Bu repo’da portal ayrıştırması tam değil. Bazı “portal”lar admin içinde sayfa olarak bulunuyor.

## 1) Public Site (Ziyaretçi)
### Routes (frontend)
- `/` → `HomePage` (`/app/frontend/src/pages/public/HomePage.js`)
- `/search` → `SearchPage` (`/app/frontend/src/pages/public/SearchPage.js`)
- `/ilan/:id` → `DetailPage` (`/app/frontend/src/pages/public/DetailPage.js`)
- `/:country/vasita` → `VehicleLandingPage`
- `/:country/vasita/:segment` → `VehicleSegmentPage`
- `/vasita` → `RedirectToCountry`

### Layout
- `PublicLayout` (`/app/frontend/src/layouts/PublicLayout.js`)

### Guards
- Yok (public)

### API bağımlılıkları (gözlenen)
- `GET /api/menu/top-items`
- `GET /api/categories?module=...`
- `GET /api/v2/search?...` (SearchPage)
- `GET /api/v1/listings/vehicle/{id}` (DetailPage)

## 2) User Panel (Bireysel)
### Routes
- `/account` → `UserPanelLayout`
  - `/account/listings` → `MyListings`
  - `/account/create` → `CreateListing`
  - `/account/create/vehicle-wizard` → `WizardContainer`

### Layout
- `UserPanelLayout` (`/app/frontend/src/layouts/UserPanelLayout.js`)

### Guards
- **Eksik**: App.js’de /account route’larında ProtectedRoute yok (gap)

### API bağımlılıkları
- Şu an `MyListings` mock data kullanıyor (gap)
- Wizard publish API’leri (backend hazır):
  - `POST /api/v1/listings/vehicle` (draft)
  - `POST /api/v1/listings/vehicle/{id}/media`
  - `POST /api/v1/listings/vehicle/{id}/submit`

## 3) Dealer Panel (Ticari)
### Routes
- Ayrı dealer layout/route gözlenmedi (gap)

### UI sayfaları (admin içi gibi duran)
- `DealerManagement.js` (admin sayfası)

### Guards
- Admin ProtectedRoute rol ile (kısmi)

### API bağımlılıkları
- Dealer endpoint’leri server.py’da görünmüyor (muhtemelen /app/backend/app/routers altında var; envanter fazı için ayrıca taranacak)

## 4) Admin Panel
### Routes
- `/admin` → `Layout + Dashboard`
- `/admin/users` → `Layout + Users`
- `/admin/countries` → `Layout + Countries`
- `/admin/categories` → `Layout + Categories`
- `/admin/attributes` → `Layout + AdminAttributes`
- `/admin/master-data/vehicles` → `Layout + AdminVehicleMDM`
- `/admin/feature-flags` → `Layout + FeatureFlags`
- `/admin/plans` → `Layout + Plans`
- `/admin/billing` → `Layout + Billing`

### Layout
- `Layout` (`/app/frontend/src/components/Layout.js`) (admin layout)

### Guards
- `ProtectedRoute` (roles)
- Admin Country Context v2:
  - URL `?country=XX` + backend enforcement (kısmi)

### API bağımlılıkları (server.py)
- `POST /api/auth/login`, `GET /api/auth/me`
- `GET /api/dashboard/stats`
- `GET /api/users`
- `GET/PATCH /api/countries`
- `GET/PATCH /api/menu/top-items`
- `GET /api/categories`
- `GET/POST /api/v1/admin/vehicle-master/*`

## 5) Moderation Workspace
### Routes
- Dedicated route yok (gap)
- UI sayfası mevcut: `ModerationQueue.js` (muhtemelen /admin içinde planlanmış)

## 6) Support / CRM
### Routes
- Dedicated route yok (gap)

## 7) Analytics / Growth Panel
### Routes
- Dedicated route yok (gap)

## Guard Noktaları Özeti
- Auth guard: `ProtectedRoute` App.js
- Role guard: `ProtectedRoute roles=[...]`
- Country context guard:
  - Frontend: Layout.js URL + toggle
  - Backend: `resolve_admin_country_context()` (yalnızca bazı endpoint’lerde uygulanıyor)
