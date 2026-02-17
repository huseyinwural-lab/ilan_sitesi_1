# P14 Promotion Execution Order (v1)

**Tarih:** 14 Şubat 2026
**Durum:** KİLİTLENDİ (LOCKED)
**Öncelik:** P0

Bu doküman, P14 Growth & Scale fazının ilk adımı olan "Promotion Engine (Kampanya & Kupon)" sisteminin geliştirme sırasını belirler.

## İcra Sırası (Execution Order)

1.  **DB Migration (Master Data & History)**
    *   `promotions`, `coupons`, `coupon_redemptions` tablolarının oluşturulması.
    *   Unique constraint ve indekslerin tanımlanması.
    *   Çıktı: `/app/architecture/P14_PROMOTION_DB_MIGRATIONS_v1.md`

2.  **Admin CRUD API + Güvenlik**
    *   Kampanya oluşturma, düzenleme ve durdurma.
    *   Kupon kodu üretimi.
    *   Audit log entegrasyonu.
    *   Çıktı: `/app/ops/P14_PROMOTION_ADMIN_API_v1.md`

3.  **Redemption Kuralları (Runtime Logic)**
    *   Kupon doğrulama servisi (`validate_coupon`).
    *   Limit kontrolleri (Tarih, Stok, Kullanıcı Limiti).
    *   Çıktı: `/app/architecture/P14_COUPON_REDEMPTION_POLICY_v1.md`

4.  **Stripe Checkout Entegrasyonu**
    *   Frontend'den gelen kupon kodunun doğrulanması.
    *   Stripe Session'a indirim uygulanması.
    *   Webhook (`checkout.session.completed`) ile redemption kaydı.
    *   Çıktı: `/app/ops/P14_STRIPE_COUPON_APPLY_INTEGRATION_v1.md`

5.  **Test & Validasyon**
    *   Unit testler (Validation logic).
    *   Integration testler (Full flow).
    *   Çıktı: `/app/tests/test_promotion_engine.py`

6.  **Monitoring**
    *   Kupon kullanım metrikleri.
    *   Çıktı: `/app/ops/P14_PROMOTION_MONITORING_v1.md`

7.  **Faz Kapanışı**
    *   Revenue lift analizi (ilk 24 saat).

## Onay
Bu sıralama kilitlenmiştir. Adımlar atlanamaz.
