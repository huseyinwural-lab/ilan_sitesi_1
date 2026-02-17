# FAZ_PORTAL_SPLIT_V1_CLOSEOUT

## Amaç
Portal Split v1 fazının PASS/PARTIAL/FAIL kapanışı.

## Portal Kriterleri

### 1) Public/Individual
- [ ] Public route’lar çalışıyor
- [ ] /account ProtectedRoute + role check
- [ ] Individual kullanıcı /admin veya /dealer’a gidince 403+redirect

### 2) Dealer
- [ ] /dealer/* portal chunk sadece dealer’da yükleniyor
- [ ] Dealer kullanıcı /admin’a gidince admin shell mount olmuyor

### 3) Backoffice
- [ ] /admin/* portal chunk sadece admin’de yükleniyor
- [ ] Individual/dealer wrong URL’de admin chunk request yok

## Release Gate
- **Admin shell leakage = FAIL (Blocker)**

## Kanıt
- Network assertion logları: `PORTAL_SPLIT_SMOKE_TEST_PLAN.md`

## Açık Riskler
- Import boundary ihlali (admin/dealer kodunun main bundle’a sızması)
- Demo credentials prod’da görünmesi

## Fix Sprint bağlantısı
- PASS olmayan maddeler `UI_GAPS_BACKLOG_PRIORITIZED.md` veya portal split backlog’unda toplanır.
