# MODERATION_RBAC_ENFORCEMENT

## Amaç
Moderation endpoint’lerinde RBAC + country scope enforcement (v1.0.0 P0 release blocker).

## Rol Kuralı
Moderasyon aksiyonlarını yalnızca şu roller yapabilir:
- `moderator`
- `country_admin`
- `super_admin`

## Country Scope Kuralı
- `country_admin` yalnızca kendi `country_scope` içindeki ülkelere ait listing’lere aksiyon alabilir.

## Kabul Kriteri
- Scope dışı attempt → **403**
- (Opsiyonel) Scope dışı deneme için audit “attempt” log’u yazılabilir; v1.0.0 için opsiyonel.
