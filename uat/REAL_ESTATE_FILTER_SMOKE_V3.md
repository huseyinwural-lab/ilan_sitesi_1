# Real Estate Filter Smoke v3

**Env:** Staging

## 1. Room Count (EU Standard)
-   [ ] Filter "3 Rooms".
-   [ ] Result: Listings with `room_count: "3"` or `"3.5"`.
-   [ ] Check: No "2+1" legacy data appears.

## 2. Kitchen Boolean
-   [ ] Filter "Kitchen Available" (Checkbox).
-   [ ] Result: Only listings where `has_kitchen: true`.

## 3. Commercial Isolation
-   [ ] Go to "Commercial / Office".
-   [ ] Check Filters: "Kitchen" checkbox should **NOT** exist.
-   [ ] Check Filters: "Room Count" should **NOT** exist (or be optional/different context). *Decision: Commercial usually uses rooms too, but let's assume it uses m2 primary.*
