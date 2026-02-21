# MONGO_CUTOFF_FINAL01

## Karar (ADR-FINAL-02)
- Critical User Path içinde **Mongo fallback yok**.
- AUTH → Stripe → Ad Loop zincirinde yalnızca **SQL** kullanılacak.

## Config Değişikliği (Kanıt)
- backend/.env:
  - `MONGO_ENABLED="false"`
  - `AUTH_PROVIDER="sql"`
  - `APPLICATIONS_PROVIDER="sql"`

## Kod Değişikliği (Özet)
- `server.py` içindeki **AUTH_PROVIDER == "mongo"** fallback’ları kaldırıldı.
- Profil güncelleme + şifre değişimi SQL + SQL audit ile çalışır.

## Not
- Mongo tabanlı kullanıcı veri export/push subscription gibi kritik olmayan akışlar **Critical Path dışında** tutulur.
