# Member Menu Split Final Specification

**Goal:** Separate "Individual" end-users from "Commercial" entities in the Admin UI.

## 1. New Menu Item: Bireysel Kullanıcılar
-   **Path:** `/admin/members/individual`
-   **Data Source:** `GET /api/users?role=individual` (or new endpoint).
-   **Columns:**
    -   Ad Soyad
    -   Email
    -   Kayıt Tarihi
    -   Durum (Aktif/Pasif)
    -   Doğrulama (Email Verified)
-   **Actions:** Düzenle, Pasife Al, Detay.

## 2. Updated Menu Item: Ticari Üyeler (Ex-Dealers)
-   **Path:** `/admin/dealers` (existing)
-   **Data Source:** `GET /api/dealers`
-   **Columns (Updated):**
    -   Firma Adı
    -   Yetkili Kişi
    -   **Paket** (Premium/Standard) -> *Critical Requirement*
    -   **Tier** (Limit Level) -> *Critical Requirement*
    -   Bakiye/Quota
-   **Actions:** Paket Ata, Tier Değiştir, Limit Override.

## 3. Role/Permission
-   **Access:** `super_admin`, `country_admin`, `support`.
-   **Difference:** `support` can view but cannot change Tier/Package.
