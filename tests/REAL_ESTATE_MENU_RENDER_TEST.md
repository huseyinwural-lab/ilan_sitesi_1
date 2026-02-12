# Real Estate Menu Render Test

**Goal:** Verify alphabetical sorting per locale.

## Test Case 1: TR Rendering
-   **Input:** Locale `tr`
-   **Fetch:** `/api/categories?module=real_estate&type=residential`
-   **Expect:** List starts with **B** (Bina), ends with **V** (Villa) or **Y** (Yalı).
-   **Check:** "Daire" is at index ~3.

## Test Case 2: DE Rendering
-   **Input:** Locale `de`
-   **Fetch:** Same endpoint.
-   **Expect:** List starts with **B** (Bauernhaus), then **E** (Einfamilienhaus).
-   **Check:** "Wohnung" (Daire) is near the end (W).
-   **Failure Condition:** If "Wohnung" appears at index ~3 (inheriting TR sort), FAIL.

## Test Case 3: URL Construction
-   **Input:** Category "Gas Station"
-   **Check TR:** `.../akaryakit-istasyonu`
-   **Check DE:** `.../tankstelle`
-   **Check FR:** `.../station-service`
