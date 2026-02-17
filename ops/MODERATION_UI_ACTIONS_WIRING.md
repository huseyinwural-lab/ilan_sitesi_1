# MODERATION_UI_ACTIONS_WIRING

## Amaç
Moderation ekranına 3 aksiyonu bağlamak:
- Approve
- Reject
- Needs Revision

## UI Kuralları (v1.0.0)
- Reject / Needs Revision aksiyonlarında **reason seçmeden** gönderilemez.
- `NEEDS_REVISION=other` seçilince **reason_note alanı zorunlu**.
- Aksiyon sonrası queue otomatik güncellenir.

## Kabul Kriteri
- Reason doğrulaması UI’da bloklayıcıdır
- Aksiyon sonrası liste güncellenir (queue reload)
