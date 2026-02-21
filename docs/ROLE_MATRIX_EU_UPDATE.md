# ROLE_MATRIX_EU_UPDATE

## Roles
- super_admin
- finance
- dealer
- individual (consumer)

## Panel Erişimleri
- Consumer panel: `individual`
- Dealer panel: `dealer`
- Admin billing audit: `super_admin`, `finance`

## GDPR/Privacy Center
- consumer: kendi verisi
- dealer: kendi verisi

## Not
RBAC enforce check: portal_scope `account` sadece `individual`, `dealer` sadece `dealer`.
