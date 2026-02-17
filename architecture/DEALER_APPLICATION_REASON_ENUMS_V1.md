# DEALER_APPLICATION_REASON_ENUMS_V1

## Scope
Bu doküman **v1.0.0 / SPRINT 1.2** için Dealer Application reject reason enum setini **tek kaynak sözleşme** olarak kilitler.

---

## REJECT Reason Enum (v1)
- `incomplete_documents`
- `invalid_company_info`
- `duplicate_application`
- `compliance_issue`
- `other`

### “other” Kuralı
- `reason=other` seçildiğinde **reason_note zorunludur**.
- Amaç: audit kalitesini ve itiraz süreçlerinde kanıt üretilebilirliğini artırmak.
