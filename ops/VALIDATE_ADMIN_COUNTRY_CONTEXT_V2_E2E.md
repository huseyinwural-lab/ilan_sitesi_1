# VALIDATE_ADMIN_COUNTRY_CONTEXT_V2_E2E

## E2E Senaryoları

### 1) Global mode → tüm veriler
- /admin/users (country param yok)
- Beklenen: filtre yok

### 2) Country mode → filtreli veriler
- /admin/users?country=DE
- Beklenen: country_code=DE filtreli

### 3) Deep link
- Direkt /admin/users?country=DE aç
- Beklenen: aynı görünüm, dropdown DE

### 4) Param silinmesi
- Country mode’dayken URL’den `country` sil
- Beklenen: redirect ?country=last_selected

### 5) RBAC restriction
- country_scope=['DE'] olan user ile /admin/users?country=FR
- Beklenen: 403

### 6) Invalid country
- /admin/users?country=ZZ
- Beklenen: 400
