# ADMIN_RBAC_COUNTRY_SCOPE_POLICY

## Amaç
Role-based access control ile country scope kısıtını entegre etmek.

## Kurallar
- Global Admin (ör: super_admin veya country_scope=['*']):
  - Tüm ülkelerde işlem yapabilir.
- Country Admin (ör: country_admin):
  - Sadece `country_scope` listesindeki ülkelerde işlem yapabilir.

## Param Override
- URL’de `?country=XX` ile scope dışı ülke seçimi:
  - Backend **403 Country scope forbidden** döner.

## Veri Modeli
- Mongo users collection içinde:
  - `country_scope: string[]` (örn: ['DE'] veya ['*'])
  - `country_code: string` (default ülke, UX)
