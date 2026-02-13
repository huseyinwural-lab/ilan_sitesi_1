# Vehicle String Fields Deprecation Plan

**Timeline:** Immediate

## Phase 1: Read-Only (Current)
-   Frontend should ignore `attributes.brand` and `attributes.model`.
-   Frontend MUST use `listing.make.name` and `listing.model.name` (via Expansion/Join).

## Phase 2: Write Block (Next Deploy)
-   Listing Create/Update API must require `make_id` and `model_id`.
-   Backend will populate `attributes` JSON for backward compatibility ONLY if needed (Legacy clients), otherwise stop writing strings.

## Phase 3: DB Drop (P+1)
-   Remove keys `brand` and `model` from `attributes` JSONB via migration script.
