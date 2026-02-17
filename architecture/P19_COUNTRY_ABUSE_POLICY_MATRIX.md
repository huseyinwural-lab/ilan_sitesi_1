# P19 Country Abuse Policy Matrix (v1)

**Amaç:** Fraud ve Abuse kurallarını ülke risk profiline göre özelleştirmek.

## 1. Risk Skorlama (Risk Scoring)

| Kural | TR (Default) | DE (Low Risk) | FR (Medium) | High Risk Countries |
| :--- | :--- | :--- | :--- | :--- |
| **Max Accounts per Device** | 3 | 5 | 3 | 1 |
| **Referral Reward Wait** | 14 Gün | 7 Gün | 14 Gün | 30 Gün |
| **Stripe 3DS Force** | Auto | Auto | Auto | Always |

## 2. Teknik Uygulama
*   `AbuseService` içine `country_code` parametresi eklenir.
*   Limitler hardcoded değil, `CountrySettings` (DB veya Config) üzerinden okunur.

## 3. Aksiyonlar
*   **Suspicious Signup:** TR için SMS onayı zorunlu olabilir (Future). DE için Email yeterli.
*   **Payout:** High Risk ülkeler için manuel onay.
