# Free Mode Phase Out Plan

## 1. Timeline
*   **Day 0 (Announcement)**: "Platform is growing! New limits apply from [Date]."
*   **Day 14 (Soft Lock)**: New users get `individual` quota (2 listings). `MONETIZATION_FREE_MODE` flag disabled for new signups.
*   **Day 30 (Hard Lock)**: Existing listings > Quota are marked `expired` unless plan upgraded.

## 2. Migration Logic
1.  **Dealers**:
    *   If listings > 10 -> Auto-assign "Legacy Trial" plan (expires in 14 days).
    *   Must subscribe to Pro/Basic to keep listings active.
2.  **Individuals**:
    *   Keep 2 newest listings active.
    *   Archive others.

## 3. Communication
*   **Email**: "Action Required: Choose your plan to keep selling."
*   **Dashboard**: Persistent banner "Free Trial ending in X days".
