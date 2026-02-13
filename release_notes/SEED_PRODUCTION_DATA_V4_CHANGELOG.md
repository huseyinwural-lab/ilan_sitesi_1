# Seed Production Data v4 Changelog

**Target:** Vehicle Module

## 1. New Attributes
-   Added 25+ Vehicle-specific attributes.
-   Configured correct Data Types (Number, Boolean, Select).

## 2. New Options
-   Added ~50 localized options (Fuel types, Body types, etc.).

## 3. Structural Changes
-   Creates `commercial-vehicles` category branch if missing.
-   Updates bindings for existing `cars` and `motorcycles` categories.

## 4. Safety
-   `--allow-prod` required for Production.
-   Idempotent execution (Checks existence before Insert).
