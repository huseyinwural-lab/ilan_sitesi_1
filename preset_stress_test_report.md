# preset_stress_test_report.md

- Tarih: 2026-03-07T11:03:19.215957Z
- Batch: 100 preset job simülasyonu (lite profile)
- Max network retry: 3

## 1) Genel Sonuç

- Success: **100**
- Failure: **0**
- Success ratio: **100.0%**

## 2) Senaryo Sonuçları

| Senaryo | Toplam | Başarılı | Başarısız | Ortalama Süre (ms) |
|---|---:|---:|---:|---:|
| normal_success | 10 | 10 | 0 | 4453.2 |
| duplicate_run | 10 | 10 | 0 | 4170.6 |
| partial_success | 5 | 5 | 0 | 6143.6 |
| validation_error | 55 | 55 | 0 | 1022.31 |
| timeout_fail_fast | 10 | 10 | 0 | 3.1 |
| network_retry | 10 | 10 | 0 | 16.4 |

## 3) Beklenen Senaryo Doğrulaması

- timeout → fail-fast: **10/10 PASS**
- partial success → raporlanır: **5/5 PASS**
- network retry → max retry uygulanır: **10/10** (max=3)
- duplicate run → idempotent: **10/10** (created_pages≈0 %100.0)

## 4) Error Sınıflandırması

| Sınıf | Adet |
|---|---:|
| timeout | 20 |
| validation | 55 |
| data conflict | 0 |
| system error | 5 |

## 5) İlk 20 Başarısız Satır

| # | scenario | http | class | detail |
|---:|---|---:|---|---|