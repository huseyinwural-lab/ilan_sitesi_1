# Individual User Supply Funnel

## 1. Funnel Stages

### Stage 1: Acquisition (Traffic)
*   **Source**: SEO Landing Pages (P29), Social Shares.
*   **CTA**: "Ücretsiz İlan Ver" (Primary Header Button).

### Stage 2: Activation (First Listing)
*   **Barrier**: Registration friction.
*   **Solution**: Allow "Guest Draft" (Create listing first, register to publish).
*   **Metric**: `guest_draft_created` -> `user_registered` conversion.

### Stage 3: Engagement (Publishing)
*   **Barrier**: Photo upload fatigue, Description writing block.
*   **Solution**: AI Description Generator (P21 feature to enable), Simple Wizard (U2.2).

### Stage 4: Retention (Second Listing)
*   **Trigger**: First listing expires or gets a lead.
*   **Action**: Email "Your listing is popular! Post another?".

## 2. Tracking Plan
We track the `user_journey` via `growth_events` table (P18).
*   `funnel_step_completed`: {step: 1, name: "signup"}
*   `funnel_step_completed`: {step: 2, name: "draft_created"}
*   `funnel_step_completed`: {step: 3, name: "published"}
