# ADMIN_COUNTRY_CONTEXT_V2_ENFORCEMENT_CHECKLIST

## Uygulanacak Modüller (Hedef)
- Users ✅ (bu iterasyonda uygulandı: /api/users?country=XX)
- Dashboard stats ✅ (bu iterasyonda uygulandı: /api/dashboard/stats?country=XX)
- Countries (global) ✅ (context resolve var)
- Categories (global) ✅ (context resolve var)
- Dealers (TBD - endpoint yoksa stub)
- Moderation (TBD - endpoint yoksa stub)
- Listings (TBD - endpoint yoksa stub)
- Finance/Analytics (TBD)

## Kural
- Global mode: filtre yok
- Country mode: filtre zorunlu (country_code / country_scoped data)
