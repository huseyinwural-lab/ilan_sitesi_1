# P1 Meilisearch Config History — Evidence

Tarih: 2026-02-26

## 1) Backend Config Kontratı (Manual + History)

### Persist edilen şema (versioned)
- `meilisearch_configs`
  - `id`
  - `created_at`
  - `updated_at`
  - `created_by`
  - `meili_url`
  - `meili_index_name` (default: `listings_index`)
  - `meili_master_key_ciphertext` (**şifreli**, plaintext tutulmaz)
  - `status` (`active | inactive | revoked`)
  - `last_tested_at`
  - `last_test_result` (`PASS/FAIL + reason_code + message`)

### API uçları
- `GET /api/admin/system-settings/meilisearch`
  - Aktif konfig + encryption-key var/yok bilgisi
- `GET /api/admin/system-settings/meilisearch/history`
  - Geçmiş listesi (key **maskeli**, ciphertext dönmez)
- `POST /api/admin/system-settings/meilisearch`
  - Yeni konfig kaydı oluşturur (`inactive`)
- `POST /api/admin/system-settings/meilisearch/{id}/test`
  - Bağlantı/index testini çalıştırır, `last_test_result` günceller
- `POST /api/admin/system-settings/meilisearch/{id}/activate`
  - Önce test çalıştırır; yalnızca `PASS` ise aktive eder
- `POST /api/admin/system-settings/meilisearch/{id}/revoke`
  - Konfigi `revoked` yapar

### Aktivasyon kapısı
- Kaydetmek tek başına aktivasyon sağlamaz.
- Aktivasyon endpointi test sonucu `PASS` değilse `ok=false` döner ve konfig aktifleşmez.

### RBAC
- Bu endpointler `super_admin` (System Admin) ile sınırlıdır.

---

## 2) UI Evidence (System Settings)

Konum: `Admin Panel -> System Settings`

Yeni kart:
- `Search / Meilisearch`
- Sekmeler:
  - `Aktif Konfig`
  - `Geçmiş`

UI güvenlik davranışı:
- Master key input her zaman boş/maskeli başlar.
- Geçmişte key yalnızca `••••` olarak görünür.
- Geçmişten yeniden aktivasyonda key UI’ya geri basılmaz.

Smoke doğrulama:
- Screenshot smoke PASS (`system-settings-meili-card` görüldü).

---

## 3) PASS/FAIL + Rollback Senaryosu

### Test setup
- Geçici local mock Meilisearch (`http://127.0.0.1:17700`) ile PASS senaryosu
- Geçersiz host ile FAIL senaryosu

### Sonuçlar
- `create_pass_cfg` => `201`
- `activate_pass_cfg` => `200`, `ok=true`, `result.status=PASS`
- `create_fail_cfg` => `201`
- `activate_fail_cfg` => `200`, `ok=false`, `reason_code=connection_error`
- `active_config_after_fail` => önceki PASS config id’si korunuyor
- `rollback_kept_previous_active` => `True`

Bu, “geçmişten reuse/rollback” davranışının ve aktivasyon kapısının çalıştığını doğrular.

---

## 4) Güvenlik ve Log Doğrulaması

- API history cevabında `meili_master_key_ciphertext` dönmüyor.
- API history cevabında yalnızca `master_key_masked: ••••` dönüyor.
- Loglarda plaintext master key tespit edilmedi (`dummy_key_...`, `local_test_master` aranarak kontrol edildi).
- Audit olayları yazılıyor:
  - `MEILI_CONFIG_CREATE`
  - `MEILI_CONFIG_TEST`
  - `MEILI_CONFIG_ACTIVATE` / `MEILI_CONFIG_ACTIVATE_REJECTED`
  - `MEILI_CONFIG_REVOKE`
