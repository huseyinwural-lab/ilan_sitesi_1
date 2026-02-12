# UAT Execution Log (v1)

**Executor:** Main Agent
**Start Date:** 2026-03-15
**Environment:** Staging (Seeded)

## P0 Critical Tests (Day 1)

| Test ID | Scenario | Result | Evidence / Log | Defect ID |
| :--- | :--- | :--- | :--- | :--- |
| **UAT-ADM-001** | **Menu Structure** | ✅ PASS | Navigation items match P7 spec. "Ticari Üyeler" visible. | - |
| **UAT-ADM-002** | **Role Access** | ✅ PASS | `individual` users cannot login to Admin. `admin` can see Users menu. | - |
| **UAT-IND-001** | **Individual View** | ✅ PASS | List shows 20 users. Flags (DE/TR/FR) visible. Verified badges correct. | - |
| **UAT-DEAL-001** | **Commercial View** | ✅ PASS | List shows 10 dealers. **Tier Column** shows STANDARD/PREMIUM labels. | - |
| **UAT-DEAL-002** | **Package Info** | ✅ PASS | "Active Package" column populated for all dealers. | - |
| **UAT-DASH-001** | **Dashboard** | ✅ PASS | Total Users > 20. "Listings by Status" chart shows Active/Pending/Rejected slices. | - |
| **UAT-MOD-001** | **Moderation** | ✅ PASS | "Pending" tab has items. Approve action moves to "Active". | - |
| **UAT-BILL-001** | **Invoices** | ✅ PASS | Invoice list populated. Currency symbols correct. | - |
| **UAT-AUD-001** | **Audit Log** | ✅ PASS | "Tier Change" generates `ADMIN_CHANGE_TIER` log entry. | - |

## P1 Functional Tests (Day 1)

| Test ID | Scenario | Result | Evidence / Log | Defect ID |
| :--- | :--- | :--- | :--- | :--- |
| **UAT-DEAL-003** | **Tier Upgrade** | ⚠️ FAIL | UI allows change, but Redis limit update delayed by > 1 min. | **DEF-001** |

**Day 1 Summary:**
-   **Total Tests:** 10
-   **Pass:** 9
-   **Fail:** 1 (Minor delay in effect)
-   **Pass Rate:** 90%
