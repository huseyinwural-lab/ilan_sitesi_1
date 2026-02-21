# Mongo→SQL Strangler Plan (Runbook)

## Amaç
Mongo bağımlılıklarını modül bazlı kaldırıp tek kaynak SQL’e geçmek; risk izolasyonu ve kontrollü rollback sağlamak.

## Strateji (Strangler Fig)
1. **Modül seçimi + kapsam kilidi**
   - Domain sınırları ve bağımlılıklar netlenir.
   - Endpoint envanterine işlenir.
2. **Schema + Migration**
   - SQL model + Alembic migration (idempotent).
   - Index planı ve unique constraint’ler.
3. **Backfill / One-time Job**
   - Mongo export → SQL import (checksum/örneklem doğrulama).
   - Row count + sample diff raporu.
4. **Switch (Read/Write Cutover)**
   - Endpoint’ler SQL repo’ya yönlendirilir.
   - Mongo read-only (varsa) + fallback kaldırılır.
5. **E2E + Observability**
   - 3 kritik senaryo + metrik kontrolleri.
6. **Decommission**
   - Mongo kodu, scriptler, config, dokümanlar kaldırılır.

## Gate’ler
- **Gate-1:** Schema + migration başarılı (alembic head)
- **Gate-2:** Backfill doğrulaması tamam
- **Gate-3:** E2E + latency/error budget OK
- **Gate-4:** Mongo kodu kaldırıldı

## Rollback Kuralı
- Cutover sonrası kritik hata → ilgili modül SQL switch geri alınır.
- Rollback sadece modül bazlı; diğer modüller etkilenmez.

## Raporlama
- Her release’te “Mongo kullanım sayacı”: kalan endpoint sayısı + çağrı frekansı.

