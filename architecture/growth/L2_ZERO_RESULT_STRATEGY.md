# L2: Zero Result Strategy

## 1. Problem
User searches for "Bonn" but we have no listings there yet. "No results" = User Churn.

## 2. Mitigation Tactic (The "Expand" Algorithm)

### Step 1: Expand Radius
*   If `count == 0` for City, automatically search `radius=20km`.
*   **UI Message**: "No listings found in **Bonn**, but here are 12 listings nearby."

### Step 2: Expand Category
*   If filtering by "3 Rooms" yields 0, suggest "2 Rooms" or "4 Rooms".
*   **UI Message**: "Broaden your search to see more results."

### Step 3: Capture Intent (Lead Gen)
*   **Action**: Show "Get Notified" form.
*   **Backend**: Save `SavedSearch` (future feature MVP).
*   **Workflow**: When a listing is added in Bonn, email this user.

## 3. Implementation
*   Modify `search_real_estate` in `search_routes.py` to return `suggested_results` if `data` is empty.
