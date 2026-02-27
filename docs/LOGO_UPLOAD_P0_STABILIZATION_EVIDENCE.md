# Logo Upload P0 Stabilizasyon Kanıtı

Tarih: 2026-02-26

## 1) Hata Kanıtı Toplama (Network + Console + UI)

### Browser Network kaydı (ilgili endpoint)
- Endpoint: `POST /api/admin/ui/configs/header/logo`
- Status: `200`
- Response (özet): `ok=true`, `logo_url`, `logo_meta`, `storage_health`, `item`
- Playwright log:
  - `NETWORK_LOGO_UPLOAD_STATUS=200`
  - `NETWORK_LOGO_UPLOAD_BODY={"ok":true,...}`

Referans:
- Screenshot + log: `/root/.emergent/automation_output/20260226_234207/`

### Console log (upload sırasında JS error)
- Upload akışında kritik JS exception yok.
- Mevcut loglarda upload ile ilgisiz bazı `ERR_ABORTED`/hydration uyarıları görüldü (önceden var olan genel gürültü).

Referans:
- `/root/.emergent/automation_output/20260226_234207/console_20260226_234207.log`

### UI hata mesajı
- Inline error banner eklendi (summary + detail + code).
- Örnek (invalid type):
  - Summary: `Dosya formatı desteklenmiyor`
  - Detail: `Beklenen: png/svg/webp · Gelen: txt`
  - Code: `INVALID_FILE_TYPE`


## 2) Upload isteği backend’e ulaşıyor mu?

- Ulaşıyor: Evet (`POST /api/admin/ui/configs/header/logo` network kaydı mevcut).
- Event binding sorunu: Yok.


## 3) Validation Gate Kontratı (Backend + UI)

Yeni kontrat (response `detail.code`):
- Format gate → `INVALID_FILE_TYPE` (400)
- Size gate (>2MB) → `FILE_TOO_LARGE` (400)
- Aspect gate (3:1 ±%10 dışı) → `INVALID_ASPECT_RATIO` (400)

Örnek curl çıktıları:
- `invalid_type.txt` → 400
  - `{"detail":{"code":"INVALID_FILE_TYPE",...}}`
- `too_large.png` → 400
  - `{"detail":{"code":"FILE_TOO_LARGE",...}}`
- `invalid_ratio_2_5.png` → 400
  - `{"detail":{"code":"INVALID_ASPECT_RATIO",...}}`


## 4) Scope / Permission Kontrolü

- `scope=system + scope_id=tenant-001` gönderildiğinde backend normalize ediyor:
  - sonuç `scope=system`, `scope_id=null` (200)
- RBAC:
  - Admin token: upload açık
  - Dealer token: `403 Forbidden`


## 5) Storage hattı sağlamlaştırma

- Endpoint’e `storage_health` bilgisi eklendi.
- Yeni health endpoint:
  - `GET /api/admin/ui/logo-assets/health`
  - örnek: `{"ok":true,"storage_health":{"status":"ok","writable":true,...}}`
- Upload success response içinde `storage_health` dönüyor.
- 5xx pipeline senaryosu için backend kodu: `STORAGE_PIPELINE_ERROR`.


## 6) Preview + Cache Bust

- Upload sonrası preview URL cache-bust ile güncelleniyor (`?v=timestamp`).
- Kanıt:
  - `PREVIEW_SRC=/api/site/assets/ui/logos/...png?v=1772149442262`

Referans:
- Screenshot + log: `/root/.emergent/automation_output/20260226_234349/`


## 7) Publish sonrası canlı header görünümü

- Admin publish sonrası dealer canlı header’da logo görünümü doğrulandı.
- Kanıt:
  - `DEALER_HEADER_LOGO_SRC=/api/site/assets/ui/logos/bf33d985-3997-435c-bc99-136858b3931e.png`

Referans:
- Screenshot + log: `/root/.emergent/automation_output/20260226_234322/`


## 8) Kapanış Test Paketi

### Dosya seti
- Geçerli: `valid_3x1.png`, `boundary_low_2_7.png`, `boundary_high_3_3.webp`
- Geçersiz format: `invalid_type.txt`
- >2MB: `too_large.png`
- Aspect dışı: `invalid_ratio_2_5.png`

### Otomasyon raporu
- Testing agent: `/app/test_reports/iteration_29.json`
  - Backend + Frontend PASS
  - Kontrat, UI banner, cache bust, publish->dealer header PASS

### Ek pytest
- `backend/tests/test_p63_logo_upload_contract.py`
- `backend/tests/test_p60_corporate_header_logo.py`
- Güncel koşum: `test_p63_logo_upload_contract.py` → **9 passed** (3:1 + sınır 2.7/3.3 kabul testleri dahil)
