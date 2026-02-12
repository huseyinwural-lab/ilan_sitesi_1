# P7 Member Filter Update Spec

**Backend Logic Update:** Separation of Concerns

## 1. Enum Verification
-   Ensure `User.role` supports:
    -   `individual` (Bireysel)
    -   `dealer` (Ticari hesap yöneticisi)
    -   `admin/support` (Sistem kullanıcısı)

## 2. Bireysel Kullanıcılar Endpoint
-   **Route:** `GET /api/users`
-   **Filter:** `?role=individual` (Strict filter).
-   **Exclusion:** Must NOT return users linked to `Dealer` records (if any overlap exists).

## 3. Ticari Üyeler Endpoint
-   **Route:** `GET /api/dealers`
-   **Join:** Must join with `DealerPackage` to fetch `tier`.
-   **Join:** Must join with `DealerSubscription` to fetch active package name.
-   **Filter:** `?tier=PREMIUM` (Support filtering by Tier).

## 4. UI Logic
-   **Tier Field:** Visible **ONLY** in "Ticari Üyeler" grid. Hidden in "Bireysel" and "Kullanıcılar".
-   **Package Field:** Visible **ONLY** in "Ticari Üyeler".
