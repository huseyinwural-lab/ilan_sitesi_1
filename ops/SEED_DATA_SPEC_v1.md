# Seed Data Spec v1

**Scope:** Populating Admin UI with realistic dummy data.
**Target Env:** Local / Staging (NEVER PROD)

## 1. Individual Users (20)
-   **Distribution:**
    -   10 Germany (DE)
    -   6 Turkey (TR)
    -   4 France (FR)
-   **Status:**
    -   70% Verified & Active
    -   20% Unverified (Email pending)
    -   10% Suspended (For testing filters)

## 2. Commercial Members (10 Dealers)
-   **Type:** 5 Auto Gallery, 5 Real Estate Agency.
-   **Tiers:**
    -   6 **STANDARD** (Small dealers)
    -   3 **PREMIUM** (Mid-size)
    -   1 **ENTERPRISE** (Large chain)
-   **Subscriptions:** All must have an active subscription linked to a `DealerPackage` matching their Tier.

## 3. Listings (40)
-   **Distribution:**
    -   Real Estate: 15
    -   Vehicles: 15
    -   Shopping: 10
-   **Status Lifecycle:**
    -   60% Active (Published)
    -   25% Pending (Moderation Queue)
    -   15% Rejected (Abuse testing)
-   **Ownership:** Linked randomly to the 10 Dealers and 5 of the Individual users.

## 4. Dependencies
-   **Prerequisite:** `seed_production_data.py` MUST be run first to create Dealer Packages.
