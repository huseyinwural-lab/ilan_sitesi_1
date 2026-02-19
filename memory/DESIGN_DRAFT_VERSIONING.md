# Draft Versioning + Diff Paneli (P1) — Teknik Tasarım

## 1) Amaç / Kapsam
- Admin tarafında kategori şeması değişikliklerini versiyon bazında izlemek
- Draft kayıtlarında immutable snapshot saklamak
- Versiyonlar arası yapısal (schema-level) diff göstermek

## 2) Veri Modeli
**Collection:** `categories_versions`

**Alanlar (snapshot bazlı):**
- `id` (uuid)
- `category_id`
- `version` (int, artan)
- `status` (`draft` | `published`)
- `schema_snapshot` (JSON, immutable)
- `created_at`
- `created_by`
- `created_by_role`
- `created_by_email`
- `published_at` (opsiyonel)
- `published_by` (opsiyonel)

**Indexler:**
- `id` unique
- `(category_id, version)` unique

## 3) API Contract
- **GET** `/api/admin/categories/{category_id}/versions`
  - Response: `{ items: [{ id, category_id, version, status, created_at, created_by_email, ... }] }`
- **GET** `/api/admin/categories/{category_id}/versions/{version_id}`
  - Response: `{ version: { id, version, status, schema_snapshot, created_at, ... } }`

> Not: Diff MVP client-side compute edilir (API diff endpoint’i P2 opsiyon).

## 4) Diff Yaklaşımı (Schema-level Structural Diff)
- JSON key-path tabanlı recursive karşılaştırma
- Çıktı: `"core_fields.title.min"`, `"modules.photos.enabled"` gibi path listesi
- UI: ilk 20-50 path listesi + side-by-side JSON görünümü

## 5) Retention
- Varsayılan: son 20 versiyon korunur
- Yeni versiyon eklenince eski kayıtlar purge edilir
- Configurable limit (ENV veya admin setting P2)

## 6) Yetkilendirme
- `super_admin`, `country_admin`
- Category country_code boş ise global erişim
- Country admin için `_assert_country_scope` doğrulaması

## 7) UI Akışı (MVP)
- Preview adımında **Versiyon Geçmişi** kartı
- Her versiyon için checkbox ile seçim (maks 2)
- **Compare View**: iki JSON snapshot + diff path listesi
- Seçim temizleme butonu

## 8) Edge-case’ler
- Versiyon yoksa “Henüz versiyon yok” boş state
- Publish direkt gelirse: son draft yoksa yeni “published” versiyon oluştur
- Büyük şema: diff listesi limitli, JSON pre max-height

## 9) Observability
- Versiyon oluşturma sırasında audit log event (P1 opsiyon)
- Dashboard metrikleri (P2): versiyon sayısı, publish sıklığı

## 10) Task Breakdown (EPIC → Ticket)
**EPIC: Draft Versioning + Diff MVP**
1. **BE-1:** `categories_versions` index + model
2. **BE-2:** Draft save’de versiyon insert + retention purge
3. **BE-3:** Publish sırasında latest version status update
4. **BE-4:** Version list/detail API endpoint’leri
5. **FE-1:** Preview step “Versiyon Geçmişi” kartı
6. **FE-2:** Compare view + diff path listesi
7. **QA-1:** Playwright/Unit test coverage (version list + compare)

---
Referans: PRD.md → “P1 Spec — Taslak Versiyon Geçmişi + Diff Paneli (MVP)”
