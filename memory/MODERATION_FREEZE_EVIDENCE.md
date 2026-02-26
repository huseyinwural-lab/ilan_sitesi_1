# Moderation Freeze Evidence

**Environment:** https://grid-editor-preview.preview.emergentagent.com
**Listing (pending created via consumer publish flow):** d91de127-7397-4c6d-b1ed-e7556713591c

## UI Evidence (Screenshots)
- `/tmp/admin-freeze-settings-reason.jpg` – Admin System Settings: Moderation Freeze reason input + toggle.
- `/tmp/admin-moderation-freeze-banner.jpg` – Moderation queue banner with reason.
- `/tmp/privacy-export-history.jpg` – /account/privacy Export Geçmişi tab (history table).

## API Evidence

### Freeze OFF → Approve → 200 OK
```
HTTP/2 200 
date: Tue, 24 Feb 2026 16:07:17 GMT
content-type: application/json
content-length: 88
server: cloudflare
cf-ray: 9d3036f79c0789fd-ORD
cf-cache-status: DYNAMIC
access-control-allow-origin: *
cache-control: no-store, no-cache, must-revalidate
via: 1.1 google
access-control-allow-headers: *
access-control-allow-methods: GET, POST, PUT, DELETE, OPTIONS, HEAD, PATCH
access-control-max-age: 300
x-request-id: 40e5f042c4a84dc88adfa1cfe233f0f3
x-response-time-ms: 2585.61
set-cookie: __cf_bm=Hkk8cGeZ6bGE8qWvTCh1qnF3AuJ1dBxpXxiNFd4.ejs-1771949237-1.0.1.1-bkKxd4wjj_78yOo_mFdma20x9QTVhU1OVW2ypSRa3EPpozhs4yiuKUnqH.gOEhvfMC6TB2VX7wYptWaigQZZ5GopTJFtzHiGVtkRaPd9i.A; path=/; expires=Tue, 24-Feb-26 16:37:17 GMT; domain=.preview.emergentagent.com; HttpOnly; Secure; SameSite=None

{"ok":true,"listing":{"id":"d91de127-7397-4c6d-b1ed-e7556713591c","status":"published"}}
```

### Freeze ON → Approve → 423 Locked
```
HTTP/2 423 
date: Tue, 24 Feb 2026 16:07:22 GMT
content-type: application/json
content-length: 37
server: cloudflare
cf-ray: 9d30371d69424fa9-ORD
cf-cache-status: DYNAMIC
access-control-allow-origin: *
cache-control: no-store, no-cache, must-revalidate
via: 1.1 google
access-control-allow-headers: *
access-control-allow-methods: GET, POST, PUT, DELETE, OPTIONS, HEAD, PATCH
access-control-max-age: 300
x-request-id: b2f141064d5046bdbb5c0826ee8c32b8
x-response-time-ms: 1294.10
set-cookie: __cf_bm=RvBATqcBYJ5nMqwBR5HxAlq6QytPYPPK.dHfVmUKHnU-1771949242-1.0.1.1-Et5PzQgLC75c6dzLQBAPJFn78inVqH0GmkzE490.1bvYPX9Aqz.W.ehADHMaNhv2MoS_zn.EvieQpoiXEP06k6q0jtqu9Sq36pNxi0l.Qsw; path=/; expires=Tue, 24-Feb-26 16:37:22 GMT; domain=.preview.emergentagent.com; HttpOnly; Secure; SameSite=None

{"detail":"Moderation freeze active"}
```

## Audit Evidence (Reason logged)
```
[
  {
    "id": "65cdb5d7-5107-40d6-85fb-4d5b81f3e10b",
    "created_at": "2026-02-24T16:07:19.542097+00:00",
    "action": "MODERATION_FREEZE_ENABLED",
    "resource_type": "moderation_freeze",
    "resource_id": "42c974ee-394d-49b3-aad3-febb3b6aa3eb",
    "user_id": "9dbd1bdc-9d5a-401c-a650-29ffda5e6b55",
    "user_email": "admin@platform.com",
    "country_scope": null,
    "metadata": {
      "reason": "Evidence freeze on"
    }
  },
  {
    "id": "74d3b136-9661-4dbc-a1ad-30202dacccec",
    "created_at": "2026-02-24T16:04:45.339730+00:00",
    "action": "MODERATION_FREEZE_DISABLED",
    "resource_type": "moderation_freeze",
    "resource_id": "42c974ee-394d-49b3-aad3-febb3b6aa3eb",
    "user_id": "9dbd1bdc-9d5a-401c-a650-29ffda5e6b55",
    "user_email": "admin@platform.com",
    "country_scope": null,
    "metadata": {
      "reason": "Freeze kapatma testi"
    }
  },
  {
    "id": "b13be420-d339-485b-a1c1-fce9a005dfb6",
    "created_at": "2026-02-24T16:01:28.760115+00:00",
    "action": "MODERATION_FREEZE_ENABLED",
    "resource_type": "moderation_freeze",
    "resource_id": "42c974ee-394d-49b3-aad3-febb3b6aa3eb",
    "user_id": "9dbd1bdc-9d5a-401c-a650-29ffda5e6b55",
    "user_email": "admin@platform.com",
    "country_scope": null,
    "metadata": {
      "reason": "Maintenance freeze test"
    }
  }
]

```
