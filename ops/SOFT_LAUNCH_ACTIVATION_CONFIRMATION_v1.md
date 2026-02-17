# Soft Launch Activation Confirmation (v1)

**Tarih:** 14 Şubat 2026
**Durum:** AKTİF
**Politika:** C - Allowlist (İzinli E-posta)

## Özet
Platformun "Public Signup" özelliği kapatılmış ve sadece veritabanında (`signup_allowlist`) tanımlı e-posta adreslerinin kayıt olabileceği "Invite-Only" mekanizması devreye alınmıştır.

## Validasyon Bulguları
*   **Public Kayıt Engeli:** İzin listesinde olmayan e-posta ile kayıt denemesi `403 Forbidden` almaktadır.
*   **Invite-Only Kayıt:** Admin tarafından eklenen e-posta ile kayıt başarılı (`201 Created`) olmaktadır.
*   **Tekrar Kullanım Takibi:** Kullanıcı kayıt olduğunda davetiye `is_used=True` olarak işaretlenmektedir.
*   **Admin API:** `/api/v1/admin/allowlist` endpoint'i üzerinden e-posta yönetimi çalışmaktadır.

## Operasyonel Prosedürler
### 1. Yeni Kullanıcı Ekleme
Admin panel veya API üzerinden:
`POST /api/v1/admin/allowlist`
```json
{"email": "yeni.kullanici@example.com"}
```

### 2. Acil Durum (Emergency Override)
Eğer sistem çalışmazsa, doğrudan DB üzerinden ekleme yapılabilir:
```sql
INSERT INTO signup_allowlist (id, email, created_at) VALUES (gen_random_uuid(), 'acil@example.com', NOW());
```

## Riskler & İzleme
*   Admin yetkisine sahip kullanıcıların allowlist operasyonları `audit_logs` tablosunda `ADMIN_ADD_ALLOWLIST` aksiyonu ile izlenmektedir.
