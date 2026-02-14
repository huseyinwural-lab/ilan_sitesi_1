# P11 Billing Domain Model

**Document ID:** P11_BILLING_DOMAIN_MODEL_v1  
**Date:** 2026-02-13  
**Status:** 🏗️ ARCHITECTURE  

---

## 1. Entity Relationship

```mermaid
erDiagram
    User ||--o{ Customer : "billing_profile"
    Customer ||--o{ Subscription : "has"
    Customer ||--o{ Invoice : "billed"
    Subscription ||--o{ Invoice : "generates"
    Invoice ||--o{ Payment : "paid_by"
    
    Customer {
        string provider_id "stripe_cus_123"
        string payment_method_token
        string billing_email
        json billing_address
    }

    Subscription {
        string provider_sub_id "sub_123"
        string status "active, past_due, canceled"
        timestamp current_period_end
        timestamp cancel_at
    }

    Invoice {
        string provider_invoice_id "in_123"
        decimal amount
        string currency
        string status "paid, open, void"
        string pdf_url
    }
```

## 2. Table Specifications (Additions)

### 2.1. `customers` (New)
Maps internal `User` to Payment Provider's Customer.
- `user_id`: PK/FK
- `provider_id`: Unique Index
- `balance`: Numeric (Credits/Debits)

### 2.2. `payments` (New)
Audit trail of transactions.
- `id`: UUID
- `invoice_id`: FK
- `amount`: Numeric
- `provider_tx_id`: String
- `status`: String (succeeded, failed)
- `created_at`: Timestamp

### 2.3. `user_subscriptions` (Update)
Enhance existing table from P10.
- Add `provider_subscription_id`: String (Index)
- Add `cancel_at_period_end`: Boolean

---

## 3. State Machine (Subscription)
1. **Incomplete:** Checkout started.
2. **Active:** Payment succeeded. -> **Quota Unlocked.**
3. **Past Due:** Renewal failed. -> **Quota Grace Period (3 days).**
4. **Canceled:** User stopped auto-renew. -> **Active until Period End.**
5. **Unpaid/Expired:** Final state. -> **Quota Reset to Free.**
