## Sprint 6 — Audit Exception Note

### Event: `UNAUTHORIZED_ROLE_CHANGE_ATTEMPT`
- Rol değişim endpoint’i **/api/users/{id}** sadece `super_admin` için `check_permissions` ile korunur.
- Yetkisiz roller request’i **dependency seviyesinde** 403 ile kesildiği için handler çalışmaz.
- Bu nedenle `UNAUTHORIZED_ROLE_CHANGE_ATTEMPT` event’i **sistematik olarak üretilemez** (handler’a düşmeyen request için audit yazımı yok).

### Doğrulama (teknik)
- Yetkisiz token ile `PATCH /api/users/{id}` → **403**
- Audit log’da ilgili event gözlemlenmez.

### Önerilen İyileştirme (opsiyonel)
- Guard seviyesinde (middleware / dependency) `UNAUTHORIZED_ROLE_CHANGE_ATTEMPT` log eklenebilir.
