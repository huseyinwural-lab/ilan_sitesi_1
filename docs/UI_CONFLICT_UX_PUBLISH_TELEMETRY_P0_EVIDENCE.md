# UI_CONFLICT_UX_PUBLISH_TELEMETRY_P0_EVIDENCE

Tarih: 2026-02-27

## Kapsam
- Conflict UX tek aksiyon senkronizasyonu
- Publish dialog auto-reopen
- Version drift guard (hash tabanlı)
- Auto-draft sync event log
- Publish attempt telemetry + admin audit görünürlüğü
- Concurrency deterministiklik doğrulamaları

---

## 1) Conflict UX (Tek Aksiyon)

### 1.1 Primary aksiyon
- Conflict dialog primary button:
  - `Latest Draft’ı Çek + Diff’i Yeniden Aç`
  - testid: `ui-designer-dashboard-conflict-sync-and-reopen-button`

Davranış:
1. `POST /api/admin/ui/configs/dashboard/conflict-sync`
2. Latest draft local state’e replace
3. Diff verisi güncellenir
4. Publish dialog otomatik yeniden açılır

### 1.2 Manual refresh kaldırma
- Eski “yenile + ayrı diff aç” akışı yerine tek akış uygulanmıştır.

---

## 2) Version Drift Guard

- UI’da `local_hash` ve `server_hash` gösterimi aktif.
- Hash mismatch durumunda publish disable edilir:
  - Mesaj: `Draft hash mismatch: latest draft senkronizasyonu gerekli`

Backend guard:
- `resolved_config_hash` publish öncesi doğrulanır.
- Mismatch -> `409 CONFIG_HASH_MISMATCH`

---

## 3) Auto-Draft Sync Event Log

Yeni event/action kayıtları:
- `DRAFT_UPDATED`
- `DRAFT_SYNCED_AFTER_CONFLICT`

Metadata alanları:
- `actor_id`
- `owner_type`
- `owner_id`
- `previous_version`
- `new_version`
- `timestamp`

---

## 4) Publish Attempt Telemetry

Audit action:
- `ui_config_publish_attempt`

Telemetry alanları:
- `conflict_detected`
- `lock_wait_ms`
- `retry_count`
- `publish_duration_ms`

API:
- `GET /api/admin/ui/configs/{config_type}/publish-audits`

Response telemetry:
- `avg_lock_wait_ms`
- `max_lock_wait_ms`
- `avg_publish_duration_ms`
- `max_publish_duration_ms`

UI görünürlüğü:
- Corporate Dashboard Designer içinde `Publish Audit` kartı
- Conflict badge, retry sayısı, lock süresi gösterimi

---

## 5) Deterministik Concurrency Sonuçları

Parallel publish senaryosu:
- Beklenen: 1 success + 1 conflict/lock
- Sonuç: PASS

Hash edge-case:
- resolved hash mismatch -> blok
- Sonuç: PASS (`409 CONFIG_HASH_MISMATCH`)

---

## 6) Test Kanıtı

### Testing agent
- Rapor: `/app/test_reports/iteration_32.json`
- Sonuç:
  - Backend: `100% (7/7)`
  - Frontend: `100%` (conflict UX + audit panel + drift guard)

### Pytest (self-test)
- `backend/tests/test_p66_conflict_ux_telemetry.py` (PASS)
- `backend/tests/test_p64_publish_hardening.py` (PASS)
- Geniş regresyon seti: PASS

---

## 7) Faz Sonucu

- Conflict çözümü tek aksiyonla tamamlanır hale geldi.
- Publish retry süreci sürtünmesiz ve ölçülebilir.
- Concurrency deterministikliği telemetry ile doğrulanabilir hale geldi.

**MOCKED API YOK**
