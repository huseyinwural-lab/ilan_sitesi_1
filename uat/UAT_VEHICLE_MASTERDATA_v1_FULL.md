# UAT Vehicle Master Data v1 Full

**Env:** Staging

## 1. Data Integrity
-   [ ] Run `integrity_audit.py`. Result: 0 Errors.

## 2. User Flow
-   [ ] Create Listing: Select "Tesla" -> "Model 3". Save.
-   [ ] Search: Filter "Tesla". Result includes new listing.
-   [ ] Search: Filter "Model Y". Result excludes new listing.

## 3. Admin Flow
-   [ ] Admin sets "Model 3" to `is_active=false`.
-   [ ] User Form: "Model 3" removed from dropdown.
-   [ ] Existing Listing: Still displays "Model 3".

## 4. API Error Handling
-   [ ] Send `make_id` of "BMW" with `model_id` of "Civic".
-   [ ] Result: `400 Bad Request` or `422 Validation Error`.
