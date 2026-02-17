# FAZ-L1: Reveal CTA A/B Test Plan

## 1. Hypothesis
Changing the "Show Phone" button design/position will increase the conversion rate (View -> Lead).

## 2. Test Variants

### Variant A (Control)
*   **Text**: "Show Phone Number"
*   **Color**: Green (Standard Success)
*   **Location**: Sidebar (Desktop), Bottom Sticky (Mobile)
*   **Icon**: Phone handset.

### Variant B (Urgency)
*   **Text**: "Contact Seller Now"
*   **Color**: Blue (Primary Brand)
*   **Location**: Same.
*   **Addition**: "Usually replies in 1 hour" text below button.

## 3. Metrics
*   **Primary**: Click-Through Rate (CTR) on the button.
*   **Secondary**: Percentage of users who *copy* the number (if tracking available) or click "Call".

## 4. Execution
*   **Traffic Split**: 50/50 randomized by Session ID.
*   **Duration**: 2 weeks or 1,000 sessions.
*   **Tracking**: P22 Experiment Logs (`experiment_name='reveal_cta_v1'`).
