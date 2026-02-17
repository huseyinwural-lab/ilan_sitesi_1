# Country Fraud Segmentation Policy

## 1. IP Geolocation Check
*   **Rule**: If User Country is `DE` but IP is `CN` (China) -> Flag as `High Risk`.
*   **Exception**: User travel (Temporary).
*   **Action**: Require Email + Phone Verification immediately.

## 2. Cross-Border Posting
*   **Scenario**: User registered in `TR` posts item in `DE`.
*   **Risk**: High (Scam potential).
*   **Action**: Manual Moderation Queue (No auto-approve).
