# Dashboard Widget Spec (UH1.1)

## KPI Kartları (Maks 4)
1. **Yayında İlan Sayısı**
   - Kaynak: `/api/v1/listings/my?status=active&limit=1` → `pagination.total`
2. **Bekleyen İlan Sayısı**
   - Kaynak: `/api/v1/listings/my?status=pending_moderation&limit=1` → `pagination.total`
3. **Favoriye Eklenen İlan Sayısı**
   - Kaynak: `/api/v1/favorites/count` → `count`
4. **Gelen Mesaj Sayısı (30 gün)**
   - Kaynak: `/api/v1/messages/unread-count` (proxy)

## Görsel Kurallar
- Maks 4 kart.
- Renkle değil, ikon + tipografi ile vurgu.
- Değer `0` ise pasif (soluk) görsel state.
- API yoksa: değer `0` + "Veri hazırlanıyor" etiketi.
