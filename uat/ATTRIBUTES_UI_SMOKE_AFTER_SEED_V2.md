# Attributes UI Smoke Test (Post-Seed v2)

**Env:** Staging

## 1. List Verification
-   [ ] Go to `Admin > İlan Alanları`.
-   [ ] Verify `room_count` exists. Label: "Oda Sayısı / Rooms / Zimmer".
-   [ ] Verify `m2_gross` exists. Type: Number. Unit: m².

## 2. Category Binding
-   [ ] Go to `Admin > Kategori Yönetimi`.
-   [ ] Select "Konut > Satılık Daire".
-   [ ] Check "Bağlı Alanlar": Should list `m2_gross`, `room_count`, `heating_type`...

## 3. Form Simulation
-   [ ] (Mental Check): Frontend using this API would render:
    -   Dropdown for Room Count.
    -   Input for m².
    -   Checkbox for Balcony.

**Status:** PENDING
