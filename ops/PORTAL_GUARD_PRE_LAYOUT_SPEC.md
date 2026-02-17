# PORTAL_GUARD_PRE_LAYOUT_SPEC

## Amaç
Portal guard’ın **layout mount’tan önce** (ve ideal olarak portal chunk import’u tetiklenmeden önce) çalışması.

## Guard’ın çalıştığı nokta
- Router resolve aşaması:
  - `/admin/*` ve `/dealer/*` için `Route element` en üst seviyede **PortalGate** olur.
  - Portal app `React.lazy(import)` çağrısı **PortalGate içinde, guard PASS ise** tetiklenir.

## Allowed Portal Matrisi (role → portal)
- backoffice:
  - super_admin, country_admin, moderator, finance, support
- dealer:
  - dealer
- public/individual:
  - individual

## Davranış

### 1) Auth yok (user=null)
- Portal bazlı login’e redirect:
  - /admin/* → `/admin/login`
  - /dealer/* → `/dealer/login`
  - /account/* → `/login`

### 2) Auth var ama wrong portal
- 403 + redirect:
  - target = kullanıcının default home’u (role→home matrisi)
  - UI mesajı: "Bu alana erişim yetkiniz yok."

### 3) Token expire / 401
- AuthContext `logout()` + ilgili portal login’e redirect

## Negatif senaryolar
- Direct URL (bookmark): /admin/users
  - dealer/individual: admin chunk import edilmeden blok
- Back button: portal dönüşlerinde guard tekrar çalışır
- Token expire: portal içinden çıkış + login

## Kabul
- Wrong role’da **admin/dealer chunk request yok** (network kanıtı)
- Wrong role’da **admin shell DOM’a mount olmaz**
