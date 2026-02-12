# Security Penetration Test Plan (v1)

**Target:** Rate Limiter & Admin Panel
**Tester:** Internal Security Team / 3rd Party

## 1. Rate Limit Bypass Tests
-   [ ] **IP Rotation:** Attack `/auth/login` using a proxy pool. Verify if limits trigger.
-   [ ] **Header Spoofing:** Send `X-Forwarded-For: 127.0.0.1`. Verify if system trusts it (Should NOT).
-   [ ] **Distributed User:** Log in same user from 10 different IPs. Check User-Tier limit enforcement.

## 2. Admin Privilege Escalation
-   [ ] **IDOR:** Attempt to call `PATCH /api/admin/dealers/{id}/tier` as a Standard Dealer token.
-   [ ] **Abuse Override:** Try to inject negative numbers or SQL into the Limit Override field.

## 3. Pricing Integrity
-   [ ] **Payload Tampering:** Send `price: 0.01` in Listing Create body. Verify system ignores it and uses Server Calculation.
-   [ ] **Currency Mismatch:** Try to send `currency: USD` for `DE`. Verify 400/409.

## 4. Logging & Audit
-   [ ] **Log Flooding:** Send massive payloads to see if logs truncate sensitive data.
-   [ ] **Audit Bypass:** Perform critical action (Tier Change) and verify DB `audit_logs` entry exists.
