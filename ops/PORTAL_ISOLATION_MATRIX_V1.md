# PORTAL_ISOLATION_MATRIX_V1

## Rol → Allowed Portal

| Role | Allowed Portal | Default Home |
|------|---------------|--------------|
| individual | public/individual | /account |
| dealer | dealer | /dealer |
| super_admin/country_admin/moderator/finance/support | backoffice | /admin |

## Wrong Portal Davranışı + Chunk Load

| Role | Wrong Portal | Beklenen Redirect | Wrong portal chunk request 0? |
|------|-------------|-------------------|------------------------------|
| individual | /admin/* | /admin/login veya /login veya /account | Evet (kabul) |
| individual | /dealer/* | /dealer/login veya /login veya /account | Evet (kabul) |
| dealer | /admin/* | /dealer | Evet (kanıtlandı) |
| admin(backoffice) | /dealer/* | /admin | Evet (kanıtlandı) |

## Not
- Dealer pozitif test: dealer chunk request > 0, backoffice chunk = 0 (kanıtlandı).
