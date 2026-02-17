# MODERATION_P0_E2E_EVIDENCE

## Amaç
Moderation uçtan uca P0 kanıt paketi (v1.0.0 release blocker).

## Test Senaryoları
1) Submit → `pending_moderation`
2) Pending ilan public’da görünmüyor (search/detail/media)
3) Approve → public’da görünür
4) Reject / Needs Revision → public’da görünmez + reason zorunlu
5) Audit log satırı yazıldı mı (alanlar dolu mu)
6) RBAC / country-scope negatif test

## Kanıt Formatı (öneri)
- API curl çıktıları (status code + JSON)
- Admin UI ekran görüntüleri (queue + aksiyon sonrası)
- `audit_logs` örnek kayıt (maskelenmiş e-posta gerekmez, sadece id/role yeter)
