# Hard Launch Go-Live Approval

## 1. Infrastructure
- [ ] **DNS**: `platform.com` resolves to Load Balancer IP.
- [ ] **SSL**: Certificate valid, HSTS enabled.
- [ ] **CDN**: Static assets serving from Edge.
- [ ] **Database**: Primary/Replica sync healthy.

## 2. Security
- [ ] **Rate Limiting**: Enabled on `/search` and `/reveal`.
- [ ] **WAF**: Web Application Firewall active (Block suspicious IPs).
- [ ] **Secrets**: No hardcoded keys in frontend bundle.

## 3. Analytics
- [ ] **GTM**: Container loaded.
- [ ] **Backend Events**: `UserInteraction` table receiving rows.
- [ ] **Error Tracking**: Sentry/Datadog active.

## 4. Feature Flags
- [ ] `MONETIZATION_FREE_MODE`: **ON** (For launch).
- [ ] `ML_RANKING`: **ON** (Group B).
- [ ] `NEW_WIZARD`: **ON**.

## 5. Sign-Off
*   **CTO**: Approved.
*   **Product Lead**: Approved.
*   **Ops Lead**: Approved.
