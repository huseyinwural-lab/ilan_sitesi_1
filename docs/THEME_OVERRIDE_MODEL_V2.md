# THEME_OVERRIDE_MODEL_V2

Tarih: 2026-02-27  
Faz: P0 Theme Override Model Netleştirme

## 1) Kapsam

Tema çözümleme iki katmana sabitlendi:

1. **Global Theme** (system)
2. **Dealer Override Theme** (tenant)

Precedence (deterministik):

`Dealer Override > Global Theme`

User/site-level override (scope=`user`) artık desteklenmez.

---

## 2) Yetki ve Scope Kuralları

Geçerli assignment scope:
- `system`
- `tenant`

Geçersiz assignment scope:
- `user` → `400 INVALID_THEME_SCOPE`

---

## 3) Resolution Algoritması

1. System assignment ile global theme bulunur (yoksa active fallback)
2. Tenant assignment varsa dealer theme bulunur
3. Resolved tokens, deep-merge ile üretilir:
   - base = global tokens
   - override = dealer tokens
4. Resolved snapshot hash üretilir (`resolved_config_hash`)

Output:
- `tokens` (fully resolved)
- `resolution.mode`
- `resolution.global_theme_id`
- `resolution.dealer_theme_id`
- `resolution.resolved_config_hash`
- `resolution.precedence = dealer_override > global_theme`

---

## 4) Publish/Assign Validation

Tenant override assignment için:
- Global theme dependency zorunlu (yoksa `400 INVALID_THEME_SCOPE`)
- Override token path’leri global token path dışında olamaz
  - ihlal: `400 INVALID_THEME_SCOPE`

Amaç:
- Scope dışı override publish’ini bloklamak
- Deterministik çözümleme sağlamak

---

## 5) Site-Level Override Alanları için Migration Planı (Plan, Kod Değil)

### Adım 1 (Şimdi)
- `user` scope assignment create/update kapalı
- Mevcut `user` scope kayıtları **deprecated + read-only**

### Adım 2 (P2)
- API level legacy desteği tamamen kaldırılır
- Read path’te `user` scope tamamen ignore edilir

### Adım 3 (P2/P3)
- DB cleanup migration:
  - `user` scope assignment kayıtları arşivlenir/silinir
  - Endpoint kontratından user scope referansları kaldırılır

---

## 6) Backward Compatibility Timeline

- Şu an: `user` scope yazma kapalı, legacy kayıtlar okunabilir metadata ile görülebilir
- P2: user scope endpoint kontratından çıkarılacak
- P2 sonrası: tek model (global + dealer override)

---

## 7) Faz-2 Sonuç

- Theme çözümleme deterministik hale geldi.
- Override modeli sadeleşti.
- Scope dışı override publish riski kontrat bazlı engellendi.
