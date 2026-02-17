# Listing Schema Extension (U2)

## 1. Değişiklikler
Mevcut `listings` tablosuna eklenecek kolonlar:

```sql
ALTER TABLE listings 
ADD COLUMN current_step INTEGER DEFAULT 1,
ADD COLUMN completion_percentage INTEGER DEFAULT 0,
ADD COLUMN user_type_snapshot VARCHAR(20), -- individual/commercial at publish time
ADD COLUMN last_edited_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN moderated_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN moderated_by UUID,
ADD COLUMN rejected_reason TEXT,
ADD COLUMN deleted_at TIMESTAMP WITH TIME ZONE;
```

## 2. Indexler
*   `ix_listings_user_status`: Kullanıcının ilanlarını filtrelemek için (`user_id`, `status`).
*   `ix_listings_expires`: Süresi dolan ilanları bulmak için (`status='active'`, `expires_at`).

## 3. Mevcut Alanlar (P27'den)
*   `status` (Enum değerleri güncellenecek).
*   `is_premium`, `is_showcase`.
*   `view_count`.
