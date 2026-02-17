## Public Report Submit (v1)

### Endpoint
`POST /api/reports`

### Payload
```json
{
  "listing_id": "...",
  "reason": "spam",
  "reason_note": "optional"
}
```

### Rate Limit
- 10 dakika pencerede 5 istek (IP + listing + user bazlı)

### Kurallar
- `other` reason için `reason_note` zorunlu

### Response
```json
{"ok": true, "report_id": "...", "status": "open"}
```
