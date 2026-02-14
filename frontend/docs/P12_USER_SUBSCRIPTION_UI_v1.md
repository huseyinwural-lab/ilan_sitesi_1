# P12 User Subscription UI

**Document ID:** P12_USER_SUBSCRIPTION_UI_v1  
**Date:** 2026-02-13  
**Status:** 🏗️ ARCHITECTURE  

---

## 1. Dashboard Widget
Located in `/admin/dashboard` or `/admin/billing`.

### 1.1. Active State
- **Plan:** "Pro Plan" (Badge: Green)
- **Next Billing:** "12 Mar 2026"
- **Usage:** Progress Bar (12 / 50 Listings)
- **Actions:** "Manage Billing" (Link to Portal), "Upgrade" (Link to Plans).

### 1.2. Free State
- **Plan:** "Free Tier" (Badge: Gray)
- **Usage:** Progress Bar (2 / 3 Listings)
- **CTA:** "Upgrade to Pro for 50 listings!" (Prominent).

### 1.3. Past Due State
- **Banner:** Red alert "Payment Failed. Please update your card."
- **Action:** "Fix Payment" (Link to Portal).

## 2. Billing History
Table showing recent invoices.
- **Date:** 12 Feb 2026
- **Amount:** 2500.00 TL
- **Status:** Paid
- **Invoice:** [Download PDF]
