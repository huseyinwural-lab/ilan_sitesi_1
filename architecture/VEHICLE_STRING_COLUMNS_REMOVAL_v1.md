# Vehicle String Columns Removal v1

**Target:** Release +1 (P8)

## 1. Plan
1.  **Audit:** Ensure 0 reads from JSONB `brand`/`model`.
2.  **Migration:**
    ```python
    op.execute("UPDATE listings SET attributes = attributes - 'brand' - 'model' WHERE module='vehicle'")
    ```
3.  **Code Cleanup:** Remove any Pydantic validators checking these strings.

**Exit Criteria:** Database is strictly relational for Make/Model.
