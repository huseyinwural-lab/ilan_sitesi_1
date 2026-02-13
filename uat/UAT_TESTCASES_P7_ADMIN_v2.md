# UAT Test Case Pack: P7 Admin (v2.0)

**Scope:** Admin Panel Full Functionality including User Mgmt & Real Estate v3.

## 1. User Management (NEW)
| ID | Priority | Scenario | Steps | Expected Result |
| :--- | :--- | :--- | :--- | :--- |
| **UAT-USER-001** | P0 | Create Moderator | Login as SuperAdmin -> Users -> Create -> Role: Moderator | Success (201). User appears in list. |
| **UAT-USER-002** | P1 | Duplicate Email | Try creating same email again | Error (400) "Email already exists". |
| **UAT-USER-003** | P1 | Invalid Role | Try creating role "hacker" (API only) | Error (400) "Invalid role". |

## 2. Real Estate v3 Data (NEW)
| ID | Priority | Scenario | Steps | Expected Result |
| :--- | :--- | :--- | :--- | :--- |
| **UAT-RE-001** | P0 | Data Quality | Check Listings List | No "Test Listing..." titles. Only "Sale Apartment...", "Rent Office..." etc. |
| **UAT-RE-002** | P1 | Room Filter | Filter by "3 Rooms" | Results show `room_count: "3"`. No `2+1` visible. |
| **UAT-RE-003** | P1 | Kitchen Filter | Filter by "Kitchen: Yes" | Results show `has_kitchen: true`. |
| **UAT-RE-004** | P1 | Commercial Isolation | Check a Commercial Listing | Does NOT show "Kitchen" or "Bathroom Count". Shows "Ceiling Height". |

## 3. General (Existing)
-   **UAT-ADM-001:** Menu Structure (Pass)
-   **UAT-DEAL-003:** Tier Upgrade (Pass)
