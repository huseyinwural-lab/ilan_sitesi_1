# BILLING_STATUS_V1 (ADR-BILL-01)

## InvoiceStatus (V1)
- `draft`
- `issued`
- `paid`
- `void`
- `refunded`

### State Transitions
- draft → issued | void
- issued → paid | void
- paid → refunded

## PaymentStatus (V1)
- `requires_payment_method`
- `requires_confirmation`
- `processing`
- `succeeded`
- `failed`
- `canceled`
- `refunded`

### State Transitions (Özet)
- requires_payment_method → requires_confirmation | processing
- requires_confirmation → processing | failed
- processing → succeeded | failed
- succeeded → refunded
- failed → requires_payment_method (retry)

## Notlar
- Stripe event mapping bu enum setine göre yapılır.
- Non-standard status değerleri DB'de saklanmaz; mapping + audit zorunlu.
