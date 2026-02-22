# AUTH_SECURITY_STRESS_EVIDENCE

**Tarih:** 2026-02-22 01:20:30 UTC

## 1) Login Rate Limit
10 hatalı deneme:
```
1:401
2:401
3:401
4:401
5:429
6:429
7:429
8:429
9:429
10:429
```

## 2) 2FA Backup Code Reuse
- Setup → verify: PASS
- Backup code ile login: PASS
- Aynı backup code reuse: **401 INVALID_TOTP**

## 3) Soft Delete → Login Block
- DELETE /api/v1/users/me/account → gdpr_deleted_at + is_active=false
- Login sonrası: **403 User account suspended**

## 4) Honeypot
```
POST /api/auth/register/consumer (company_website dolu) → 400 Invalid request
```
Audit log:
```
register_honeypot_hit
```

## 5) GDPR Export Notification
- /api/v1/users/me/data-export → JSON
- Notification: “Veri dışa aktarma tamamlandı. Hesabınızdan bir veri erişimi gerçekleşti.” (severity=warning)
- Audit: gdpr_export_completed + gdpr_export_notification_sent
