# ADMIN_COUNTRY_CONTEXT_V2_API_NOTES

- Country-aware filtering currently implemented on:
  - GET /api/users?country=XX
  - GET /api/dashboard/stats?country=XX

- Validation:
  - invalid country => 400
  - scope forbidden => 403
