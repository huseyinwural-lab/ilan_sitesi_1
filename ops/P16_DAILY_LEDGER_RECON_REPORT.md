# P16 Daily Ledger Reconciliation Report (v1)

**Kapsam:** İç Muhasebe (Ledger) ve Dış Ödeme Sağlayıcı (Stripe) Tutarlılığı

## 1. Mutabakat Denklemi
Her gün saat 03:00'da çalışacak `audit_ledger.py` scripti şu eşitliği kontrol eder:

**Internal Ledger Sum** == **Stripe Customer Balance**

*   `Internal Ledger Sum`: `SUM(amount)` WHERE `user_id = X` (Credits are negative in Stripe logic usually, but here we map: Credit -> Negative Stripe Balance).
*   **Not:** Stripe Customer Balance'da **Negatif** değer, işletmenin müşteriye borcu olduğunu (Kredi) gösterir. Bizim Ledger'da **CREDIT** pozitiftir.
*   **Denklem:** `Internal Ledger (Credit - Debit)` == `ABS(Stripe Balance)` (Eğer Stripe Balance < 0 ise).

## 2. Rapor Formatı

### Özet
*   **Total Users Checked:** 1540
*   **Fully Reconciled:** 1538 (%99.9)
*   **Mismatch Found:** 2

### Mismatch Detayı
| User ID | Internal Net | Stripe Balance | Fark | Olası Neden |
| :--- | :--- | :--- | :--- | :--- |
| `u_123` | 100.00 TRY | -80.00 TRY | 20.00 | Manuel Stripe müdahalesi veya senkronizasyon hatası. |

## 3. Aksiyonlar
*   Fark < 1 TRY (Kur farkı/Yuvarlama): Yoksay (Auto-adjust opsiyonel).
*   Fark > 1 TRY: "Financial Alert" tetikle -> Ops ekibine Ticket aç.
