# VEHICLE MASTER DATA — Storage Policy (REV‑B)

## 1) Temel karar
- Master data **repo içinde tutulmaz**.
- Production’da belirlenmiş bir **data directory** altında tutulur.

## 2) Varsayılan path standardı (LOCKED)
- Env var: `VEHICLE_MASTER_DATA_DIR`
- Varsayılan: `VEHICLE_MASTER_DATA_DIR=/data/vehicle_master`

## 3) Directory layout
Önerilen dizin yapısı:
```
/data/vehicle_master/
  current.json                 # aktif manifest pointer (atomik switch)
  versions/
    2026-02-17.1/
      manifest.json
      makes.json
      models.json
      validation_report.json
    2026-02-18.1/
      ...
  logs/
    audit.jsonl                # append-only audit log
    sync.jsonl                 # append-only sync log (opsional, aynı format)
```

## 4) Deployment pipeline ile güncelleme
- Artefact’ler CI/CD pipeline ile hedef sunucuya `/data/vehicle_master/versions/<version>/...` olarak taşınır.
- Aktivasyon işlemi yalnızca `current.json` pointer/manifest switch ile yapılır.

## 5) v2 notu
- Object storage (S3 uyumlu) entegrasyonu **v2’ye bırakılır**.
