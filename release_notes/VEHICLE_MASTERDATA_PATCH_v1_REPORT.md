# Vehicle Master Data Patch v1

**Type:** Data Correction
**Scope:** Staging Data Clean-up

## Actions
-   **No Schema Change.**
-   **No New Master Data:** We will NOT insert "Model 123" into `vehicle_models` table.
-   **Data Mutation:** We will mutate the *Listings* to point to valid Models.

## Rationale
The unmapped listings are artifacts of a random seed script. They do not represent real user data worth preserving. "Fixing forward" by aligning them to valid Master Data is the cleanest approach.
