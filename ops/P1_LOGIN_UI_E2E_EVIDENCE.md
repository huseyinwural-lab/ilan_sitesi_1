# P1_LOGIN_UI_E2E_EVIDENCE

## Amaç
FAZ-FINAL-02 (P1) kapsamında login UI rate-limit görünürlüğü ve contract uyumunu kanıtlamak.

## Senaryolar

### A) 401 (Invalid credentials)
- Yanlış şifre ile giriş
- Beklenen:
  - HTTP 401 body: `{ code: "INVALID_CREDENTIALS" }`
  - UI banner: “E-posta veya şifre hatalı”
  - (opsiyonel) “Şifremi unuttum” linki görünür

### B) 429 (Rate limited)
- Aynı kullanıcı/email için 10 dk içinde 3 kez 401
- 4. deneme
- Beklenen:
  - HTTP 429 body: `{ code: "RATE_LIMITED", retry_after_seconds: X }`
  - UI banner: “Çok fazla deneme yaptınız. 15 dakika sonra tekrar deneyin.”
  - Retry-after varsa “~14 dk” gibi yaklaşık süre görünür
  - Alt metin: “Güvenlik nedeniyle geçici olarak engellendi.”
  - CTA’lar:
    - “Şifremi unuttum”
    - “Hesap kilitlendi mi?”

## Kapsam
- Public: `/login`
- Dealer: `/dealer/login`
- Admin: `/admin/login`

## Kanıt
- API response dump (status + body)
- UI screenshot (banner + CTA)
