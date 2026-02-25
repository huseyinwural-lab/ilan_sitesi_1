# P1 Cross-Browser Evidence (Manual Checklist)

## Kapsam
- Safari (Mac)
- Firefox (Mac/Win)
- Edge (Win)

## Zorunlu Kontroller
1. Tema toggle (light/dark) + refresh sonrası persistence
2. Header auth dönüşümü (guest -> auth)
3. Footer grid render (public)
4. /bilgi/:slug sayfası
5. Kampanya modal tarih picker (admin)

## Manuel Test Adımları (Checklist)
### Safari (Mac)
- [ ] Home (light) açıldı, header/footer doğru render.
- [ ] Tema toggle ile dark moda geçildi, refresh sonrası persist.
- [ ] /bilgi/:slug sayfası title/description düzgün.
- [ ] Auth login sonrası header aksiyonları görünüyor.

### Firefox (Mac/Win)
- [ ] Home (dark) görünümü stabil.
- [ ] Footer grid içerikleri doğru hizalanıyor.
- [ ] /bilgi/:slug sayfası meta/OG doğrulandı.
- [ ] Kampanya modal tarih picker görünür ve seçilebilir.

### Edge (Win)
- [ ] Tema toggle ve persistence doğrulandı.
- [ ] Footer grid render doğrulandı.
- [ ] Auth header dönüşümü doğrulandı.
- [ ] Kampanya modal tarih picker doğrulandı.

## Zorunlu Screenshot Listesi
- Safari: home-light.png, home-dark.png, info-slug.png
- Firefox: footer-grid.png, auth-header.png, campaign-date-picker.png
- Edge: home-light.png, footer-grid.png, auth-header.png

## Notlar
- Bu ortamda Safari/Firefox/Edge çalıştırılamadığı için kanıtlar manuel sağlanacaktır.
