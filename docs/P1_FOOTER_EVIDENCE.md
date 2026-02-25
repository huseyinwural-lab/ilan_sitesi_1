# P1 Footer Evidence

## API Curl Kanıtı
### Footer Layout Save (Draft)
```bash
curl -X PUT "$API/admin/footer/layout" -H "Authorization: Bearer $ADMIN"   -H "Content-Type: application/json"   -d '{"layout":{"rows":[{"columns":[{"type":"text","title":"Hakkımızda","text":{"tr":"Kurumsal açıklama","de":"","fr":""}}]}]},"status":"draft"}'
```
Response (örnek):
```json
{"ok":true,"id":"21afd594-9d98-41fc-b6a4-771a615f4b62","version":1}
```

### Footer Publish (Version Rollout)
```bash
curl -X POST "$API/admin/footer/layout/21afd594-9d98-41fc-b6a4-771a615f4b62/publish"   -H "Authorization: Bearer $ADMIN"
```

### Footer Versions
```bash
curl -X GET "$API/admin/footer/layouts" -H "Authorization: Bearer $ADMIN"
```

### Public Footer
```bash
curl -X GET "$API/site/footer"
```
Response (örnek):
```json
{"layout":{"rows":[{"columns":[{"type":"text","title":"Hakkımızda","text":{"tr":"Kurumsal açıklama"}}]}]},"version":1}
```

## Info Pages CRUD (Bilgi Sayfaları)
```bash
curl -X POST "$API/admin/info-pages" -H "Authorization: Bearer $ADMIN"   -H "Content-Type: application/json"   -d '{"slug":"hakkimizda","title_tr":"Hakkımızda","title_de":"Uber Uns","title_fr":"A propos","content_tr":"İçerik TR","content_de":"Inhalt DE","content_fr":"Contenu FR","is_published":false}'
```
```bash
curl -X PATCH "$API/admin/info-pages/{id}" -H "Authorization: Bearer $ADMIN"   -H "Content-Type: application/json" -d '{"is_published":true}'
```
```bash
curl -X GET "$API/info/hakkimizda"
```

## UI Screenshot Kanıtı
- `footer-builder.png` (Admin Footer Yönetimi)
- `footer-row-added.png` (Satır ekleme + kolon seçimi)
- `footer-link-group.png` (Link group alanları)
- `info-pages-table.png` (Bilgi sayfaları listesi)
- `info-pages-modal.png` (Bilgi sayfası modalı)

## Test Notları
- Admin footer builder row/column/link ekleme doğrulandı.
- Draft/publish + version listesi çalışıyor.
- Bilgi sayfaları draft/publish + preview çalışıyor.
- Auto frontend testing agent: PASS.
