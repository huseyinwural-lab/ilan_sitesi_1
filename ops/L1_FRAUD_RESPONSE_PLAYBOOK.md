# Fraud Response Playbook

## 1. Scenario: Spam Attack
**Symptoms**:
*   Hundreds of listings created in < 1 hour.
*   Same title/description or nonsensical text.
*   Multiple accounts from same IP range.

**Response**:
1.  **Block IP**: Add IP to firewall / Rate Limit blacklist.
2.  **Suspend Accounts**: `UPDATE users SET is_active=false WHERE id IN (...)`.
3.  **Bulk Delete**: `UPDATE listings SET status='deleted' WHERE user_id IN (...)`.
4.  **Harden**: Increase Rate Limit on `POST /listings`.

## 2. Scenario: Scraping
**Symptoms**:
*   Single IP requesting > 1000 Detail Pages or Reveals per hour.

**Response**:
1.  **Throttling**: 429 Too Many Requests triggers automatically (P20).
2.  **Captcha**: Enable ReCaptcha for that IP (Manual toggle for MVP).
3.  **Legal**: If competitor, log IP for legal action (Cease & Desist).

## 3. Scenario: Fake Dealer
**Symptoms**:
*   Dealer uploading "Too good to be true" prices.
*   Asking for deposit via WhatsApp.

**Response**:
1.  **Immediate Suspension**: `dealers.status = 'suspended'`.
2.  **Audit**: Check `DealerProfile` verification docs.
3.  **Refund**: If Escrow used, freeze funds and refund buyers.
