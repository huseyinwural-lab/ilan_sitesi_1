# Soft Launch Invite Mode Configuration

**Document ID:** SOFT_LAUNCH_INVITE_MODE_v1  
**Date:** 2026-02-13  
**Status:** 🚀 ACTIVE  

---

## 1. Strategy
To control initial load and verify revenue integrity, registration is restricted to invited users only.

## 2. Implementation
### 2.1. Feature Flag
- **Flag Key:** `REGISTRATION_INVITE_ONLY`
- **Value:** `True`

### 2.2. API Logic (`auth_routes.py`)
```python
@router.post("/register")
def register(data: UserCreate):
    if FEATURE_FLAGS["REGISTRATION_INVITE_ONLY"]:
        if not is_valid_invite_code(data.invite_code):
            raise HTTPException(403, "Invite code required for Beta")
```

### 2.3. Invite Management
- **Admin Tool:** `POST /api/v1/admin/invites` (Generate Codes).
- **Distribution:** Email codes manually to first 100 dealers.

## 3. Exit Criteria
- 50 Paying Customers.
- Zero Critical Billing Issues for 14 days.
- **Action:** Set `REGISTRATION_INVITE_ONLY = False`.
