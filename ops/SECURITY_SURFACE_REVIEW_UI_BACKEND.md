# SECURITY_SURFACE_REVIEW_UI_BACKEND

## Amaç
UI + backend güvenlik yüzeyi ön kontrolü (kurumsal).

## 1) Auth Brute Force Koruması
- [ ] Login rate limit var mı? (backend)
- [ ] Yanlış parola denemeleri lockout var mı?

## 2) Rate Limit
- [ ] login
- [ ] message
- [ ] reveal phone
- [ ] upload

## 3) PII Leakage
- [ ] Public listing listelerinde email/telefon sızıyor mu?
- [ ] Listing detail PII minimizasyonu
- [ ] Admin listelerinde gereksiz PII var mı?

## 3.1) Moderation Audit (Kritik)
- [ ] Moderation state change event’leri audit log’a düşüyor mu?
- [ ] Red/Düzeltme reason tam mı? (boş reason engeli var mı?)

## 4) Draft Media Erişim
- [ ] Draft medya public erişilebilir mi?
- [ ] Media preview URL auth ister mi?

## 5) CSRF / CORS
- [ ] CORS politika
- [ ] CSRF (cookie tabanlı auth yoksa düşük risk)

## 6) Upload Güvenliği
- [ ] content-type doğrulama
- [ ] boyut limiti
- [ ] path traversal

## Ön Karar (repo gözlem)
- Rate limit: FAIL (görünür implementasyon yok)
- Draft media: PARTIAL (backend guard kontrol edilmeli)
- PII: PARTIAL (DetailPage mock reveal)
