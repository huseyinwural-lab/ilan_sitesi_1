# Search Page Layout Spec

## 1. Desktop Layout
*   **Left Sidebar (25%)**: Filters. Sticky position.
*   **Main Column (75%)**:
    *   Header: Breadcrumbs, Count ("150 results"), Sort Dropdown.
    *   Grid: 3 or 4 columns of cards.
    *   Footer: "Load More" button.

## 2. Mobile Layout
*   **Filter**: Floating Action Button (FAB) or "Filter" button in header opens Modal.
*   **Grid**: 1 column (Full width cards).

## 3. Empty State
If `results.length === 0`:
*   Icon: Search loop / Empty box.
*   Text: "No results found".
*   Action: "Clear Filters" button.
