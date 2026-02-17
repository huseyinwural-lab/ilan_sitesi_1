# P27: Escrow Transaction Schema

## 1. Overview
The Escrow system holds buyer funds until the transaction is successfully completed or disputed.

## 2. Database Schema (`escrow_transactions`)

| Column | Type | Index | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PK | Transaction ID |
| `listing_id` | UUID | Index | Item being sold |
| `buyer_id` | UUID | Index | User paying |
| `seller_id` | UUID | Index | User receiving (eventually) |
| `amount` | Decimal | - | Total amount locked |
| `fee_amount` | Decimal | - | Platform fee (deducted from payout) |
| `currency` | String | - | e.g. "EUR" |
| `status` | String | Index | `initiated`, `funded`, `released`, `refunded`, `disputed` |
| `stripe_payment_intent_id` | String | - | External reference |
| `created_at` | DateTime | Index | - |
| `updated_at` | DateTime | - | - |

## 3. Workflow States
1.  **Initiated**: Buyer clicks "Buy Now". Payment Intent created.
2.  **Funded**: Buyer pays. Money held in Stripe Connect platform account.
3.  **Released**: Buyer confirms receipt OR auto-release after 3 days. Money moves to Seller.
4.  **Disputed**: Buyer claims issue. Money frozen.
5.  **Refunded**: Admin or Seller approves refund. Money returned to Buyer.

## 4. Dispute Lifecycle
*   **Table**: `disputes`
*   **Relation**: 1-to-1 with `escrow_transactions`.
*   **Columns**: `reason`, `description`, `status` (`open`, `resolved_buyer`, `resolved_seller`).
