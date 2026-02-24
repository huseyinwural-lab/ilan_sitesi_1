# RBAC_NEGATIVE_TESTS

**Son güncelleme:** 2026-02-24 11:21:40 UTC

## Amaç
Deny-by-default ve allowlist doğrulaması için negatif test seti.

## Test Önkoşulları
- Test roller için token alınmış olmalı (super_admin, country_admin, moderator, support, finance, dealer, individual)
- Tüm testlerde **403** beklenir (aksi belirtilmedikçe)

## Negatif Test Listesi (Özet)
1) **SUPPORT → Sistem Ayarları**
   - GET `/api/admin/system-settings/cloudflare` → **403**
2) **SUPPORT → Finans**
   - GET `/api/admin/invoices` → **403**
3) **MODERATOR → Sistem**
   - GET `/api/admin/countries` → **403**
4) **MODERATOR → Admin Users**
   - GET `/api/admin/admin-users` → **403**
5) **ADMIN (country_admin) → Admin Users**
   - GET `/api/admin/admin-users` → **403**
6) **FINANCE → Moderation Queue**
   - GET `/api/admin/moderation/queue` → **403**
7) **DEALER → Admin Panel**
   - GET `/api/admin/system/health-detail` → **403**
8) **CONSUMER → Admin Panel**
   - GET `/api/admin/system/health-detail` → **403**
9) **AUDIT_VIEWER → System Settings**
   - GET `/api/admin/system-settings` → **403**
10) **PUBLIC (no token) → protected admin endpoint**
   - GET `/api/admin/system/health-detail` → **401**

## Not
- Public allowlist: `/api/admin/invite/preview` ve `/api/admin/invite/accept` sadece token doğrulama üzerinden erişebilir (RBAC guard **public** istisnası).
