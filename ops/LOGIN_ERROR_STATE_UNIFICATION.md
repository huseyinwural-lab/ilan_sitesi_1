# LOGIN_ERROR_STATE_UNIFICATION

## Amaç
Tüm portalların Login UI’ında error state handling’i tek standarda birleştirmek.

## State Model
- `error_code`: `INVALID_CREDENTIALS | RATE_LIMITED | UNKNOWN`
- `retry_after_seconds`: number | null

## Render Kuralları
- 401 → banner: **“E-posta veya şifre hatalı”**
- 429 → banner: **“Çok fazla deneme yaptınız. 15 dakika sonra tekrar deneyin.”**
  - `retry_after_seconds` varsa yaklaşık dakika: `ceil(retry_after_seconds/60)`
  - alt metin: “Güvenlik nedeniyle geçici olarak engellendi.”

## Controlled Error
- 500/unknown → banner: `t('login_error')` veya “Giriş başarısız. Lütfen tekrar deneyin.”
- Toast kullanılmaz.

## CTA
- “Şifremi unuttum” tüm login ekranlarında gösterilir.
- “Hesap kilitlendi mi?” sadece RATE_LIMITED durumunda gösterilir.
