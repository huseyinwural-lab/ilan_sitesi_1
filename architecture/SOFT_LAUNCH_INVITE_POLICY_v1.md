# Soft Launch Invite Policy (v1)

**Politika Adı:** Invite-Only Allowlist Enforcement
**Kapsam:** `/auth/register` (Tüm Kullanıcı Kayıtları)
**Faz:** Soft Launch (P14 öncesi)

## 1. Amaç
Platformun "Soft Launch" aşamasında kontrolsüz kullanıcı büyümesini engellemek, sistem stabilitesini korumak ve sadece hedeflenen (onboarding listesindeki) kullanıcıların sisteme girişini sağlamak.

## 2. Mimari Karar: C - Allowlist (İzinli E-posta)
Kullanıcı kayıtları, veritabanında tutulan bir `signup_allowlist` tablosuna dayalı olarak sınırlandırılır.

### Gerekçe
*   **Davet Kodu (Riskli):** Statik kodların sızması ve kontrolsüz paylaşımı riski vardır.
*   **Tamamen Kapalı (Operasyonel Yük):** Kullanıcıların admin tarafından manuel oluşturulması, parola belirleme ve KVKK süreçlerini zorlaştırır.
*   **Allowlist (Dengeli):** Kullanıcı kendi şifresini belirler, KVKK onayını verir; ancak sadece admin'in "yetki verdiği" e-posta adresini kullanabilir.

## 3. Uygulama Detayları

### Veritabanı Şeması
`signup_allowlist` tablosu:
*   `id`: UUID
*   `email`: String (Unique, Index) - E-posta adresi
*   `created_by`: UUID (Admin User ID)
*   `created_at`: Datetime
*   `is_used`: Boolean (Kullanıcı kayıt olduğunda True olur)

### Kayıt Akışı (`/auth/register`)
1.  Kullanıcı kayıt formunu doldurur.
2.  Backend, gelen `email` adresini `signup_allowlist` tablosunda sorgular.
3.  **EĞER** e-posta listede yoksa:
    *   HTTP 403 Forbidden döner.
    *   Hata Mesajı: *"Kayıtlar şu an sadece davetiye ile yapılmaktadır. Lütfen bekleme listesine katılın."*
4.  **EĞER** e-posta listede varsa:
    *   Kayıt işlemi standart prosedürle (User tablosuna ekleme) devam eder.
    *   `signup_allowlist` tablosundaki `is_used` alanı `True` olarak işaretlenir (Opsiyonel: tekrar kaydı engellemek için değil, takip için).

### Admin Operasyonu (Admin Override)
*   Acil durumlarda veya yeni kullanıcı onboard edileceğinde, Admin Panel (veya API) üzerinden `signup_allowlist` tablosuna yeni e-posta satırı eklenir.
*   Denetim (Audit) loglarında bu işlem `ADMIN_ADD_ALLOWLIST` olarak kaydedilir.

## 4. Güvenlik & Riskler
*   **Risk:** Yanlış e-posta eklenmesi. -> **Önlem:** Ekleme işleminde format validasyonu.
*   **Risk:** Allowlist bypass. -> **Önlem:** Backend seviyesinde zorunlu kontrol (Frontend kontrolü yetersizdir).

## 5. Çıkış Kriteri (Gate)
Bu politika, "Public Launch" kararı verilene kadar (P14 veya sonrası) aktif kalacaktır. Public Launch'ta bu kontrol devre dışı bırakılır veya "Waitlist" moduna evrilir.
