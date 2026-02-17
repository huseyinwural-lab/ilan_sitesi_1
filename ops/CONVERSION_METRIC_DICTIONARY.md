# Conversion Metric Dictionary

## 1. Funnel Definitions

### 1.1. Top of Funnel (Awareness)
*   **Impression**: Listing card appeared in viewport (Search Result).
*   **CTR (Click-Through Rate)**: `Detail Views / Impressions`.

### 1.2. Middle of Funnel (Interest)
*   **Detail View**: User loaded `/ilan/{id}`.
*   **Time on Page**: Dwell time > 10s indicates interest.
*   **Photo Gallery Interaction**: User swiped > 3 photos.

### 1.3. Bottom of Funnel (Intent/Lead)
*   **Reveal Click**: User clicked "Show Phone".
*   **Message Start**: User opened chat window.
*   **Message Sent**: User successfully sent a message.
*   **Conversion Rate**: `(Unique Reveals + Unique Messages) / Unique Detail Views`.

## 2. Implementation
*   **Tracking**: `track_interaction` (P21) handles these events.
*   **Dashboard**: Dealer Dashboard (G1) displays these aggregates.
