# IMPLEMENT_MODERATION_STATE_MACHINE

## Amaç
Moderation state machine’i üretime hazır hale getirmek (v1.0.0 P0 release blocker).

## Kapsam
- Listing submit sonrası ilan **kamuya açılmadan** moderasyon kuyruğuna girer.
- Public sorgular yalnızca **approved/published** statüleri döndürür.

## State’ler (v1.0.0)
- `draft`
- `pending_moderation`
- `approved`
- `rejected`
- `needs_revision`

## Geçişler
1) `draft` → `pending_moderation`
   - Trigger: Submit (user)

2) `pending_moderation` → `approved` (veya yayınlanabilir statü)
   - Trigger: Admin approve

3) `pending_moderation` → `rejected`
   - Trigger: Admin reject (reason zorunlu)

4) `pending_moderation` → `needs_revision`
   - Trigger: Admin needs_revision (reason zorunlu; `other` ise reason_note zorunlu)

## Kabul Kriteri (State Machine)
- Submit sonrası status: `pending_moderation`
- `pending_moderation` ilan public search/detail/media’da görünmez
- Approve sonrası ilan public’da görünür
- Reject / Needs revision sonrası ilan public’da görünmez
