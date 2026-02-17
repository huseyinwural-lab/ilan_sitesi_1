# FAZ-G1 Scope Lock: Dealer Growth

## 1. Objective
To build a robust B2B ecosystem for professional sellers (Real Estate Agents, Car Dealers).

## 2. In-Scope

### 2.1. Dealer Onboarding
*   Self-service upgrade from Individual to Commercial.
*   Company verification form (Tax ID, Address).
*   Admin moderation queue.

### 2.2. Dealer Dashboard
*   Listing Quota Status (Active/Total).
*   Lead Analytics (Views, Reveals).
*   Subscription Status.

### 2.3. Public Profile
*   Storefront Page (`/bayi/{slug}`).
*   Verified Badge.
*   "All listings by this dealer" filter.

## 3. Data Model Alignment
*   **Merge**: `DealerProfile` (P28) and `Dealer` (P1).
*   **Target**: Single `dealers` table linked to `users`.
*   **Status**: `pending_verification`, `verified`, `suspended`.
