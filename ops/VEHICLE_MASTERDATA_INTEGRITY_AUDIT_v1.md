# Vehicle Master Data Integrity Audit v1

**Scope:** Validate Relational Integrity of Vehicle Listings.
**Status:** PENDING

## 1. Mandatory Checks (SQL)
- [ ] `SELECT count(*) FROM listings WHERE module='vehicle' AND make_id IS NULL` => **Target: 0**
- [ ] `SELECT count(*) FROM listings WHERE module='vehicle' AND model_id IS NULL` => **Target: 0**
- [ ] **Cross-Check:**
    ```sql
    SELECT count(*) 
    FROM listings l
    JOIN vehicle_models m ON l.model_id = m.id
    WHERE l.make_id != m.make_id;
    ```
    => **Target: 0** (Ensures Model actually belongs to the Make).

## 2. Orphan Check
- [ ] `SELECT count(*) FROM vehicle_models WHERE make_id NOT IN (SELECT id FROM vehicle_makes)` => **Target: 0**

## 3. Data Type Check
- [ ] `listing.make_id` is proper UUID.
- [ ] `listing.model_id` is proper UUID.
