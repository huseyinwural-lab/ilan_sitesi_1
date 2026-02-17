# FAZ-U1 Scope Lock

## 1. Kapsam (In-Scope)
FAZ-U1, platformun son kullanıcıya yönelik "Self-Service" yeteneklerinin temelini atar.

### 1.1. Veri Modeli
*   `User` tablosunun genişletilmesi:
    *   `user_type` (P28'den devralınır: `individual` / `commercial`)
    *   `kyc_status` (`none`, `pending`, `verified`, `failed`)
    *   `default_country` (`DE`, `AT`, `CH`, `FR`)
    *   `email_verified` (Boolean)
    *   `phone_verified` (Boolean)

### 1.2. API (/api/v1/me)
*   **READ**: Profil bilgilerini görüntüleme.
*   **UPDATE**: Temel bilgileri güncelleme (Ad, Ülke).
*   **SECURITY**: Doğrulama durumlarını sorgulama.

## 2. Kapsam Dışı (Out-of-Scope) - U1 İçin
*   **OTP/SMS Gönderimi**: Sadece durum (status) gösterilir, gönderim U1.1'de.
*   **Belge Yükleme (KYC)**: U1.1 veya U2 kapsamında.
*   **İlan Yönetimi**: U2 kapsamında.
*   **Ödeme/Fatura**: U2 kapsamında.

## 3. Bağımlılıklar
*   **P28**: Mevcut `user_type` alanı korunmalı.
*   **U2 (Listing)**: Listing wizard, U1'deki `user_type`'a göre akışı değiştirecek.
