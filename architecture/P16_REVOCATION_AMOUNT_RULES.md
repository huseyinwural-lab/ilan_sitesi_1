# P16 Revocation Amount Rules (v1)

**Kapsam:** İade durumunda geri alınacak ödül miktarının hesaplanması.

## 1. Tam İade (Full Refund)
*   **Senaryo:** Ödemenin tamamı iade edildi (`charge.refunded` -> `amount == amount_refunded`).
*   **Kural:** Ödülün **TAMAMI** geri alınır.
*   `Debit Amount = Reward Amount`

## 2. Kısmi İade (Partial Refund)
*   **Senaryo:** Ödemenin bir kısmı iade edildi (Örn: 100 EUR ödendi, 50 EUR iade).
*   **Kural:** Ödül, iade oranı kadar geri alınır (Pro-rata).
*   **Formül:** `Debit = Reward * (Refunded Amount / Total Charge Amount)`
*   **Örnek:**
    *   Reward: 100 TRY
    *   Charge: 1000 TRY
    *   Refund: 200 TRY (%20)
    *   Debit: 100 * 0.20 = 20 TRY.

## 3. Yuvarlama (Rounding)
*   Hesaplamalar Decimal tipinde yapılır.
*   Sonuç **2 ondalık basamağa** yuvarlanır (Half-Up).
*   `Debit` tutarı asla `Reward` tutarını aşamaz (`min(Calculated, Reward)`).

## 4. Minimum Tutar
*   Eğer hesaplanan debit tutarı 0.01'den küçükse işlem yapılmaz (Gereksiz ledger kaydı önlenir).
