# Seed Production Data v2 Changelog

**Changes in v2:**

## Added Attributes
-   Full Real Estate Suite (Global/Res/Comm).
-   Correct Data Types (Select, Boolean, Number).
-   Filters Configuration (Range, Multi-Select).

## Added Options (Multi-Lang)
-   `room_count`: 11 options (1+0 to 6+).
-   `building_status`: 3 options.
-   `heating_type`: 8 options.
-   `floor_location`: 11 options.
-   `ground_survey`: 2 options.

## Logic Improvements
-   **Upsert:** Checks `key` uniqueness before inserting.
-   **Translations:** Supports TR/DE/FR dicts for Labels and Options.
-   **Linking:** Smart mapping to Category Slugs.
