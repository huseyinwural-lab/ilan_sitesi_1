# Vehicle Global Attributes v1

**Scope:** Applied to ALL Vehicle Categories (Cars, Motorcycles, Commercial).

## 1. Core Identity
-   **Key:** `brand`
    -   **Type:** Select (Filterable)
    -   **Mandatory:** **YES**
    -   **Example:** BMW, Mercedes, Honda.
-   **Key:** `model`
    -   **Type:** Text (or Dependent Select in future)
    -   **Mandatory:** **YES**
    -   **Example:** 320i, C200, Civic.
-   **Key:** `year`
    -   **Type:** Number (Year)
    -   **Filter:** Range (Min-Max)
    -   **Mandatory:** **YES**
-   **Key:** `km`
    -   **Type:** Number
    -   **Unit:** km
    -   **Filter:** Range (Min-Max)
    -   **Mandatory:** **YES**

## 2. Condition & Sales
-   **Key:** `condition`
    -   **Type:** Select
    -   **Options:** New, Used, Classic, Damaged.
    -   **Filter:** Multi-Select.
-   **Key:** `warranty`
    -   **Type:** Boolean
    -   **Label:** Warranty
    -   **Filter:** Checkbox.
-   **Key:** `swap`
    -   **Type:** Boolean
    -   **Label:** Swap Available
    -   **Filter:** Checkbox.
