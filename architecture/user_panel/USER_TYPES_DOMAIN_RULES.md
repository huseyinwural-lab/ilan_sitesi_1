# User Types Domain Rules

## 1. Data Model Strategy
We use a single `users` table with a discriminator `user_type`, linked to a detailed profile table for businesses.

### 1.1. User Table Extension
*   `user_type`: Enum(`individual`, `business`).
*   `business_profile_id`: UUID (FK -> `dealer_profiles`, Nullable).

### 1.2. Dealer Profile Table (`dealer_profiles`)
*   `company_name`: String.
*   `tax_id`: String (Unique).
*   `address`: JSONB.
*   `contact_person`: String.
*   `verification_status`: Enum(`pending`, `verified`, `rejected`).

## 2. Transition Rules (State Machine)

### 2.1. Individual -> Business (Upgrade)
1.  **Request**: User submits form with Tax ID & Company Info.
2.  **State**: User remains `individual` but `dealer_application` is created.
3.  **Approval**: Admin reviews application.
4.  **Transition**: On approve -> `user_type` becomes `business`, `dealer_profile` created.

### 2.2. Business -> Individual (Downgrade)
*   **Rule**: **Not Allowed** in V1.
*   **Reason**: Invoice history and liability complexity.
*   **Workaround**: User must create a new account for personal use.

## 3. Limits & Quotas
| Feature | Individual | Business (Standard) |
| :--- | :--- | :--- |
| Active Listings | Max 2 (Free) | Based on Package |
| Photos per Listing | 10 | 20 |
| Video Upload | No | Yes |
| Profile Page | Basic | Branded Storefront |
