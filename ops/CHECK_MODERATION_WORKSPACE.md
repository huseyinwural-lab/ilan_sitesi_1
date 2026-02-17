# CHECK_MODERATION_WORKSPACE

## Amaç
Moderation Workspace’in form ekranı değil, workflow ekranı olup olmadığını kontrol etmek.

## Mevcut Durum
- UI dosyası: `/app/frontend/src/pages/ModerationQueue.js`
- Ancak App.js’de route bağlı değil (gap).
- Backend’de moderation endpoint’leri server.py’da görünmüyor (gap).

## Kontroller
- [ ] Queue katmanları ayrılmış mı?
- [ ] Risk skoru gösteriliyor mu?
- [ ] Foto büyük inceleme var mı?
- [ ] Onay/Red hızlı mı?
- [ ] Batch action var mı? (yoksa gap)
- [ ] Önceki karar geçmişi var mı?
- [ ] Workflow ekranı mı gerçekten?

## Ön Karar
- Moderation Workspace: FAIL (route + backend yok)
