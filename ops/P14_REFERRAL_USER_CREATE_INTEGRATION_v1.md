# P14 Referral User Create Integration (v1)

**Kapsam:** `/auth/register` Endpoint Güncellemesi

## Akış
1.  **Kod Üretimi:** Her yeni kullanıcı için `users.referral_code` otomatik üretilir (Random 8-char string, Unique).
2.  **Attribution:** Request payload'da `referral_code` varsa:
    *   Kod `users` tablosunda aranır.
    *   Bulunursa `referrer_id` alınır.
    *   Bulunamazsa `400` hatası fırlatılır.
3.  **Kayıt:** Yeni kullanıcı `referred_by` alanı ile kaydedilir.

## Kodlama Planı
*   `server.py` içindeki `register` endpoint'i güncellenecek.
*   `app/services/referral_service.py` oluşturulacak (Kod üretimi ve validasyon için).
