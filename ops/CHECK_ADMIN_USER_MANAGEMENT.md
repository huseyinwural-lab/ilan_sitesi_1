# CHECK_ADMIN_USER_MANAGEMENT

## Amaç
Admin kullanıcı yönetimi (admin ekleme/çıkarma) ve least-privilege denetimi.

## Mevcut Repo Durumu (Gözlem)
- Admin kullanıcı listesi: `/admin/users` mevcut.
- Kullanıcı oluşturma/güncelleme: UI’da kısmi (role update vs) var.
- Backend’de admin create/update/disable/delete endpoint envanteri bu fazda netleştirilecek.

## Kontroller

### 1) Admin create/update/disable/delete
- [ ] Admin create akışı var mı?
- [ ] Admin disable/delete var mı?
- [ ] Role atama güncellemesi var mı?

### 2) Audit
- [ ] Role değişikliği audit’e düşüyor mu?
- [ ] Country scope loglanıyor mu?

### 3) Least privilege
- [ ] Moderator finance görememeli
- [ ] Finance admin moderation görememeli
- [ ] Support admin sadece gerekli domain’leri görebilmeli

### 4) Self-lockout engeli
- [ ] super_admin kendini role/disable ile kilitleyemiyor mu?

## Ön Karar
- Bu modül: PARTIAL/FAIL bekleniyor (audit ve self-lockout muhtemelen eksik)

## Sonraki Adım
- Backend router dosyalarında (users, admin, rbac) endpoint taraması yap.
- UI’da Users sayfasında create/update yeteneklerini doğrula.
