# P27: Fraud Intelligence (Risk Scoring V2)

## 1. Risk Factors
We calculate a dynamic `risk_score` (0-100) for every user. Higher is riskier.

| Factor | Weight | Detection Logic |
| :--- | :--- | :--- |
| **New Account** | +20 | Created < 7 days ago. |
| **No Verification** | +30 | `is_phone_verified` is False. |
| **Spam Behavior** | +40 | Sending > 10 messages/hour to different users. |
| **Device Reuse** | +50 | Device ID associated with banned accounts. |
| **Bad Rating** | +20 | `rating_avg` < 3.0. |

## 2. Enforcement Policy
| Score | Action | Limitation |
| :--- | :--- | :--- |
| **0-20** | None | Trusted User. |
| **21-60** | Watch | Flagged in Admin Dashboard. |
| **61-80** | Restrict | Max 1 listing, Max 3 messages/day. |
| **81+** | Ban | Account suspended automatically. |

## 3. Implementation
*   **Service**: `RiskEngine`.
*   **Trigger**: On Login, On Message Send, On Listing Post.
*   **Storage**: Score is stored in Redis (`risk:user:{id}`) for fast access, persisted to `users` table periodically.
