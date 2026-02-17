# ADMIN_DEALER_APPLICATION_UI_WIRING

## Route
- `/admin/dealer-applications`

## UI Özellikleri
- Liste: email, company_name, country_code, status, created_at
- Filtre: status, search
- Approve / Reject modal:
  - Reject: reason dropdown (enum) + other → textarea zorunlu
  - Approve: confirm
- İşlem sonrası liste refresh

## Kabul Kriteri
- Reject reason seçmeden gönderilemez
- other seçilince note zorunlu
- Approve/Reject sonrası tablo güncellenir
