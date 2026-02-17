# P18 Affiliate Link Tracking (v1)

**Amaç:** `/ref/{slug}` linklerine tıklayan ziyaretçileri takip etmek ve kayıt olduklarında ilgili Affiliate'e bağlamak.

## 1. Redirect Endpoint (`GET /ref/{slug}`)
*   **İşlev:** Gelen isteği karşılar, Affiliate ID'sini bulur ve ana sayfaya (veya hedef sayfaya) yönlendirir.
*   **Cookie:** `aff_ref` adında, değeri `{affiliate_id}` olan bir cookie bırakır.
*   **TTL:** 30 Gün.
*   **Analytics:** `AffiliateClick` tablosuna (async) kayıt atar.

## 2. Attribution Logic (Kayıt Anı)
*   `/auth/register` endpoint'i `aff_ref` çerezini (veya query parametresini) kontrol eder.
*   Eğer cookie varsa ve kullanıcı zaten bir `referral_code` kullanmamışsa, `users.referred_by_affiliate_id` alanına yazar.
*   **Öncelik:** `referral_code` > `aff_ref` cookie. (Arkadaş daveti affiliate'i ezer).

## 3. Commission Logic (Ödül Anı)
*   Mevcut `invoice.paid` webhook handler güncellenir.
*   Eğer ödeyen kullanıcının `referred_by_affiliate_id` alanı doluysa:
    *   Affiliate'in komisyon oranı (`commission_rate`) üzerinden tutar hesaplanır.
    *   `RewardLedger` tablosuna `CREDIT` (Type: `AFFILIATE_COMMISSION`) olarak işlenir.
    *   Affiliate'in Stripe bakiyesine eklenir.
