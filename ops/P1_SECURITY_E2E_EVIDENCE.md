# P1_SECURITY_E2E_EVIDENCE

## Ek Kanıt — Login UI (401/429)
- Doküman: `/app/ops/P1_LOGIN_UI_E2E_EVIDENCE.md`
- Public `/login`, Dealer `/dealer/login`, Admin `/admin/login` ekranlarında:
  - 401 banner + “Şifremi unuttum” doğrulandı
  - 429 banner + retry-after + “Hesap kilitlendi mi?” doğrulandı


## Amaç
FAZ-FINAL-02 (P1) güvenlik/yetki audit kapsamı için negatif test kanıt paketi.

## Senaryolar

### 1) Failed login 3 kez
- Yanlış şifre ile 3 deneme
- Beklenen:
  - 3 adet `FAILED_LOGIN` audit

### 2) Rate-limit tetiklenmesi
- Aynı pencere içinde 4. deneme
- Beklenen:
  - HTTP 429
  - 1 adet `RATE_LIMIT_BLOCK` audit (blok başlangıcında)
  - Blok süresince tekrar tekrar RATE_LIMIT_BLOCK yazılmaz

### 3) Admin role change
- Admin panelden bir kullanıcı rolünü değiştir
- Beklenen:
  - `ADMIN_ROLE_CHANGE` audit
  - previous_role / new_role doğru

### 4) Scope dışı role change denemesi
- `country_admin` rolü ile scope dışı kullanıcıya role change dene
- Beklenen:
  - HTTP 403
  - `UNAUTHORIZED_ROLE_CHANGE_ATTEMPT` audit

## Kanıt Önerisi
- curl çıktıları (status code + response)
- `audit_logs` örnek kayıtları (alanlar dolu)
- Admin UI ekran görüntüleri (audit-logs filtreleri)
