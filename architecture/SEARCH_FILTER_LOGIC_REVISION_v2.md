# Search Filter Logic Revision v2

**Update:** Align filters with EU Standards.

## 1. Room Count Filter
-   **Type:** Multi-Select Buttons or Checkboxes.
-   **Values:** [1] [1.5] [2] [2.5] [3] [4] [5+]
-   **Logic:** OR (e.g. User selects "2" and "3" -> Show both).

## 2. Kitchen Filter
-   **Type:** Single Checkbox.
-   **Logic:**
    -   Checked: `has_kitchen = true`
    -   Unchecked: Show All.

## 3. Floor Filter (Clarification)
-   Keep as is (Ground, 1, 2...).
