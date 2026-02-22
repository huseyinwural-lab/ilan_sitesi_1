# SPRINT1_PREVIEW_E2E_EVIDENCE

**Tarih:** 2026-02-22 19:35:00 UTC
**Ticket ID:** #1
**SLA:** 24 saat
**Target resolution:** 23 Feb 2026
**Durum:** PARTIAL PASS

## Consumer Login + Profile
- POST /api/auth/login (user@platform.com) → 200 OK
- GET /api/v1/users/me/profile → 200 OK (consumer profile döndü)

## Dealer Login + Profile
- POST /api/auth/login (dealer@platform.com) → 200 OK
- GET /api/v1/users/me/dealer-profile → 200 OK (dealer profile döndü)

## Not
GDPR export / soft delete / honeypot kanıtları sonraki adımda doğrulanacak.
