# TWOFA_BACKUP_CODE_EVIDENCE

**Tarih:** 2026-02-24 13:47:41 UTC
**Ortam URL:** https://category-wizard-1.preview.emergentagent.com
**Test Kullanıcı:** user2@platform.com

## Curl Kanıtı (Tek Kullanım)
- Backup code: `fd0caab4`

```
# 1. login (OK)
{"access_token":"..."}

# 2. login (FAIL)
{"detail":{"code":"INVALID_TOTP"}}
```

## UI Kanıtı (Tek Kullanım)
- Backup code: `a4fd8dad`
- Başarılı giriş: `/root/.emergent/automation_output/20260224_134152/backup-code-login-success.jpeg`
- Tekrar deneme (FAIL): `/root/.emergent/automation_output/20260224_134152/backup-code-login-fail.jpeg`

## Not
- Backup code kullanımı login akışında `totp_code` alanı üzerinden çalışır.
- İlk kullanım sonrası aynı code invalid olur (tek-kullanım enforce).
