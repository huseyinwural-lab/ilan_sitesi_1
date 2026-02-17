# ROUTE_NAMESPACE_STANDARD

## Standart

### Public/Individual
- `/`
- `/search`
- `/listing/:id` *(repo şu an `/ilan/:id` kullanıyor; alias/redirect ile standarda geçiş planlanır)*
- `/account/*`
- `/login`

### Dealer
- `/dealer/*`
- `/dealer/login`

### Backoffice
- `/admin/*`
- `/admin/login`

### Opsiyonel (ADS)
- `/moderation/*`
- `/support/*`
- `/analytics/*`

> Bu fazda izolasyon chunk+guard ile sağlanır; route namespace netliği “portal eligibility” ile birlikte enforced edilir.
