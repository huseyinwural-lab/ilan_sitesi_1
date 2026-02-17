# PORTAL_SPLIT_V1_EVIDENCE
## Evidence Result (Automated)
- Re-test PASS: No-chunk-load acceptance verified by frontend testing agent.
- Logged-out redirects:
  - /admin/users → /admin/login: backoffice chunk requests = 0
  - /dealer → /dealer/login: dealer chunk requests = 0
- Authorized access:
  - admin → /admin/users: backoffice chunk requested (expected)
  - admin/moderator → /dealer: dealer chunk requests = 0 (expected)



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
