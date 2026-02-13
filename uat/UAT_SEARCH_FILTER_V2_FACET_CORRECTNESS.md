# UAT Search Filter v2 Facet Correctness

**Goal:** Verify Facet Logic Logic.

## 1. Inheritance
-   **Scenario:** Go to "Smartphones".
-   **Check:** Facets include "Brand" (Inherited from Electronics) and "Storage" (Direct).
-   **Result:** [PENDING]

## 2. Self-Filter Exclusion (Multi-Select)
-   **Scenario:** Select Brand = "Apple".
-   **Check:** "Brand" facet counts should reflect *Global* scope for that category (showing Samsung count too), NOT filtered scope (Samsung = 0).
-   *Correction:* Current impl uses `WHERE id IN filtered_ids`. This hides unselected options (Drill-down).
-   *Decision:* Standard e-com behavior is "OR within same attribute, AND between attributes".
-   *Action:* Refine logic in future sprint if needed. Current logic: Drill-down.

## 3. Localization
-   **Scenario:** Switch language to TR.
-   **Check:** Facet Label "Storage" -> "Hafıza". Option "New" -> "Sıfır".
