# SPRINT_PREVIEW_ADMIN_E2E_EVIDENCE

**Tarih:** 2026-02-22 19:14:00 UTC
**Ticket ID:** #1
**SLA:** 24 saat
**Target resolution:** 23 Feb 2026
**Durum:** PASS

## Admin Login
```
POST /api/auth/login (admin@platform.com)
```
Sonuç: **200 OK** (token alındı)

## Moderation Queue
```
GET /api/admin/moderation/queue
```
Sonuç: **1 ilan** listelendi (pending_moderation)

## Approve Akışı
```
POST /api/admin/listings/{listing_id}/approve
```
Sonuç: `status=published`
