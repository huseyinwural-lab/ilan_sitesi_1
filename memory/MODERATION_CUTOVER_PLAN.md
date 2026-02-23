# Moderation Cutover Plan

## Freeze Window (30 dakika)
- Low-traffic zaman dilimi seçilecek.
- Moderation write işlemleri kısa süreli read-only moda alınır.
- Dry-run ile süre ölçülür; 30 dk aşarsa plan revize edilir.

## Rollback (Mongo Read Fallback)
- Feature flag veya rollback script ile Mongo read tekrar etkinleştirilir.
- SQL yazımları durdurulur; ops logları korunur.

## Post-Cutover Monitoring
- Error rate (5dk)
- Moderation approve/reject latency
- UI queue load time
- Audit parity spot-check
