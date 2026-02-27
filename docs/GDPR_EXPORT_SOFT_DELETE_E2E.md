# GDPR_EXPORT_SOFT_DELETE_E2E

**Tarih:** 2026-02-24 12:51:30 UTC
**Ortam URL:** https://config-telemetry.preview.emergentagent.com

## Scope
- Kullanıcı veri exportu oluşturma
- Soft delete sonrası erişim doğrulaması
- Admin audit kayıtları

## Kanıt
- Export endpoint: `/api/v1/users/me/data-export` → 200
- Soft delete endpoint: `/api/v1/users/me/account` → 200 (status=scheduled)
- Soft delete sonrası login: `/api/auth/login` → 403 (User account suspended)
- UI kanıtı: `/root/.emergent/automation_output/20260224_125145/gdpr-soft-delete-login.jpeg`
- Audit log:
  - `gdpr_export_requested`
  - `gdpr_delete_requested`

## Test Notları
- Test kullanıcı: user2@platform.com
- Export payload içinde user.email ve exported_at doğrulandı
- Soft delete sonrası kullanıcı erişimi bloke edildi (login 403)
