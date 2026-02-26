# PROFILE_ENDPOINT_FIX_EVIDENCE

**Tarih:** 2026-02-21
**Base URL:** https://theme-config-api.preview.emergentagent.com

## CURL Denemeleri

### 1) Login (consumer)
```
curl -X POST https://theme-config-api.preview.emergentagent.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@platform.com","password":"User123!"}'
```
**Sonuç:** 520 (Cloudflare: Web server is returning an unknown error)

### 2) Login (dealer)
```
curl -X POST https://theme-config-api.preview.emergentagent.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"dealer@platform.com","password":"Dealer123!"}'
```
**Sonuç:** 520 (Cloudflare: Web server is returning an unknown error)

## Not
Preview ortamında origin backend erişimi 520 hatası veriyor. Bu nedenle `/api/v1/users/me/profile` çağrıları için token üretimi ve 200 doğrulaması **şu an mümkün değil**. 

**Aksiyon:** Preview ortamında DATABASE_URL/SQL servis erişimi sağlandığında curl doğrulaması yeniden yapılmalı.
