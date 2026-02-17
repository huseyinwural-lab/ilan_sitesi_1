# PORTAL_GATE_NO_CHUNK_LOAD_ACCEPTANCE

## Kabul Kriterleri (Testlenebilir)

### 1) Wrong role ile /admin/*
- Backoffice chunk request **yok**
- Admin shell DOM mount **yok**
- Davranış:
  - Auth yoksa: 401 → `/admin/login`
  - Auth var ama wrong portal: 403 → kullanıcı default_home redirect

### 2) Wrong role ile /dealer/*
- Dealer chunk request **yok**
- Dealer shell DOM mount **yok**
- Davranış:
  - Auth yoksa: 401 → `/dealer/login`
  - Auth var ama wrong portal: 403 → kullanıcı default_home redirect

### 3) Doğru role
- Sadece ilgili portal chunk yüklenir
- Diğer portal chunk’ları yüklenmez

## Kanıt
- Playwright network request log (chunk js dosyaları)
- Screenshot/DOM assertion
