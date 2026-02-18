# Sprint 6 Gate Test Matrix

## Scope
- **Portals:** Public / User / Dealer / Admin
- **Countries:** DE + FR (country-scope doğrulama)
- **Roles:** individual, dealer, country_admin, super_admin, finance, support

## Test Credential Seti (Seed)
- **super_admin:** admin@platform.com / Admin123!
- **country_admin:** countryadmin@platform.com / Admin123!
- **finance:** finance@platform.com / Demo123!
- **support (individual proxy):** support@platform.ch / Demo123!
- **dealer:** dealer@platform.com / Dealer123!

## Matrix (Özet)
| Portal | Rol | Ülke | Gate Kapsamı |
| --- | --- | --- | --- |
| Public | anonymous | DE/FR | Search + Detail + Report Submit |
| User | support (individual proxy) | DE | Listing Create/Submit + Moderation + Publish |
| Dealer | dealer | DE | Listing Create/Submit + Publish + Plan görünümü |
| Admin | super_admin | DE/FR | RBAC, Country-scope, Audit, Finance, Reports |
| Admin | country_admin | DE | Country-scope enforcement |
| Admin | finance | DE | Finance endpoints (invoices/revenue/tax/plan) |

## Evidence Dokümanları
- /app/ops/SPRINT6_RBAC_GATE_EVIDENCE.md
- /app/ops/SPRINT6_COUNTRY_SCOPE_GATE_EVIDENCE.md
- /app/ops/SPRINT6_AUDIT_COVERAGE_EVIDENCE.md
- /app/ops/SPRINT6_CRITICAL_FLOWS_E2E_EVIDENCE.md
- /app/ops/SPRINT6_NON_FUNCTIONAL_GATE.md
