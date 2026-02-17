# P16 Withdraw Guard Validation (v1)

**Test:** Negatif bakiyeli veya riskli bir kullanıcının para çekme denemesi.
**Hedef:** Finansal zarar önleme (Loss Prevention).

## Test Senaryosu
1.  **Hazırlık:**
    *   Kullanıcı A'nın 100 TRY ödülü var (`confirmed`). Ledger Net: +100.
    *   Kullanıcı B'nin 100 TRY ödülü vardı, ancak iade edildi (`revoked`). Ledger Net: 0 (veya -50 eğer önceki çekimden sonra iade olduysa).
2.  **Deneme 1 (Kullanıcı A):**
    *   `withdraw(amount=50)` çağrılır.
    *   `net_balance` (100) >= 50.
    *   Sonuç: **BAŞARILI**.
3.  **Deneme 2 (Kullanıcı B - Negatif Bakiye Simülasyonu):**
    *   Manuel olarak Ledger'a `DEBIT 200` eklenir. Net: -100.
    *   `withdraw(amount=10)` çağrılır.
    *   `net_balance` (-100) < 0.
    *   Sonuç: **REDDEDİLDİ** (Blocking condition).

**Sonuç:** BAŞARILI (Logic verification: `ledger_service.py` -> `can_withdraw`).
