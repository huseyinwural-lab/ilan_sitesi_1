# Billing Transaction Audit V1

## Requirement
Billing zincirinde audit **zorunlu**.

## Events
- payment_succeeded
- invoice_marked_paid
- subscription_activated
- quota_limits_updated

## Rule
- State update e audit insert **aynı transaction içinde**.
