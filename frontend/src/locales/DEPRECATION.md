# Legacy Locale Dosyaları — Deprecate/Read-Only

Bu klasördeki aşağıdaki dosyalar migrasyon süresince **silinmeyecek** ancak **read-only** kabul edilir:

- `tr.json`
- `de.json`
- `fr.json`

## Kurallar

1. Bu dosyalara yeni key eklenmez / içerik değiştirilmez.
2. Uygulama kodunda bu dosyalara import yapılmaz.
3. Yeni i18n geliştirmeleri yalnızca namespace dosyalarına yapılır:
   - `tr/common.json`, `tr/auth.json`, `tr/dealer.json`, `tr/admin.json`
   - `de/*`
   - `fr/*`

## Doğrulama

```bash
node /app/frontend/scripts/check-legacy-locales-deprecated.mjs
```

Bu kontrol CI lint adımına eklenmelidir.
