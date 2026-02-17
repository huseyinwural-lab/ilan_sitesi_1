# ADMIN_RBAC_MENU_VISIBILITY

Bu doküman Admin IA v2 kapsamında menü görünürlüğü kurallarını standartlaştırır.

## 1) Roller (Örnek)
- Super Admin: her şey
- Finance Admin: Finans + raporlar
- Moderator: Moderation + listings read-only
- Ops Admin: Countries + Audit + Feature flags

> Repo’daki mevcut rol string’leri (gözlenen):
- super_admin
- country_admin
- moderator
- support
- finance

## 2) Domain Bazlı Menü Görünürlüğü (Önerilen)

### Dashboard
- super_admin, country_admin, moderator, support, finance

### Genel Bakış
- super_admin, country_admin, support

### Kullanıcı & Satıcı
- Kullanıcılar: super_admin, country_admin
- Bayiler: super_admin, country_admin
- Başvurular: super_admin, country_admin

### İlan & Moderasyon
- Moderation Queue: super_admin, country_admin, moderator
- İlanlar (liste/arama): super_admin, country_admin, moderator(read-only)
- Şikayetler: super_admin, country_admin, moderator

### Katalog & Yapılandırma
- Kategoriler: super_admin, country_admin
- Attributes: super_admin
- Menü Yönetimi: super_admin
- Feature Flags: super_admin, country_admin

### Master Data
- MDM Attributes: super_admin, country_admin
- Vehicle Makes/Models: super_admin, country_admin
- Import Jobs: super_admin, country_admin

### Finans
- Plans: super_admin, finance, country_admin
- Invoices: super_admin, finance
- Billing: super_admin, finance, country_admin
- Tax Rates: super_admin, finance

### Sistem
- Ülkeler: super_admin, country_admin
- Audit Logs: super_admin, country_admin, finance
- Sistem Ayarları: super_admin

## 3) Kural
- Menü görünürlüğü **UI tarafında** kısıtlanır.
- API tarafında gerçek yetki kontrolü ayrıca şarttır (server-side).
