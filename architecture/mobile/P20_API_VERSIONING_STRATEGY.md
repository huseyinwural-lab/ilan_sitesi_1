# P20: API Versioning Strategy (/api/v2/mobile)

## 1. Strategy: Separate Namespace
We will introduce a dedicated router prefix `/api/v2/mobile` for the mobile application.
- **Base URL**: `https://api.platform.com/api/v2/mobile`
- **Why?**: Allows breaking changes for mobile (which has slower update cycles) without affecting the Web Frontend (v1).

## 2. Directory Structure
```
backend/
└── app/
    └── routers/
        └── mobile/
            ├── __init__.py
            ├── auth_routes.py      # Mobile-specific Auth (JWT + Refresh)
            ├── listing_routes.py   # Optimized Feeds
            ├── user_routes.py      # Profile & Favorites
            └── affiliate_routes.py # Simple Stats
```

## 3. Versioning Rules
1.  **No Breaking Changes in v2**: Once published to App Store, v2 endpoints must remain backward compatible.
2.  **Additive Changes Only**: Adding fields is allowed. Removing/Renaming requires v3.
3.  **Deprecation**: If v3 is needed, v2 must be supported for at least 6 months.

## 4. Response Envelope (Standard)
All v2 endpoints must return data in this format:
```json
{
  "data": <Payload>,
  "meta": {
    "cursor": "next-page-token",
    "total": 100,
    "message": "Optional user-facing message"
  }
}
```

## 5. Error Envelope (Standard)
```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "İlan bulunamadı.",
    "trace_id": "req-12345"
  }
}
```
