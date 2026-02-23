# Moderation Migration Plan (Post-Search Parity)

## 1) Moderation Tablosu + Status Flow
- listings.status: pending_moderation → approved/rejected/needs_revision
- moderation_actions: approve/reject/suspend/unsuspend
- moderation_queue (SQL): listing_id, status, priority, sla_deadline, created_at

## 2) Parity Test Checklist (Reject/Approve)
- [ ] pending → approved (listing status + audit log)
- [ ] pending → rejected (reason_code + reason_detail + audit log)
- [ ] needs_revision → approved
- [ ] SLA/priority hesaplarının eşleşmesi
- [ ] Moderation queue count parity (Mongo vs Postgres)

## 3) Freeze Window + Rollback
**Freeze Window:**
- Search parity PASS sonrası düşük trafik saatinde write lock
- Moderation write işlemleri read-only moda alınır

**Rollback:**
- Read toggle → Mongo fallback
- Postgres’e yazılan yeni aksiyonlar queue’de tamponlanır
- Hata giderildikten sonra tekrar cutover
