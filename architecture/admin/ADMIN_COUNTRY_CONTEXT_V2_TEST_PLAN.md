# ADMIN_COUNTRY_CONTEXT_V2_TEST_PLAN

## Backend
- /api/users global
- /api/users?country=DE => 200
- /api/users?country=ZZ => 400
- country_admin scope=['DE'] ile /api/users?country=FR => 403

## Frontend
- Toggle global<->country URL update
- Country dropdown URL update
- Deep link /admin/users?country=DE => UI DE
