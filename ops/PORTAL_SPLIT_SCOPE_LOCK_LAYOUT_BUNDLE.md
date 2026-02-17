# PORTAL_SPLIT_SCOPE_LOCK_LAYOUT_BUNDLE

## Scope Lock — Portal ayrımı (layout + bundle split)

### Hedef
Tek domain altında **3 portal** için ayrı layout + ayrı bundle (chunk) hedefi:
1) Public/Individual
2) Dealer
3) Backoffice

### Login yüzeyleri
- Public/Individual: `/login`
- Dealer: `/dealer/login`
- Backoffice: `/admin/login`

### Bu fazda “no-refactor” geçersiz
- Bu iş mimari ayrıştırma içerir.

### Yaklaşım (CRA bağlamı)
- **Multi-entry HTML yapılmayacak.**
- Tek entry korunur; portal ayrımı **route-based lazy loading** ile **chunk split** olarak uygulanır.

### Kabul
- Individual/Dealer kullanıcıları **admin shell’i hiçbir koşulda görmeyecek**.
- Admin/dealer chunk’ları yanlış rolde **indirilmeyecek**.

### Release gate
- **Admin shell leakage = blocker** (FAIL).
