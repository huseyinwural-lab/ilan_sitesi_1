# CONSUMER_SECURITY_GDPR_SPEC

## Amaç
Güvenlik ve GDPR uyumlu kimlik yönetimi.

## Özellikler
- Email doğrulama zorunlu
- 2FA (TOTP) opsiyonel
- Aktif oturumlar listesi
- Şifre değiştirme
- Hesap silme (soft delete + 30 gün grace, hard delete job)

## Bileşenler
- 2FA setup wizard
- Active sessions table
- Change password form
- Delete account modal (geri dönüş uyarısı)

## Empty state
- Oturum yok → "Sadece bu cihaz" mesajı

## Success/Error
- 2FA etkinleştirildi → success banner
- Yanlış şifre → error

## RBAC
- consumer

## GDPR Notu
- Right to be Forgotten: soft delete + hard delete job
