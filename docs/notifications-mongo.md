# Decommission: Notifications (Mongo)

## Kapsam
Mongo tabanlı notification okuma/yazma akışlarının kaldırılması ve SQL tabanlı `notifications` tablosuna geçiş.

## Aşama-1 (Bu Sprint)
- [x] `/api/v1/notifications` endpointleri SQL’e alındı.
- [x] `notifications` Mongo read/write path kaldırıldı (`db.notifications` kullanımı temizlendi).
- [x] Backfill scripti eklendi: `backend/scripts/backfill_notifications.py`.
- [x] Model: `Notification` V1 (source_type/source_id/action_url/payload_json/dedupe_key/read_at/delivered_at).

## Aşama-2 (1 release sonrası)
- [ ] Mongo tarafındaki eski koleksiyon referanslarını tamamen sil.
- [ ] `mongo` + `notification` anahtar kelime araması → 0 sonuç.
- [ ] Backfill raporu ve örnekleme doğrulaması onaylandıktan sonra kalıcı temizlik.

## Doğrulama Checklist
- [ ] `/api/v1/notifications` listesi kullanıcıya ait kayıtları getiriyor.
- [ ] Okundu işaretleme çalışıyor.
- [ ] Yetkisiz erişimde 403.
- [ ] Backfill raporu üretildi ve örneklem doğrulandı.
