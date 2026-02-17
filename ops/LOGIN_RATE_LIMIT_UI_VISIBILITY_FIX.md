# LOGIN_RATE_LIMIT_UI_VISIBILITY_FIX

## Amaç
429 (rate-limit) durumunda kullanıcıya mesajın **kalıcı** ve **deterministik** şekilde görünmesini sağlamak.

## Kural
- Toast/snackbar kullanılmaz.
- Login form içinde kalıcı banner kullanılır.

## Mesaj
- 429 banner metni: **“Çok fazla deneme yaptınız. 15 dakika sonra tekrar deneyin.”**
- Alt açıklama: **“Güvenlik nedeniyle geçici olarak engellendi.”**
- `retry_after_seconds` varsa “~X dk” gösterimi.

## Ayrıştırma
- 401 → “E-posta veya şifre hatalı”
- 429 → rate-limit mesajı
- Unknown → controlled generic mesaj
