# P7 Admin Abuse Investigation Panel

**Component:** Admin Panel > Security > Abuse Watch

## 1. Search & Filter
-   **Input:** IP Address or User ID.
-   **Output:** History of Blocked Requests, Login Failures, and Tier violations.

## 2. Suspicious Timeline
-   Visual timeline showing spikes in traffic vs Limit.
-   Highlights: "Bot-like behavior" (e.g., constant 61 req/min).

## 3. Manual Override (Emergency)
-   **UI:** "Whitelisting / Override" Section.
-   **Action:** Set Temporary Limit.
-   **Backend:** `SET rl:override:{user_id} {limit} EX {ttl}`.
-   **Audit:** Mandatory "Reason" field input.

## 4. Analysis Features
-   **Filter by Tier:** "Show me all PREMIUM dealers getting blocked".
-   **Filter by Endpoint:** "Who is spamming /auth/login?".
