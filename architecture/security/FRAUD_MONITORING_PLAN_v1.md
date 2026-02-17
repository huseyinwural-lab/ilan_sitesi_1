# Fraud & Abuse Monitoring Plan v1

## 1. Early Warning Signals
We scan for patterns that indicate organized abuse.

### 1.1. Mass Account Creation
*   **Signal**: > 10 signups from same IP in 1 hour.
*   **Action**: Rate Limit IP, Require Captcha.

### 1.2. Lead Farming (Scraping)
*   **Signal**: User reveals > 50 phones/day without sending messages.
*   **Action**: Shadowban (Show fake numbers), Flag for review.

### 1.3. Content Spam
*   **Signal**: Same title/description posted > 5 times across different accounts.
*   **Action**: Auto-reject listings.

## 2. Monitoring Dashboard
*   A dedicated section in Admin Panel.
*   **Metrics**: "High Risk Users", "Blocked Messages", "Rejected Listings Ratio".
