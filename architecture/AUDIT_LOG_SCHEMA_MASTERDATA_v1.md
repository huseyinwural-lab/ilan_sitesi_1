# Audit Log Schema MasterData v1

**Event:** `ADMIN_UPDATE_MASTERDATA`

## Schema
```json
{
  "action": "ADMIN_UPDATE_MASTERDATA",
  "resource_type": "attribute", // or "option", "binding"
  "resource_id": "uuid",
  "user_id": "uuid",
  "user_email": "admin@platform.com",
  "old_values": { "is_filterable": false },
  "new_values": { "is_filterable": true },
  "ip_address": "1.2.3.4"
}
```

## Logic
-   **Diff:** Controller MUST compute diff before commit.
-   **Failure:** If Audit insert fails, DB transaction MUST rollback.
