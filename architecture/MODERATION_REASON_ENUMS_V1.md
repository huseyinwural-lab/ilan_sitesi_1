# MODERATION_REASON_ENUMS_V1

## Scope
Bu doküman **v1.0.0** için moderasyon reason enum setini **tek kaynak sözleşme** olarak kilitler.

> Not: v1.0.0 kapsamında bu liste değiştirilmeyecektir. Değişiklik talepleri v1.1 backlog’una gider.

---

## Enum Set (v1.0.0)

### REJECT
- `duplicate`
- `spam`
- `illegal`
- `wrong_category`

### NEEDS_REVISION
- `missing_photos`
- `insufficient_description`
- `wrong_price`
- `other`

---

## “other” Kullanım Kuralı
- `NEEDS_REVISION=other` seçildiğinde **reason_note alanı zorunludur**.
- Amaç: Audit kalitesini ve itiraz süreçlerinde kanıt üretilebilirliğini artırmak.
