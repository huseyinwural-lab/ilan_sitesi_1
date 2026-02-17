# CHECK_MODERATION_WORKSPACE

## Amaç
Moderation Workspace’in form ekranı değil, workflow ekranı olup olmadığını kontrol etmek.

## Mevcut Durum
- UI dosyası: `/app/frontend/src/pages/ModerationQueue.js`
- Ancak App.js’de route bağlı değil (gap).
- Backend’de moderation endpoint’leri server.py’da görünmüyor (gap).

## Kontroller

### Queue ayrımı (Individual vs Dealer)
- [ ] Queue ayrımı: **INDIVIDUAL / DEALER** var mı? (yoksa gap)
- [ ] Dealer ticari panel var mı? (yoksa gap)

### Aksiyon standardı
- [ ] Aksiyonlar: **Onay / Red / Düzeltme** var mı? (yoksa gap)
- [ ] Red reason enum zorunlu mu? (yoksa gap)
- [ ] Düzeltme reason enum zorunlu mu? (yoksa gap)

### Denetim / Audit
- [ ] Audit log: tüm aksiyonlar zorunlu mu? (yoksa gap)
- [ ] Önceki karar geçmişi var mı?

### Workflow ergonomisi
- [ ] Risk skoru gösteriliyor mu?
- [ ] Foto büyük inceleme var mı?
- [ ] Onay/Red hızlı mı?
- [ ] Batch action var mı? (yoksa gap)
- [ ] Workflow ekranı mı gerçekten?

## Ön Karar
- Moderation Workspace: FAIL (route + backend yok)
- Ek Gap: Individual/Dealer queue ayrımı, aksiyon standardı (approve/reject/request-fix), reason enum ve audit zorunluluğu tanımlı değil.
