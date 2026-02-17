# P16 Webhook Replay Validation (v1)

**Test:** Stripe webhooklarının mükerrer gönderilmesi (Replay Attack / Network Retry).
**Hedef:** Sistem `Idempotency` prensibine uymalıdır. Aynı olay (Event ID) ikinci kez işlenmemeli, Ledger'da çift kayıt (Double Debit) oluşmamalıdır.

## Test Senaryosu
1.  **Simülasyon:** `evt_refund_test_123` ID'li bir `charge.refunded` olayı gönderilir.
2.  **İlk İşlem:**
    *   Ödül `confirmed` -> `revoked`.
    *   Ledger `DEBIT` kaydı atılır.
    *   Stripe Customer Balance güncellenir.
    *   `stripe_events` tablosuna kayıt atılır.
3.  **İkinci İşlem (Replay):**
    *   Aynı ID'li olay tekrar gönderilir.
    *   Sistem `stripe_events` tablosunda ID'yi bulur.
    *   İşlem yapmadan `200 OK` döner (Already processed).
    *   Ledger'da yeni kayıt oluşmaz.

**Sonuç:** BAŞARILI (Code verification: `stripe_service.py` -> `handle_webhook` -> Unique Constraint Check).
