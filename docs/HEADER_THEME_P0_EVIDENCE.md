# HEADER + THEME P0 SIMPLIFICATION EVIDENCE

Tarih: 2026-02-27

## Özet

Bu iterasyonda Faz 1 (Header Mimari Sadeleştirme) + Faz 2 (Theme Override Model) P0 kapanışı yapıldı.

Ana çıktılar:
- Individual header edit akışı sistemden kaldırıldı (UI + backend hard disable).
- Corporate header effective erişimi dealer scope ile sınırlandı.
- Header publish snapshot scope-aware ve immutable hale getirildi.
- Theme precedence sabitlendi: `Dealer Override > Global Theme`.
- User/site-level theme scope yazımı kontrat bazlı kapatıldı.

---

## 1) Header Fazı Kanıtları

### 1.1 Individual header endpoint hard-disable
- `POST /api/admin/ui/configs/header` (segment=individual) -> `403 FEATURE_DISABLED`
- `GET /api/admin/ui/configs/header` (segment=individual) -> `403 FEATURE_DISABLED`

### 1.2 Corporate header access scope enforcement
- `GET /api/ui/header?segment=corporate`
  - anonymous -> `403 UNAUTHORIZED_SCOPE`
  - admin token -> `403 UNAUTHORIZED_SCOPE`
  - dealer token -> `200 OK`

### 1.3 Publish snapshot scope validation
- Header publish payload zorunlu:
  - `config_version`
  - `owner_type`
  - `owner_id`
- Scope mismatch -> `409 SCOPE_CONFLICT`
- Success snapshot alanları:
  - `owner_type`
  - `owner_id`
  - `config_version`
  - `resolved_config_hash` (SHA256)

---

## 2) Theme Fazı Kanıtları

### 2.1 Scope modeli sadeleşmesi
- Theme assignment sadece `system` ve `tenant`
- `scope=user` -> `400 INVALID_THEME_SCOPE`

### 2.2 Deterministik precedence
- Effective resolution: `Dealer Override > Global Theme`
- Effective payload içinde:
  - resolved `tokens`
  - `resolution.precedence`
  - `resolution.resolved_config_hash`

### 2.3 Publish/assign validation
- Dealer override için global dependency zorunlu
- Override token path’leri global dışında olamaz (invalid ise `400 INVALID_THEME_SCOPE`)

---

## 3) UI Kanıtları

- Admin UI Designer sekmeleri:
  - `Kurumsal Dashboard V2`
  - `Kurumsal Header Tasarım`
  - `Tema Yönetimi`
- `Bireysel Header Tasarım` sekmesi kaldırıldı.
- Theme scope dropdown: `system`, `tenant` (user kaldırıldı).

---

## 4) Test Kanıtları

### Pytest (Self-test)
- `backend/tests/test_p60_corporate_header_logo.py`
- `backend/tests/test_p61_dashboard_backend.py`
- `backend/tests/test_p62_ui_publish_workflow.py`
- `backend/tests/test_p62_extended_dashboard_ui.py`
- `backend/tests/test_p63_logo_upload_contract.py`
- `backend/tests/test_p64_publish_hardening.py`
- `backend/tests/test_p65_header_theme_v2.py`

Sonuç:
- PASS (self-test)

### Testing Agent
- Rapor: `/app/test_reports/iteration_31.json`
- Sonuç:
  - Backend: `100%`
  - Frontend: `100%`

---

## 5) Doküman Çıktıları

- `/app/docs/HEADER_ARCHITECTURE_V2.md`
- `/app/docs/THEME_OVERRIDE_MODEL_V2.md`
- `/app/docs/HEADER_THEME_P0_EVIDENCE.md` (bu dosya)

---

## 6) Not

- Legacy publish endpoint (`/publish/{config_id}`) deprecated olarak işaretli, remove planı: **P2**.
- **MOCKED API YOK**.
