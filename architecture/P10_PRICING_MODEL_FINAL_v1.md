# P10 Pricing Model & Logic

**Document ID:** P10_PRICING_MODEL_FINAL_v1  
**Date:** 2026-02-13  
**Status:** 🔒 FROZEN  

---

## 1. User Segments

### 1.1. Individual (Bireysel)
- **Model:** Freemium.
- **Free Limit:** 3 active listings / year (Global).
- **Overage:** Pay-per-listing (e.g., 50 TL / listing).
- **Premium Features:** Available for purchase individually.

### 1.2. Dealer (Kurumsal)
- **Model:** Subscription Only.
- **Tiers:**
  - **Basic:** 10 Listings (500 TL/mo)
  - **Pro:** 50 Listings + 5 Showcase (2000 TL/mo)
  - **Enterprise:** 500 Listings + 20 Showcase (15000 TL/mo)
- **Overage:** Not allowed (Must upgrade tier or buy Booster Pack).

---

## 2. Pricing Configuration

### 2.1. Price Table (DB Driven)
Pricing logic is dynamic based on `Country` + `Module` + `UserType`.

| Rule ID | Country | Module | Segment | Type | Price | Currency |
|---|---|---|---|---|---|---|
| P-001 | TR | Vehicle | Individual | Listing | 150.00 | TRY |
| P-002 | TR | Vehicle | Dealer | Package_Basic | 1000.00 | TRY |
| P-003 | DE | Vehicle | Individual | Listing | 15.00 | EUR |

### 2.2. Discount Logic
- **Promotional Codes:** Valid for specific timeframe/segment.
- **Bulk Discount:** Admin override for Enterprise deals.

---

## 3. Subscription Lifecycle
1. **Created:** Pending payment.
2. **Active:** Payment confirmed, quotas applied.
3. **Past Due:** Payment failed, quotas restricted (grace period 3 days).
4. **Cancelled/Expired:** Quotas revoked, listings > free_limit deactivated.

---

## 4. Quota Definition
Quotas are tracked per feature.

- `listing_limit`: Max active listings.
- `showcase_limit`: Max concurrent showcase items.
- `bump_limit`: Monthly bump rights.
