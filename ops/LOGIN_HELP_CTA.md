# LOGIN_HELP_CTA

## Amaç
Login ekranlarında 401/429 durumlarında kullanıcıya yardımcı CTA’lar sağlamak.

## CTA’lar
- “Şifremi unuttum”
  - Tüm login ekranlarında görünür.
  - URL: v1.0.0 için placeholder kullanılabilir (örn. `/help/forgot-password`).

- “Hesap kilitlendi mi?”
  - Sadece 429 (RATE_LIMITED) durumunda görünür.
  - Kısa açıklama: “Güvenlik nedeniyle geçici olarak engellendi.”
  - URL: v1.0.0 için placeholder (örn. `/help/account-locked`).
