# PORTAL_SPLIT_V1_EVIDENCE

## Kanıt Paketi (Toplanacak)

### Network kanıtı
- Wrong role → ilgili chunk 0 request
  - individual → /admin/* : backoffice chunk yok
  - dealer → /admin/* : backoffice chunk yok
  - admin → /dealer/* : dealer chunk yok

### Doğru rolde
- admin → /admin/* : backoffice chunk yüklenir
- dealer → /dealer/* : dealer chunk yüklenir

### Smoke
- Public: `/` ve `/search` render
- Loginler:
  - `/login`
  - `/dealer/login`
  - `/admin/login`

### Güvenlik
- Prod’da demo credentials DOM’da render değil

### Referans
- Test plan: `/app/tests/PORTAL_SPLIT_SMOKE_TEST_PLAN.md`
