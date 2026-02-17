# P27: Trust-Based Monetization Spec

## 1. Trusted Seller Subscription
A premium tier for high-volume sellers who want to signal trust.

### 1.1. Benefits
*   **Trust Badge**: Displayed on profile and listings.
*   **Search Boost**: Slight weight increase in organic ranking.
*   **Lower Fees**: Escrow fee reduced from 5% to 3%.

### 1.2. Requirements
*   `is_identity_verified` = True.
*   `rating_avg` > 4.5.
*   Monthly Fee: €19.99.

## 2. Escrow Fee Model
Platform takes a cut for securing the transaction.

### 2.1. Structure
| Transaction Value | Standard Fee | Trusted Seller Fee |
| :--- | :--- | :--- |
| €0 - €500 | 5% | 3% |
| €500 - €2000 | 4% | 2.5% |
| €2000+ | 3% | 2% |

### 2.2. Logic
Implemented in `EscrowService.calculate_fee()`.

## 3. Insurance Add-on (Roadmap)
*   **Partner**: 3rd Party Insurtech (e.g., Qover).
*   **Model**: API call to get quote -> User pays premium -> Platform gets commission (20%).
*   **Status**: Analysis only for P27.
