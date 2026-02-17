# LOGIN_RESPONSE_CONTRACT_V1

## Amaç
Backend → Frontend login error response contract’ini sabitlemek.

## 401
### HTTP
- Status: **401**
### Body
```json
{ "code": "INVALID_CREDENTIALS" }
```

## 429
### HTTP
- Status: **429**
### Body
```json
{ "code": "RATE_LIMITED", "retry_after_seconds": 900 }
```

## Notlar
- `detail` alanı geriye uyumluluk için kalabilir; ancak UI temel kararını `code` alanı ile verir.
- `retry_after_seconds` yoksa UI 15 dk sabit mesajı gösterir.
