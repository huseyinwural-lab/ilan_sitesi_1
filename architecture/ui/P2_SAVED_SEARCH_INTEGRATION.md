# P2 Saved Search Integration

## Amaç
Dashboard’daki “Kayıtlı Aramalar” kartını gerçek veriyle beslemek.

## İhtiyaç
- Saved search count endpoint (consumer scope)
- “Tümünü gör” listesi için Saved Search list endpoint

## Önerilen API
- `GET /api/v1/saved-searches/count`
- `GET /api/v1/saved-searches?limit=20`

## Fallback
- API yoksa: `0` + “Veri hazırlanıyor” state (deterministic).
