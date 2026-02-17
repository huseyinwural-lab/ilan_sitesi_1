# ADMIN_COUNTRY_CONTEXT_V2_ACCEPTANCE_GATE

## Kabul Kriterleri
1) URL deterministik
- Country mode’da tüm admin sayfaları ?country=XX taşır
- Global mode’da param yok

2) Backend enforcement aktif
- Invalid country => 400
- Scope dışı => 403

3) RBAC country kısıtı çalışıyor
- country_admin sadece allowed ülkelere erişebilir

4) Redirect/fallback doğru
- Country mode’a geçişte last_selected kullanılır

5) Audit log country-aware
- Admin write işlemlerinde mode+country_scope loglanır

## Kanıt
- curl çıktıları
- Frontend E2E raporu
- Dokümanlar
