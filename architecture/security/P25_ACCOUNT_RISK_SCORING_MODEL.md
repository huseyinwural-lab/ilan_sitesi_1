# P25: Account Risk Scoring Model

## 1. Score Calculation (0-100)
`Score = Base + (Age_Weight * Age) + (Verif_Weight * Verification) - (Report_Weight * Reports)`

*   **New Account (< 24h)**: +50 Risk.
*   **Phone Verified**: -30 Risk.
*   **Email Verified**: -10 Risk.
*   **IP Country Mismatch**: +20 Risk.
*   **Reported by Others**: +40 Risk (per report).

## 2. Actions
*   **Score > 80**: Auto-Suspend.
*   **Score > 60**: Listings go to "Manual Moderation" (Pending).
*   **Score < 20**: Trusted (Instant Publish).
