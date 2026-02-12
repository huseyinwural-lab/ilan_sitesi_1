# Migration: Add Tier to DealerPackage

**Version:** 2026_P6_S2_001
**Description:** Adds `tier` column to `dealer_packages` to support Tiered Rate Limiting.

## 1. Schema Change
```python
# Alembic Upgrade
op.add_column('dealer_packages', sa.Column('tier', sa.String(20), nullable=False, server_default='STANDARD'))
op.create_index('ix_dealer_packages_tier', 'dealer_packages', ['tier'])
```

## 2. Backfill Logic
-   Existing packages are mapped as follows:
    -   `BASIC` -> `STANDARD`
    -   `PRO` -> `PREMIUM`
    -   `ENTERPRISE` -> `ENTERPRISE`
-   *Note:* The server default sets everything to STANDARD. A data migration script is required immediately after schema change to correct PRO/ENTERPRISE.

## 3. Rollback Plan
```python
# Alembic Downgrade
op.drop_index('ix_dealer_packages_tier', 'dealer_packages')
op.drop_column('dealer_packages', 'tier')
```

## 4. Verification
-   Run `SELECT tier, count(*) FROM dealer_packages GROUP BY tier;`
-   Expected: Distribution across Standard/Premium/Enterprise matching current sales.
