# HEADER_ARCHITECTURE_V2

Tarih: 2026-02-27  
Faz: P0 Header Mimari Sadeleştirme

## 1) Hedef Mimari

Header sahiplik modeli iki katmana indirildi:

1. **Global Header** (owner_type=`global`, owner_id=`global`)
2. **Dealer Override Header** (owner_type=`dealer`, owner_id=`tenant_id`)

`Individual/site-level header editor` devre dışı bırakıldı.

---

## 2) Yetki Matrisi

| Persona | Admin edit endpoint | Effective corporate header (`/api/ui/header?segment=corporate`) |
|---|---|---|
| Admin UI Designer | ✅ (corporate header) | ❌ `403 UNAUTHORIZED_SCOPE` |
| Dealer | ❌ (admin endpoint) | ✅ |
| Anonymous / Public | ❌ | ❌ `403 UNAUTHORIZED_SCOPE` |

Ek kural:
- Individual header admin endpointleri: `403 FEATURE_DISABLED`

---

## 3) Publish Akışı (Scope-Aware)

Header publish için zorunlu payload:
- `config_version`
- `owner_type`
- `owner_id`

Endpointler:
- Yeni: `POST /api/admin/ui/configs/{config_type}/publish`
- Legacy: **kaldırıldı** (`POST /api/admin/ui/configs/{config_type}/publish/{config_id}` artık yok)

Doğrulamalar:
1. `config_version` yoksa → `400 MISSING_CONFIG_VERSION`
2. Versiyon güncel değilse → `409 CONFIG_VERSION_CONFLICT`
3. owner scope uyuşmazsa → `409 SCOPE_CONFLICT`
4. Paralel publish lock çakışması → `409 PUBLISH_LOCKED`

---

## 4) Snapshot Scope Yapısı (Immutable)

Publish response `snapshot` alanı:
- `owner_type` (zorunlu)
- `owner_id` (zorunlu)
- `config_version` (zorunlu)
- `resolved_config_hash` (zorunlu, SHA256)

Audit metadata içine de snapshot yazılır.

Amaç:
- Yanlış scope publish riskini önlemek
- Audit/replay güvenliğini artırmak

---

## 5) Bireysel Header Editor Durumu

- Admin UI’dan kaldırıldı.
- Backend admin header endpointlerinde `segment=individual` talepleri hard-disabled:
  - `403 FEATURE_DISABLED`
- Runtime `segment=individual` effective header: statik public default model.

---

## 6) Faz-1 Sonuç

- Header edit akışı artık yalnızca global + dealer override modeline bağlı.
- Publish scope enforcement aktif.
- Snapshot güvenliği scope-aware ve immutable hale getirildi.
