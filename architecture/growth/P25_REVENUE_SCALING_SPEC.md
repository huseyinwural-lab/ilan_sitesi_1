# P25: Revenue Scaling & Monetization Expansion

## 1. Affiliate Tier System
To incentivize top performers, we introduce a tiered commission structure.

### 1.1. Tiers
| Tier | Threshold (Referrals) | Commission Bonus | Badge |
| :--- | :--- | :--- | :--- |
| **Bronze** | 0 - 9 | 0% (Standard) | 🥉 |
| **Silver** | 10 - 49 | +5% | 🥈 |
| **Gold** | 50+ | +15% | 🥇 |

### 1.2. Implementation
*   **Storage**: `referral_tiers` table (Already exists from P18).
*   **Logic**: `ReferralService.calculate_commission(user_id, base_amount)`.
*   **Automation**: A daily job checks referral counts and upgrades users automatically.

## 2. Dynamic Boost Pricing (Elasticity)
Instead of fixed pricing for "Boost" products, we apply multipliers based on demand.

### 2.1. Logic
`Final Price = Base Price * Category Multiplier * Location Multiplier`

*   **Config**: `dynamic_pricing_rules` in `SystemConfig`.
*   **Example**:
    *   Istanbul (High Demand): 1.5x
    *   Vehicle (High Value): 2.0x
    *   Result: A €5 boost costs €15 for a Car in Istanbul.

## 3. Dealer Analytics Dashboard
Dealers need ROI visibility to keep spending.

### 3.1. Metrics
*   **Funnel**: Impressions -> Views -> Contacts.
*   **Spend**: Total spent on Premium/Boost.
*   **Performance**: Avg Cost Per Lead (CPL).

### 3.2. Endpoint
`GET /api/v2/dealer/analytics/overview`
