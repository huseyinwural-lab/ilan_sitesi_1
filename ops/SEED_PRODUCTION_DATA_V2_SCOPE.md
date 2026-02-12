# Seed Production Data v2 Scope

**Version:** v2.0
**Target:** Real Estate Attributes (Full Set)

## 1. Included Attributes (Upsert)
-   **Global:** `m2_gross`, `m2_net`, `building_status`, `heating_type`, `eligible_for_bank`, `swap_available`, `dues`.
-   **Residential:** `room_count`, `floor_location`, `bathroom_count`, `balcony`, `furnished`, `in_complex`.
-   **Commercial:** `ceiling_height`, `entrance_height`, `power_capacity`, `crane`, `is_transfer`, `ground_survey`.

## 2. Localization
-   **Languages:** TR, DE, FR (for all Labels and Options).
-   **Source:** `/app/i18n/REAL_ESTATE_ATTRIBUTE_OPTIONS_TR_DE_FR.md`.

## 3. Bindings
-   Link Global -> `real_estate` (Module Root).
-   Link Residential -> `housing` (and subs).
-   Link Commercial -> `commercial` (and subs).

## 4. Exclusion
-   Vehicle attributes (v1 remains, or update if needed later).
-   Shopping attributes.
