## Admin Route Map (v1)

| Menü | Route | Durum | Not |
| --- | --- | --- | --- |
| Kontrol Paneli | /admin | DONE | Dashboard özet kartlar + quick actions |
| Genel Bakış | /admin/dashboard | DONE | KPI + revenue MTD |
| Ülke Karşılaştırma | /admin/country-compare | DONE | Ülke bazlı KPI |
| Admin Kullanıcıları | /admin/admin-users | DONE | Read-only v1 |
| Rol Tanımları | /admin/roles | DONE | Read-only v1 |
| Yetki Atama (RBAC Matrix) | /admin/rbac-matrix | DONE | Read-only v1 |
| Kullanıcı Yönetimi | /admin/users | DONE | Tam liste yönetimi |
| Bireysel Kullanıcılar | /admin/individual-users | DONE | Read-only v1 |
| Kurumsal Kullanıcılar | /admin/dealers | DONE | Dealer yönetimi |
| Bireysel Üye Başvurular | /admin/individual-applications | DONE | Liste + approve/reject |
| Kurumsal Üye Başvurular | /admin/dealer-applications | DONE | Onay/ret akışı |
| Moderation Queue | /admin/moderation | DONE | Moderasyon listesi |
| Bireysel İlan Başvuruları | /admin/individual-listing-applications | DONE | Moderation Queue filtresi (dealer_only=false) |
| Kurumsal İlan Başvuruları | /admin/corporate-listing-applications | DONE | Moderation Queue filtresi (dealer_only=true) |
| Bireysel Kampanyalar | /admin/individual-campaigns | PLACEHOLDER | P1 CRUD |
| Kurumsal Kampanyalar | /admin/corporate-campaigns | PLACEHOLDER | P1 CRUD |
| Şikayetler | /admin/reports | DONE | Liste + detay + status |
| Kategoriler | /admin/categories | DONE | CRUD |
| Özellikler | /admin/attributes | DONE | CRUD |
| Menü Yönetimi | /admin/menu-management | PLACEHOLDER | v1 read-only |
| Araç Markaları | /admin/vehicle-makes | DONE | JSON seed |
| Araç Modelleri | /admin/vehicle-models | DONE | Make filtreli |
| Planlar | /admin/plans | DONE | CRUD |
| Faturalar | /admin/invoices | DONE | Liste + detay |
| Ödemeler | /admin/billing | PLACEHOLDER | P1 ödeme kayıtları |
| Vergi Oranları | /admin/tax-rates | DONE | CRUD |
| Ülkeler | /admin/countries | DONE | CRUD |
| Denetim Kayıtları | /admin/audit-logs | DONE | Filtreli liste |
| Sistem Ayarları | /admin/system-settings | DONE | CRUD |

Not: /admin/feature-flags route’u menüden kaldırılmıştır (v1 kapsamı dışı).
