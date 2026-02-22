# REGISTER_ANTIBOT_HONEYPOT_SPEC

## Amaç
Register endpointlerinde bot kayıtlarını engellemek.

## Uygulama
- Frontend formuna görünmez honeypot alanı eklendi: `company_website`
- Server-side zorunlu kontrol: değer doluysa **400**
- Audit log event_type: `register_honeypot_hit`

## Davranış
- Dolu honeypot → 400 `Invalid request`
- Audit log metadata: field, value, role

## Erişilebilirlik
- Alan görünmez + aria-hidden + tabIndex=-1
