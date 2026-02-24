# RBAC_MATRIX

**Son güncelleme:** 2026-02-24 11:21:40 UTC
**Phase:** B — RBAC Final Freeze (Source of Truth)
**Durum:** FREEZE v1 (değişiklikler PR diff-onay zorunlu)

## İlke
- **Deny-by-default** (allowlist yoksa erişim yok)
- **Explicit allow list** (endpoint bazlı politika)
- **RBAC audit log** (RBAC_DENY / RBAC_POLICY_MISSING)

## Kanonik Roller (Freeze v1)
- **SUPER_ADMIN**: Tüm admin modülleri + sistem ayarları + RBAC yönetimi
- **ADMIN**: Ülke kapsamlı admin yetkileri (kullanıcı/ilan/moderasyon/katalog/sistem)
- **MODERATOR**: Moderasyon ve içerik kalite
- **SUPPORT**: Üye operasyonları ve destek
- **DEALER_ADMIN**: Dealer portal yönetimi
- **DEALER_USER**: Dealer portal standart kullanım
- **CONSUMER**: Consumer portal kullanım

## Runtime Rol Eşlemesi (mevcut sistem)
- SUPER_ADMIN → `super_admin`
- ADMIN → `country_admin`
- MODERATOR → `moderator`
- SUPPORT → `support`
- DEALER_ADMIN / DEALER_USER → `dealer` (v1’de ayrım yok)
- CONSUMER → `individual`

**Legacy / özel roller (v1 uyumluluk):**
- `finance` → ADMIN alt set (Finans modülleri)
- `campaigns_admin` / `campaigns_supervisor` → MODERATOR alt set (Kampanyalar)
- `ROLE_AUDIT_VIEWER` / `audit_viewer` → SUPPORT alt set (Audit görüntüleme)

## Modül Bazlı Erişim Matrisi (Özet)
| Modül | SUPER_ADMIN | ADMIN | MODERATOR | SUPPORT | DEALER_ADMIN | DEALER_USER | CONSUMER |
|---|---|---|---|---|---|---|---|
| Admin Dashboard & Health | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Admin Kullanıcıları / RBAC | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Üyeler (Bireysel/Kurumsal) | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ |
| Moderasyon (Queue + Aksiyon) | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Katalog & İçerik (Kategori/Attribute) | ✅ | ✅ | ✅ (view) | ❌ | ❌ | ❌ | ❌ |
| Araç Master Data | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Finans (Plan/Ödeme/Fatura) | ✅ | (finance) | ❌ | ❌ | ❌ | ❌ | ❌ |
| Sistem (Ülkeler/Sistem Ayarları) | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Audit Log | ✅ | ❌ | ❌ | (audit_viewer) | ❌ | ❌ | ❌ |
| Kampanyalar | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Dealer Portal | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ❌ |
| Consumer Portal | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |

## Notlar
- ADMIN rolü (country_admin) **country_scope** ile sınırlandırılır.
- MODERATOR sadece moderasyon aksiyonlarına erişir; sistem ayarlarına erişmez.
- SUPPORT yalnız üye operasyonlarını görür; sistem/finans erişimi yoktur.
- Dealer/Consumer rollerinin admin panel erişimi yoktur.
