# P1 — Public Site Console V1 (Route Map + Screen List + API Contract)

**Tarih:** 2026-02-24
**Amaç:** Public Site (Header/Ads/Doping/Footer/Info Pages) için backend + UI paralel geliştirme sözleşmesi.

---

## A) Route Map

### Admin (Backoffice)
- `/admin/site/header` → **Header Yönetimi** (logo upload + guest/auth preview)
- `/admin/ads` → **Reklam Yönetimi** (placement, süre, öncelik, upload)
- `/admin/doping` → **Doping Onay Masası** (requested/paid/approved/published/expired)
- `/admin/footer` → **Footer Grid Builder** (row/column/block düzenleme)
- `/admin/info-pages` → **Bilgi Sayfaları CRUD**

### Public
- `/` → **Homepage** (state-aware header + AD_HOME_TOP + doping showcase)
- `/search` → **Search** (AD_SEARCH_TOP)
- `/category/:slug` → **Category** (AD_CATEGORY_RIGHT)
- `/listing/:id` → **Listing Detail** (AD_LISTING_RIGHT)
- `/login` → **Login** (AD_LOGIN_1 / AD_LOGIN_2)
- `/bilgi/:slug` → **Info Page Template** (tek template)

---

## B) Ekran Listesi (UI Deliverables)

### Admin UI
1. **Header Yönetimi**
   - Logo upload + “guest/auth state” önizleme
   - Kaynak: `/api/admin/site/header`, `/api/admin/site/header/logo`

2. **Reklam Yönetimi**
   - Placement seçimi + priority + start/end + asset upload
   - Liste + güncelleme
   - Kaynak: `/api/admin/ads`, `/api/admin/ads/{id}`, `/api/admin/ads/{id}/upload`

3. **Doping Onay Masası**
   - Status filter (requested/paid/approved/published/expired)
   - Placement checkbox: homepage + category
   - Start/end + priority ayarı
   - Aksiyonlar: mark-paid → approve → publish

4. **Footer Grid Builder**
   - Row/column/block düzenleme
   - Layout JSON (link_group/social/text)
   - Publish aksiyonu

5. **Bilgi Sayfaları**
   - CRUD (TR/DE/FR içerikleri)
   - Publish toggle

### Public UI
1. **State-aware Header**
   - Guest: Giriş Yap / Üye Ol
   - Auth: Mesajlar / Bildirimler / Favoriler + profil menüsü
   - Logo admin’den çekilir (`/api/site/header`)

2. **Ads Render**
   - AD_HOME_TOP (homepage top)
   - AD_CATEGORY_RIGHT (category right)
   - AD_SEARCH_TOP (search top)
   - AD_IN_FEED (listing feed içinde)
   - AD_LISTING_RIGHT (detail right)
   - AD_LOGIN_1 / AD_LOGIN_2 (login slotları)

3. **Doping Showcase**
   - Homepage + Category highlight

4. **Footer Render + Info Pages**
   - Footer layout JSON
   - `/bilgi/:slug` tek template

---

## C) API Contract (Backend)

### 1) Header
- `GET /api/site/header`
  - **Response:** `{ logo_url: string | null }`
- `GET /api/admin/site/header`
  - **Response:** `{ id: string | null, logo_url: string | null }`
- `POST /api/admin/site/header/logo` (multipart)
  - **Response:** `{ ok: true, logo_url: string }`

### 2) Ads (Placement Engine + Analytics)
**Placement Enum (tek kaynak):**
```
AD_HOME_TOP
AD_CATEGORY_TOP
AD_CATEGORY_RIGHT
AD_CATEGORY_BOTTOM
AD_SEARCH_TOP
AD_IN_FEED
AD_LISTING_RIGHT
AD_LOGIN_1
AD_LOGIN_2
```

**Format Matrix:**
- TOP/BOTTOM/LOGIN/SEARCH = horizontal
- RIGHT = vertical
- IN_FEED = square

**Campaign Status:** `draft | active | paused | expired`

- `GET /api/ads?placement=AD_HOME_TOP`
  - **Response:** `{ items: [{ id, asset_url, target_url, start_at, end_at, priority }] }`

- `POST /api/ads/{id}/impression`
  - **Body:** `{ placement }`
  - **Rule:** IP+UA dedup (30 dk)
  - **Response:** `{ ok: true, deduped: boolean }`

- `GET /api/ads/{id}/click`
  - **Behavior:** click log → target_url redirect

- `GET /api/admin/ads`
  - **Response:** `{ items: [...], placements: { AD_HOME_TOP: "Anasayfa Üst Banner", ... } }`

- `GET /api/admin/ads/analytics?group_by=ad|campaign|placement&range=30d`
  - **Response:** `{ range, totals: { impressions, clicks, ctr, active_ads }, group_by, groups: [...] }`

- `POST /api/admin/ads`
  - **Body:** `{ placement, start_at?, end_at?, priority?, is_active?, target_url? }`
  - **Response:** `{ ok: true, id }`

- `PATCH /api/admin/ads/{id}`
  - **Body:** `{ start_at?, end_at?, priority?, is_active?, target_url? }`
  - **Response:** `{ ok: true }`

- `POST /api/admin/ads/{id}/upload` (multipart)
  - **Response:** `{ ok: true, asset_url }`

### 3) Doping (State Machine)
**Zorunlu Akış:** `requested → paid → approved → published → expired`

- `POST /api/v1/doping/requests`
  - **Body:** `{ listing_id, placement_home?, placement_category?, start_at?, end_at?, priority? }`
  - **Response:** `{ ok: true, id }`
  - **Initial status:** `requested`

- `POST /api/admin/doping/requests/{id}/mark-paid`
  - **Rule:** sadece `requested` → `paid`

- `POST /api/admin/doping/requests/{id}/approve`
  - **Rule:** sadece `paid` → `approved`
  - **Body:** `{ placement_home?, placement_category?, start_at?, end_at?, priority? }`

- `POST /api/admin/doping/requests/{id}/publish`
  - **Rule:** sadece `approved` → `published`

- `GET /api/admin/doping/requests?status=paid`
  - **Response:** `{ items: [...] }`

- `GET /api/doping/placements?placement=homepage|category`
  - **Response:** `{ items: [{ doping_id, listing_id, title, price, currency, priority }] }`

### 4) Footer Builder
- `GET /api/site/footer`
  - **Response:** `{ layout, version }`
- `GET /api/admin/footer/layout`
  - **Response:** `{ id, layout, status, version }`
- `PUT /api/admin/footer/layout`
  - **Body:** `{ layout, status }`
  - **Response:** `{ ok: true }`
- `POST /api/admin/footer/layout/publish`
  - **Response:** `{ ok: true }`

### 5) Info Pages
- `GET /api/admin/info-pages`
- `POST /api/admin/info-pages`
- `PATCH /api/admin/info-pages/{id}`
- `GET /api/info/{slug}` (public)

---

## D) Paralel Çalışma Hatları (P1)
- **Hat A (Backend):** API’ler + state machine + public endpoints
- **Hat B (UI):** Admin ekranları + public render (header/ads/doping/footer/info)

> Contract drift önlemi: Yukarıdaki enum ve endpoint sözleşmeleri tek kaynak kabul edilir.
