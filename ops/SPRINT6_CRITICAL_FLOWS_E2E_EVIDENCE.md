## Sprint 6 — Kritik Akışlar E2E Evidence

### 5.1 Public → Search → Detail
```bash
curl "${BASE}/api/v2/search?country=DE" # pagination.total > 0
curl "${BASE}/api/v1/listings/vehicle/55149ef5-a993-47ce-ac76-c833c09586fe" # status=published
```
**Sonuç:** Public search sonuç veriyor, detail published listing dönüyor.

### 5.2 Individual → Listing Create → Submit → Moderation → Publish
> Individual rolü seed’de yok; support@platform.ch ile doğrulandı.
```bash
# Create listing
POST /api/v1/listings/vehicle (support token)
# media update (DB)
# submit
POST /api/v1/listings/vehicle/f2e572d2-c174-4461-beb7-0438d7e4e626/submit
# approve
POST /api/admin/listings/f2e572d2-c174-4461-beb7-0438d7e4e626/approve
```
**Sonuç:** Submit → approve sonrası public search’te görünür.

### 5.3 Dealer → Listing Create → Submit → Publish
```bash
# Create listing
POST /api/v1/listings/vehicle (dealer token)
# media update (DB)
# submit
POST /api/v1/listings/vehicle/55149ef5-a993-47ce-ac76-c833c09586fe/submit
# approve
POST /api/admin/listings/55149ef5-a993-47ce-ac76-c833c09586fe/approve
```
**Sonuç:** Moderation approve sonrası public search’te görünür.

### 5.4 Report Flow
```bash
POST /api/reports {listing_id, reason}
GET /api/admin/reports?country=DE
POST /api/admin/reports/7cdd1cb3-d107-4dc1-b744-5dbd319a211b/status (in_review → resolved)
```
**Sonuç:** Report admin listte görünür, status change audit log üretir.

### 5.5 Finance Flow
```bash
POST /api/admin/dealers/{dealer_id}/plan
POST /api/admin/invoices
POST /api/admin/invoices/9cc6ba40-3559-4536-a358-eecf58de66a3/status (paid)
GET /api/admin/finance/revenue?country=DE&start_date=2026-02-01T00:00:00+00:00&end_date=2026-02-28T23:59:59+00:00
```
**Sonuç:** Plan assign + invoice paid + revenue endpoint doğrulandı.
