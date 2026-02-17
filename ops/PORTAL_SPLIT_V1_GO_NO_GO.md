# PORTAL_SPLIT_V1_GO_NO_GO

## Karar
**GO (Onaylandı)** — Portal Split v1 implementasyonuna başlanacaktır.

## Kapsam
- Route’ların portal modüllerine taşınması
- Lazy chunk split (route-based)
- PortalGate (pre-layout guard)
- Login ayrımı: `/login`, `/dealer/login`, `/admin/login`
- Demo credentials prod’da gizleme

## Zorunlu Guard Şartları (Release Gate)
- Wrong role → ilgili portal chunk request **olmayacak**
- Wrong role → admin shell DOM **mount olmayacak**
- Redirect hedefi doğru olacak (login veya doğru portal home)

## Not
- Bu faz “mimari ayrıştırma” içerir; önceki “no-refactor” kilidi bu faz için geçersizdir.
