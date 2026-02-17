# VEHICLE MASTER DATA — File‑Based Versioning & Rollback v1

## 1) Versioning modeli
- Her import/aktivasyon **yeni bir version** üretir: `version_id`.
- Version klasörü: `versions/<version_id>/`.

## 2) Aktif versiyon (current manifest)
- Aktif versiyon `current.json` ile belirlenir.
- `current.json` içeriği minimal bir pointer’dır:
```json
{
  "active_version": "2026-02-17.1",
  "activated_at": "2026-02-17T12:30:00Z",
  "activated_by": "<admin_user_id>",
  "source": "manual-upload",
  "checksum": "<sha256>"
}
```

## 3) Atomik switch
- Aktivasyon: yeni `current.json` önce temp olarak yazılır, sonra **atomic rename** ile yer değiştirir.
- Böylece yarım yazılmış pointer ile servis edilmez.

## 4) Rollback
- Rollback: `current.json` içindeki `active_version` önceki bir versiyona atomik olarak switch edilir.
- Rollback işlemi audit log’a yazılır.

## 5) Retention (ops kuralı)
- Varsayılan retention: son **N=10** versiyon saklanır.
- Daha eskileri ops script ile temizlenir (v1’de manuel operasyon).
