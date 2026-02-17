# P25: Support Automation Plan

## 1. Ticket Categorization (Keyword Based)
*   **"Refund", "Charge"** -> Billing Queue (High Priority).
*   **"Reject", "Pending"** -> Moderation Queue.
*   **"Bug", "Error"** -> Tech Queue.
*   **"Password", "Login"** -> Account Queue.

## 2. Auto-Response (Macros)
If ticket contains "Why is my listing pending?":
*   **Bot Reply**: "Your listing is under review. This usually takes 4-6 hours. Please check our Posting Guidelines."
*   **Status**: Solved (if user doesn't reply).

## 3. SLA Watchdog
*   Cron job checks open tickets > 24h.
*   Alerts Support Lead via Slack.
