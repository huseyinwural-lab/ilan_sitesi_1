# User DB Migration Plan (U1)

## 1. Değişiklikler
`users` tablosuna aşağıdaki kolonlar eklenecek (Eğer yoksa):

```sql
ALTER TABLE users ADD COLUMN kyc_status VARCHAR(20) DEFAULT 'none';
ALTER TABLE users ADD COLUMN default_country VARCHAR(5) DEFAULT 'DE';
ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT FALSE;
-- user_type P28'den zaten var, kontrol edilecek.
-- phone_verified P27'de is_phone_verified olarak eklendi, standardize edilecek.
```

## 2. Backfill Stratejisi
*   **Mevcut Kullanıcılar**:
    *   `kyc_status` -> `none`
    *   `default_country` -> `DE` (veya mevcut veriden çıkarım)
    *   `email_verified` -> `True` (Eski kullanıcılar için varsayım veya `is_verified` alanından taşıma)

## 3. Indexler
*   `ix_users_kyc_status`: Admin panelinde filtreleme için.
*   `ix_users_country`: Bölgesel raporlama için.

## 4. Rollback
*   Kolon silme işlemi veri kaybına yol açmaz (yeni kolonlar).
