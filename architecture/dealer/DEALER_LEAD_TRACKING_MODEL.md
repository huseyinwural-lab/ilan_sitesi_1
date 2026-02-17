# Dealer Lead Tracking Model

## 1. Objective
To quantify the value provided to the dealer by tracking every potential buyer intent.

## 2. Lead Definition
A "Lead" is created when a user performs a high-intent action on a dealer's listing.

### 2.1. Lead Types
1.  **Message**: User sends an internal message.
2.  **Phone Reveal**: User clicks "Show Number".
3.  **WhatsApp Click**: User clicks "Chat on WhatsApp" (if enabled).

## 3. Data Storage
We use `user_interactions` (P21) as the raw source, but we might need a `dealer_leads` aggregation for faster CRM-like access.

### 3.1. Aggregated View (Virtual)
`SELECT * FROM user_interactions WHERE event_type IN ('message', 'phone_reveal') AND listing.dealer_id = :my_id`

## 4. Attribution
*   **Source**: Organic Search, Paid Boost, External Ref.
*   **Retention**: Leads are kept for 1 year.
