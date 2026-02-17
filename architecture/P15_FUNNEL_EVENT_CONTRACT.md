# P15 Funnel Event Contract (v1)

**Amaç:** Dönüşüm ve ödeme eventlerinin veri yapısını standardize etmek.

## 1. checkout_started
*   **Kaynak:** Frontend / API (`POST /checkout`)
*   **Trigger:** Kullanıcı ödeme sayfasına gitmek istediğinde.
*   **Payload:**
    ```json
    {
      "user_id": "uuid",
      "session_id": "string (opsiyonel)",
      "plan_code": "TR_DEALER_PRO",
      "coupon_code": "WELCOME50 (opsiyonel)",
      "referral_code": "REF123 (opsiyonel)",
      "amount": 100.00,
      "currency": "TRY"
    }
    ```

## 2. checkout_completed
*   **Kaynak:** Webhook (`checkout.session.completed` / `invoice.paid`)
*   **Trigger:** Ödeme başarıyla alındığında.
*   **Payload:**
    ```json
    {
      "user_id": "uuid",
      "stripe_checkout_session_id": "cs_test_...",
      "stripe_invoice_id": "in_test_...",
      "amount_paid": 100.00,
      "currency": "TRY",
      "plan_code": "TR_DEALER_PRO"
    }
    ```

## 3. reward_generated
*   **Kaynak:** Backend Logic (`ReferralService`)
*   **Trigger:** İlk başarılı ödeme sonrası.
*   **Payload:**
    ```json
    {
      "referrer_id": "uuid",
      "referee_id": "uuid",
      "reward_amount": 100.00,
      "currency": "TRY",
      "status": "applied"
    }
    ```
