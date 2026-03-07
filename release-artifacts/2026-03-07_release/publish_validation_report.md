# publish_validation_report.md

- Tarih: 2026-03-07T11:10:01.875360Z
- Module: global
- Hedef Ülkeler: TR, DE, FR

## 1) Final Publish Doğrulama (#612/#198)

| Kontrol | Beklenen | Sonuç |
|---|---|---|
| Page publish | başarı | ✅ (HTTP 200) |
| route oluşumu | doğru slug route'ları | ✅ (6/6 route HTTP 200) |
| cache invalidation | tetiklenmiş | ✅ (önce: cache -> sonra: default/cache) |
| locale fallback | doğru | ✅ (es header ile country resolve korundu) |

## 2) TR/DE/FR Publish Checklist (canlı veri)

- Verify ready_ratio: **100.0%**
- Missing rows: **0**
- not-ready satır temizliği: **tamamlandı**

| Country | Page Type | HTTP | Source | Revision |
|---|---|---:|---|---|
| TR | home | 200 | default | 59e4ff35-912f-4f83-9323-13b3f7ca0a75 |
| TR | search_ln | 200 | default | 71415b1e-6f10-4558-b212-84d48fbf4438 |
| TR | urgent_listings | 200 | default | d551a0fa-d1c6-4cec-88e5-35994d714354 |
| TR | category_l0_l1 | 200 | default | 584ae625-08ff-46b0-aa69-0d1a6fd276df |
| DE | home | 200 | default | 69525e4e-006d-4244-9ade-03f652e361e7 |
| DE | search_ln | 200 | default | 38e88951-c1f8-4616-a801-e567a5796889 |
| DE | urgent_listings | 200 | default | 751b3a43-9f0d-489f-b2f0-c000da3dede3 |
| DE | category_l0_l1 | 200 | default | 18e3f9de-85c6-464a-9145-c72ab56a6f44 |
| FR | home | 200 | default | 7b6d1f30-55ea-4606-8e2a-9220d35ee7b6 |
| FR | search_ln | 200 | default | a8ce99f0-c411-4dfa-9030-fe27c35aea97 |
| FR | urgent_listings | 200 | default | dea138bf-226e-4fc8-9e5b-f65dfb8a9565 |
| FR | category_l0_l1 | 200 | default | f7208bb3-dbc7-4982-bd68-e1bbb8cb1931 |

## 3) Route Doğrulaması (slug/route contract)

| Route | HTTP |
|---|---:|
| /tr | 200 |
| /de | 200 |
| /fr | 200 |
| /tr/liste | 200 |
| /de/liste | 200 |
| /fr/liste | 200 |

## 4) Publish Log Snapshot

```log
INFO:     10.64.128.6:37632 - "GET /api/site/content-layout/resolve?page_type=home&country=TR&module=global HTTP/1.1" 200 OK
INFO:     10.64.131.171:35768 - "GET /api/site/content-layout/resolve?page_type=search_ln&country=TR&module=global HTTP/1.1" 200 OK
INFO:     10.64.131.171:35768 - "GET /api/site/content-layout/resolve?page_type=urgent_listings&country=TR&module=global HTTP/1.1" 200 OK
INFO:     10.64.128.6:37632 - "GET /api/site/content-layout/resolve?page_type=category_l0_l1&country=TR&module=global HTTP/1.1" 200 OK
INFO:     10.64.131.171:35768 - "GET /api/site/content-layout/resolve?page_type=home&country=DE&module=global HTTP/1.1" 200 OK
INFO:     10.64.131.171:35768 - "GET /api/site/content-layout/resolve?page_type=search_ln&country=DE&module=global HTTP/1.1" 200 OK
INFO:     10.64.131.171:35768 - "GET /api/site/content-layout/resolve?page_type=urgent_listings&country=DE&module=global HTTP/1.1" 200 OK
INFO:     10.64.128.6:37632 - "GET /api/site/content-layout/resolve?page_type=category_l0_l1&country=DE&module=global HTTP/1.1" 200 OK
INFO:     10.64.128.6:37632 - "GET /api/site/content-layout/resolve?page_type=home&country=FR&module=global HTTP/1.1" 200 OK
INFO:     10.64.128.6:37632 - "GET /api/site/content-layout/resolve?page_type=search_ln&country=FR&module=global HTTP/1.1" 200 OK
INFO:     10.64.131.171:35768 - "GET /api/site/content-layout/resolve?page_type=urgent_listings&country=FR&module=global HTTP/1.1" 200 OK
INFO:     10.64.131.171:35768 - "GET /api/site/content-layout/resolve?page_type=category_l0_l1&country=FR&module=global HTTP/1.1" 200 OK
INFO:     10.64.131.171:35768 - "GET /api/site/content-layout/resolve?page_type=home&country=TR&module=global HTTP/1.1" 200 OK
INFO:     10.64.128.6:40390 - "GET /api/site/content-layout/resolve?page_type=home&country=TR&module=global HTTP/1.1" 200 OK
INFO:     10.64.131.171:35768 - "POST /api/admin/site/content-layout/preset/install-standard-pack HTTP/1.1" 200 OK
INFO:     10.64.128.6:50124 - "GET /api/site/content-layout/resolve?page_type=home&country=TR&module=global HTTP/1.1" 200 OK
INFO:     10.64.131.171:35768 - "GET /api/site/content-layout/resolve?page_type=home&country=TR&module=global HTTP/1.1" 200 OK
INFO:     10.64.128.6:50124 - "GET /api/site/content-layout/resolve?page_type=home&country=TR&module=global HTTP/1.1" 200 OK
INFO:     10.64.131.171:35768 - "GET /api/site/content-layout/resolve?page_type=home&country=DE&module=global HTTP/1.1" 200 OK
INFO:     10.64.128.6:50124 - "GET /api/site/content-layout/resolve?page_type=home&country=FR&module=global HTTP/1.1" 200 OK
```

## 5) Sonuç

- Publish pipeline genel durum: **PASS**
- Rapor dosyası faz kapanış kanıtı olarak üretildi.