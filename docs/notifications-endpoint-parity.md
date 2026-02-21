# Notifications Endpoint Parity Checklist

## Endpoint: `GET /api/v1/notifications`
**Auth:** `require_portal_scope("account")`

**Response (schema)**
- `items[]`:
  - `id` (uuid)
  - `user_id` (uuid)
  - `title` (string | null)
  - `message` (string)
  - `source_type` (string | null)
  - `source_id` (string | null)
  - `action_url` (string | null)
  - `payload_json` (object)
  - `dedupe_key` (string | null)
  - `read_at` (iso | null)
  - `delivered_at` (iso | null)
  - `created_at` (iso)
  - `is_read` (boolean)
- `pagination`:
  - `total` (int)
  - `page` (int)
  - `limit` (int)

**Query Params**
- `page` (default=1)
- `limit` (default=30, max=100)
- `unread_only` (default=false)

## Endpoint: `POST /api/v1/notifications/{notification_id}/read`
**Auth:** `require_portal_scope("account")`

**Response**
- `ok` (boolean)
- `notification` (same item schema)

## Pagination/Ordering
- Order: `created_at DESC`
- Pagination: `offset/limit`

## Permissions
- User can only access their own notifications.
- Unauthorized access → `403 Forbidden`.
