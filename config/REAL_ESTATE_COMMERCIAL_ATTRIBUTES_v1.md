# Real Estate Commercial Attributes v1

**Scope:** Commercial (Ticari İşletme) Sub-categories only.

## 1. Attributes

### 🏭 Industrial & Physical (Fiziksel)
-   **Key:** `ceiling_height`
    -   **Type:** Number
    -   **Unit:** m (meter)
    -   **Label:** Tavan Yüksekliği
    -   **Filter:** Range
-   **Key:** `entrance_height`
    -   **Type:** Number
    -   **Unit:** m
    -   **Label:** Giriş Yüksekliği (Kapı)
    -   **Filter:** Range
-   **Key:** `power_capacity`
    -   **Type:** Number
    -   **Unit:** kW
    -   **Label:** Elektrik Gücü
    -   **Filter:** Range
-   **Key:** `crane`
    -   **Type:** Boolean
    -   **Label:** Vinç
    -   **Filter:** Checkbox ("Has Crane")

### 📄 Legal & Status (Durum)
-   **Key:** `is_transfer`
    -   **Type:** Boolean
    -   **Label:** Devren (Satılık/Kiralık İşyeri için)
    -   **Filter:** Checkbox
-   **Key:** `ground_survey`
    -   **Type:** Select
    -   **Label:** Zemin Etüdü
    -   **Filter:** Select (Yapıldı / Yapılmadı)
