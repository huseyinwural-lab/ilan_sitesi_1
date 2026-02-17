# ADMIN_ROUTING_COUNTRY_STANDARD_v2

## Amaç
Admin panelde country scope deterministik ve deep-link paylaşılabilir olmalıdır.

## Kural
### Global Mode
- Admin URL’lerinde `country` paramı **yoktur**.
- Örn: `/admin/users`

### Country Mode
- Admin URL’lerinde `country` paramı **zorunludur**.
- Örn: `/admin/users?country=DE`

## Deep Link
- Her admin sayfası `?country=XX` ile direkt açılabilmelidir.

## URL Param Standardı
- Param adı: `country`
- Değer: **ülke code** (DE/CH/FR/AT)

## Not
- LocalStorage yalnızca son seçimi hatırlamak içindir.
- Uygulama state’i URL ile sync edilir; URL primary source of truth.
