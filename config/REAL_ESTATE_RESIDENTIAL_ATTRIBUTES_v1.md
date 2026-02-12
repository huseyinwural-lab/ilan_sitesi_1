# Real Estate Residential Attributes v1

**Scope:** Housing (Konut) Sub-categories only.

## 1. Attributes

### 🏠 Layout (Düzen)
-   **Key:** `room_count`
    -   **Type:** Select (Enum)
    -   **Mandatory:** **YES**
    -   **Filter:** Multi-Select (e.g., "2+1" OR "3+1")
    -   **Sorting:** By `sort_order` field in Option DB.
-   **Key:** `floor_location`
    -   **Type:** Select
    -   **Label:** Bulunduğu Kat
    -   **Filter:** Multi-Select
-   **Key:** `bathroom_count`
    -   **Type:** Select
    -   **Label:** Banyo Sayısı
    -   **Filter:** Select (1, 2, 3, 4+)

### ✨ Features (Özellikler)
-   **Key:** `balcony`
    -   **Type:** Boolean
    -   **Label:** Balkon
    -   **Filter:** Checkbox
-   **Key:** `furnished`
    -   **Type:** Boolean
    -   **Label:** Eşyalı
    -   **Filter:** Checkbox
-   **Key:** `in_complex`
    -   **Type:** Boolean
    -   **Label:** Site İçerisinde
    -   **Filter:** Checkbox
