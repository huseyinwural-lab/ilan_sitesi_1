# Regression Test Suite (Post-Fix)

**Goal:** Ensure no side effects on standard limiting.

## 1. Downgrade Test
-   **Action:** Change Premium -> Standard.
-   **Check:** User sending 70 req/min should be blocked *immediately*.

## 2. Legacy Flow
-   **Action:** Regular traffic (no tier change).
-   **Check:** Cache `rl:context:{id}` should persist for 60s (Not deleted).

## 3. Burst Reset
-   **Action:** User consumes full burst.
-   **Action:** Tier Change.
-   **Check:** Burst bucket should be replenished (New Tier = New Key).

**Status:** PENDING EXECUTION
