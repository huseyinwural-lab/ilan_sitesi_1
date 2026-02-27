# UI Publish Hardening P0 — Evidence

Tarih: 2026-02-27

## Kapsam
- `config_version` zorunluluğu: **yeni** ve **legacy** publish endpoint
- Conflict kontratı: `409 CONFIG_VERSION_CONFLICT`
- Kısa publish lock: `409 PUBLISH_LOCKED`
- Dashboard publish öncesi görsel diff paneli (Önceki/Yeni Grid + highlight)
- Rollback reason zorunlu + audit metadata
- Legacy publish endpoint deprecated işaretleme

---

## 1) API Kontrat Kanıtı

### 1.1 Yeni endpoint version zorunluluğu
- Endpoint: `POST /api/admin/ui/configs/dashboard/publish`
- Senaryo: `config_version` yok
- Sonuç: `400 MISSING_CONFIG_VERSION`

Örnek response:
```json
{
  "detail": {
    "code": "MISSING_CONFIG_VERSION",
    "message": "config_version zorunludur",
    "hint": "Sayfayı yenileyin ve tekrar deneyin"
  }
}
```

### 1.2 Legacy endpoint version zorunluluğu
- Endpoint: `POST /api/admin/ui/configs/{config_type}/publish/{config_id}`
- Senaryo: body boş
- Sonuç: `400 MISSING_CONFIG_VERSION`

### 1.3 Version mismatch conflict
- Endpoint: `POST /api/admin/ui/configs/dashboard/publish`
- Senaryo: stale / yanlış `config_version`
- Sonuç: `409 CONFIG_VERSION_CONFLICT`

Örnek response:
```json
{
  "detail": {
    "code": "CONFIG_VERSION_CONFLICT",
    "message": "config_version güncel değil",
    "current_version": 1,
    "your_version": 10,
    "last_published_by": null,
    "last_published_at": null,
    "hint": "Sayfayı yenileyin ve diff ekranını tekrar kontrol edin"
  }
}
```

### 1.4 Publish lock race
- Senaryo: aynı scope için paralel publish
- Beklenen: bir çağrı `200`, diğer çağrı `409` (`CONFIG_VERSION_CONFLICT` veya `PUBLISH_LOCKED`)
- Sonuç: PASS

### 1.5 Rollback reason zorunluluğu
- Endpoint: `POST /api/admin/ui/configs/dashboard/rollback`
- Senaryo: `rollback_reason` yok
- Sonuç: `400 MISSING_ROLLBACK_REASON`

---

## 2) Frontend Kanıtı

### Corporate Dashboard Designer
- Publish dialog içinde görsel diff panelleri mevcut:
  - `Önceki Grid`
  - `Yeni Grid`
- Highlight:
  - Eklenen: yeşil
  - Kaldırılan: kırmızı
  - Taşınan: amber
- Publish request body içinde `config_version` gönderiliyor.
- Conflict dialog alanları doğrulandı:
  - `current_version`
  - `your_version`
  - `last_published_by`
  - `last_published_at`
- Conflict aksiyonları:
  - `Sayfayı Yenile`
  - `Diff Gör`

### Rollback UX
- `Son Snapshot’a Dön` hızlı butonu mevcut.
- Rollback dialogunda reason zorunlu:
  - reason boşken buton disabled
  - reason doluyken buton enabled

### Legacy publish UX yönlendirmesi
- Legacy publish akışında `MISSING_CONFIG_VERSION` durumunda kullanıcıya:
  - “Version bilgisi eksik. Lütfen sayfayı yenileyin ve tekrar deneyin.”

---

## 3) Test Kanıtı

### Pytest
- Komut:
  - `pytest -q backend/tests/test_p61_dashboard_backend.py backend/tests/test_p62_ui_publish_workflow.py backend/tests/test_p62_extended_dashboard_ui.py backend/tests/test_p63_logo_upload_contract.py backend/tests/test_p64_publish_hardening.py`
- Sonuç: `37 passed`

### Testing Agent
- Rapor: `/app/test_reports/iteration_30.json`
- Sonuç:
  - Backend: `100% (18/18 passed)`
  - Frontend: `100%` (publish hardening UI akışları verified)

### Frontend Testing Subagent
- Sonuç: `P64 Publish Hardening UI Validation - COMPLETE PASS`
- Kritik doğrulamalar:
  - görsel diff paneli
  - conflict dialog
  - rollback reason zorunluluğu
  - son snapshot quick action

---

## 4) Notlar
- Legacy publish endpoint route seviyesinde **deprecated** işaretlendi.
- Remove planı: **P2**.
- **MOCKED API YOK**.
