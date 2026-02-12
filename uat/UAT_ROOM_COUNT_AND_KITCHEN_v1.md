# UAT Room Count and Kitchen v1

**Goal:** Verify new Attribute Structure.

## Test 1: Seed Verification
-   Check `AttributeOption` table for `room_count`.
-   Verify values are `1`, `2`, `3`... not `1+1`.

## Test 2: Listing Data
-   Check `listings` table `attributes` column.
-   Verify `room_count` is stored as "2" or "3".
-   Verify `has_kitchen` is boolean `true/false`.

## Test 3: Search Simulation (Mental)
-   Query `attributes->>'room_count' IN ('2', '3')` should return results.
-   Query `attributes->>'has_kitchen' = 'true'` should return results.
