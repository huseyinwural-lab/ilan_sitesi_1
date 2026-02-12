# UAT Test Case Pack: P7 Admin (v1.0)

**Priority Legend:**
-   **P0:** Critical (Blocker)
-   **P1:** High (Major functionality broken)
-   **P2:** Medium (UI/UX glitch)

## 1. Navigation & General (ADM)
| ID | Priority | Scenario | Steps | Expected Result | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **UAT-ADM-001** | P0 | Menu Renaming | Login -> Check Sidebar | "Dealers" -> "**Ticari Üyeler**", "Users" -> "**Kullanıcılar**" | ⬜ |
| **UAT-ADM-002** | P0 | Role Access | Login as `admin` | "Kullanıcılar" menu visible. | ⬜ |

## 2. Member Management (MEM)
| ID | Priority | Scenario | Steps | Expected Result | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **UAT-IND-001** | P1 | Individual List | Go to "**Bireysel Kullanıcılar**" | Grid shows verified icons, country flags. No company names. | ⬜ |
| **UAT-DEAL-001**| P0 | Dealer List Tiers | Go to "**Ticari Üyeler**" | "**Tier**" column visible. Shows STANDARD/PREMIUM/ENTERPRISE. | ⬜ |
| **UAT-DEAL-002**| P0 | Package Info | Check Dealer Row | "**Paket**" column shows "Basic Package" etc. | ⬜ |
| **UAT-DEAL-003**| P0 | Upgrade Tier | Edit Dealer -> Change Tier -> Save | Tier updates immediately. Log created. | ⬜ |

## 3. Dashboard (DASH)
| ID | Priority | Scenario | Steps | Expected Result | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **UAT-DASH-001**| P1 | Metric Accuracy | Check "Total Users" | Count > 20. Graphs populated. | ⬜ |

## 4. Moderation (MOD)
| ID | Priority | Scenario | Steps | Expected Result | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **UAT-MOD-001** | P0 | Pending Items | Go to "**İçerik Denetimi**" | Pending Listings visible. Approve works. | ⬜ |

## 5. Billing (BILL)
| ID | Priority | Scenario | Steps | Expected Result | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **UAT-BILL-001**| P1 | Invoice List | Go to "**Faturalar**" | List populated. Currencies (EUR) correct. | ⬜ |

## 6. Audit (AUD)
| ID | Priority | Scenario | Steps | Expected Result | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **UAT-AUD-001** | P0 | Tier Change Log | Check "**Sistem Logları**" | `ADMIN_CHANGE_TIER` event present. | ⬜ |
