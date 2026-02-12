# EU Real Estate Form UI Revision v1

**Target:** Listing Creation Form & Search Sidebar.

## 1. Room Input
-   **Label:** Oda Sayısı / Zimmer / Rooms
-   **Component:** Select Dropdown.
-   **Options:** 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5, 6, 7+

## 2. Kitchen Input
-   **Label:** Mutfak / Küche / Kitchen
-   **Component:** Toggle / Checkbox.
-   **Helper Text:** "Mutfak dolapları/tezgahı mevcut mu?" / "Ist eine Einbauküche vorhanden?"

## 3. Legacy Cleanup
-   Remove `kitchen_type` if exists.
-   Remove `room_count` Turkish style `+1` logic from UI parsers.
