# P16 Stripe Event to Reward Actions (v1)

**Kapsam:** Stripe Olaylarına Karşı Sistem Davranış Matrisi

## 1. Charge Refunded (`charge.refunded`)

*   **Tetikleyici:** Ödeme iade edildi.
*   **Reward Statüsü:**
    *   `Pending` -> `Revoked`
    *   `Confirmed` -> `Revoked`
    *   `Revoked` -> İşlem yok (Idempotent).
*   **Ledger (Defter) İşlemi:**
    *   `DEBIT` kaydı oluşturulur.
    *   Tutar: İade edilen tutar ile orantılı (Full refund ise tam reward, Partial ise oranlı).
*   **Stripe Balance:**
    *   Kullanıcının Stripe Customer Balance hesabına "Pozitif Bakiye" (Borç) eklenir veya mevcut kredi düşülür.

## 2. Charge Dispute Created (`charge.dispute.created`)

*   **Tetikleyici:** İtiraz süreci başladı.
*   **Reward Statüsü:** Değişmez (Pending veya Confirmed kalır).
*   **Aksiyon:**
    *   Audit loguna "DISPUTE_RISK" kaydı atılır.
    *   Admin panelinde ilgili reward "At Risk" flag'i ile gösterilir (UI Backlog).
    *   Payout (Withdraw) mekanizması varsa, bu tutar "Blocked" bakiyeye alınır.

## 3. Charge Dispute Closed (`charge.dispute.closed`)

*   **Tetikleyici:** İtiraz sonuçlandı.
*   **Koşul:** `event.data.object.status` == `lost`.
*   **Reward Statüsü:**
    *   `Pending/Confirmed` -> `Revoked`
*   **Ledger İşlemi:**
    *   `DEBIT` kaydı oluşturulur (Tutar: Reward Amount - Dispute sırasında zaten refund yapılmışsa double count önlenir).
*   **Koşul:** `event.data.object.status` == `won`.
*   **Aksiyon:** Risk flag'i kaldırılır.

## 4. Özet Tablo

| Event | Reward Status (Current) | New Status | Ledger Action | Not |
| :--- | :--- | :--- | :--- | :--- |
| `charge.refunded` | Pending | Revoked | None (Henüz verilmedi) | Pending ödülün bakiyesi zaten blokajlıdır. |
| `charge.refunded` | Confirmed | Revoked | Debit | Bakiye düşülür. |
| `dispute.created` | Any | No Change | None | Risk Flag. |
| `dispute.closed (lost)` | Confirmed | Revoked | Debit | Bakiye düşülür. |
