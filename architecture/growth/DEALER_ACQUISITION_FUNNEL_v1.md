# Dealer Acquisition Funnel v1

## 1. Funnel Stages

### Stage 1: Awareness (Top of Funnel)
*   **Source**: Google Search ("Car dealer software"), LinkedIn Ads, Direct Sales.
*   **Landing Page**: `/dealers` (Value Prop: "More Leads, Less Cost").

### Stage 2: Consideration
*   **Pricing Page**: `/dealers/pricing`.
*   **Demo**: View public dealer profiles.

### Stage 3: Conversion (Sign Up)
*   **Action**: `POST /api/v1/user-panel/dealer-onboarding/upgrade`.
*   **Barrier**: Tax ID verification (Pending state).

### Stage 4: Activation (First Value)
*   **Milestone**: First Listing Published.
*   **Milestone**: First Lead Received.

### Stage 5: Retention (Loyalty)
*   **Metric**: Subscription Renewal (Month 2).
*   **Metric**: Usage Frequency (Dashboard logins > 2/week).

## 2. Bottlenecks & Fixes
*   **Drop-off at Verification**: Send email reminders ("Your account is waiting approval").
*   **Drop-off at Payment**: Offer 14-day free trial (Future).
