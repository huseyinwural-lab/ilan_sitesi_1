# REPORT_REASON_ENUMS_V1

## Amaç
Şikayet (Reports) reason enum setini **tek kaynak sözleşme** olarak kilitlemek.

## Enum Set (v1)
- `spam`
- `scam_fraud`
- `prohibited_item`
- `wrong_category`
- `harassment`
- `copyright`
- `other` *(note zorunlu)*

## Kurallar
- `other` seçildiğinde `reason_note` zorunludur.
- Enum dışı değerler kabul edilmez.
