# P18 Growth Event Taxonomy (v1)

**Amaç:** Büyüme ve gelir verilerini tek bir merkezde toplamak.

## Event Tipleri
*   `user_registered`: Yeni üye kaydı. (Metadata: source, ref_code)
*   `subscription_started`: Checkout başladı.
*   `subscription_confirmed`: Ödeme başarılı. (Metadata: amount, plan)
*   `affiliate_click`: Partner linki tıklandı.
*   `referral_generated`: Yeni bir davet kodu ile üye geldi.

## Tablo Yapısı (`growth_events`)
*   `event_type`: String (Index)
*   `user_id`: UUID (Nullable)
*   `affiliate_id`: UUID (Nullable)
*   `event_data`: JSON
*   `created_at`: Datetime
