# P26: Messaging Monetization Strategy

## 1. Premium Message Priority
In a crowded Inbox (e.g., popular car dealer), messages from Premium Listings or Verified Buyers should appear at the top.

### 1.1. Logic
*   **Inbox Sort Order**:
    1.  `is_premium_sender` (True) OR `is_premium_listing` (True) -> Top.
    2.  `last_message_at` DESC.

### 1.2. Implementation
Modify `get_inbox` query to JOIN with `listings` and `users` to determine priority.

## 2. Paid Message Boost (Highlight)
Allow buyers to pay small fee to highlight their message.
*   **Action**: `POST /messages/boost/{conversation_id}`.
*   **Cost**: $1.00.
*   **Effect**: Adds `is_highlighted=True` flag to Conversation.

## 3. Dealer Messaging Dashboard
Expand the Analytics dashboard to include response metrics.
*   **Metrics**:
    *   Response Rate (%).
    *   Avg Response Time (minutes).
    *   Unanswered Threads Count.
