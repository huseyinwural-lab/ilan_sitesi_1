# LOGIN_SECURITY_UI_STANDARD_V1

## Amaç
Tüm login yüzeylerinde (Public `/login`, Dealer `/dealer/login`, Admin `/admin/login`) güvenlik kaynaklı error state’leri aynı UX standardına bağlamak.

## Genel Kural
- Error mesajları **toast** değil, formun üstünde **kalıcı (persist) banner** olarak gösterilir.
- 401 ve 429 **ayrı** ele alınır; aynı mesaj kullanılmaz.
- 500/unknown error durumunda “sistem hatası”na düşmeden **controlled** bir hata mesajı gösterilir.

## Banner Yerleşimi
- Login form içinde, submit butonunun üstünde.
- `data-testid="login-error"`

## Error Mesajları
### 401 (INVALID_CREDENTIALS)
- Metin: **“E-posta veya şifre hatalı”**
- CTA:
  - “Şifremi unuttum” linki (opsiyonel ama önerilir) → v1.0.0’da her ekranda gösterilebilir.

### 429 (RATE_LIMITED)
- Metin: **“Çok fazla deneme yaptınız. 15 dakika sonra tekrar deneyin.”**
- Ek açıklama: **“Güvenlik nedeniyle geçici olarak engellendi.”**
- Eğer `retry_after_seconds` varsa: yaklaşık dakika gösterimi (örn. “~14 dk”).
- CTA:
  - “Şifremi unuttum” linki
  - “Hesap kilitlendi mi?” yardımcı linki (FAQ/yardım sayfasına)

## CTA Kuralları
- “Şifremi unuttum” tüm login ekranlarında görünür.
- 429 durumunda CTA alanı zorunlu.
