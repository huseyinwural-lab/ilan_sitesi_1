# SPRINT1_2_E2E_EVIDENCE

## Amaç
SPRINT 1.2 Dealer Applications domain’i için zorunlu E2E kanıt paketi.

## Testler
1) Approve → dealer oluştu mu?
2) Reject → status rejected oldu mu?
3) Scope dışı attempt → 403?
4) Audit kaydı oluştu mu?
5) Approve sonrası login mümkün mü? (temp_password ile)

## Kanıt
- curl çıktıları (status + JSON)
- audit_logs örnek kayıtları
- admin UI ekran görüntüsü (liste + modal)
