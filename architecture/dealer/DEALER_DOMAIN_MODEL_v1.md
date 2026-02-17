# Dealer Domain Model v1

## 1. Entity: `dealers`
Replaces/Merges previous partial implementations.

| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | UUID | PK |
| `user_id` | UUID | Owner User (FK) |
| `slug` | String | Unique URL slug (e.g. `xyz-auto`) |
| `company_name` | String | Official Name |
| `tax_id` | String | VKN / Tax Number |
| `logo_url` | String | Storefront Logo |
| `status` | Enum | `pending`, `active` (verified), `rejected` |
| `plan_id` | UUID | Current Subscription Plan |
| `verified_at` | DateTime | Approval Timestamp |

## 2. Verification Policy
1.  User fills "Upgrade to Dealer" form.
2.  `dealers` record created with `status='pending'`.
3.  Admin reviews Tax ID.
4.  Admin approves -> `status='active'`, `user.user_type='commercial'`.
