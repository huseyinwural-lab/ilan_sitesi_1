## Reports Schema + Lifecycle (Locked)

### Koleksiyon: `reports`
Alanlar:
- `id` (uuid)
- `listing_id`
- `reporter_user_id` (optional)
- `reason`
- `reason_note` (optional, `other` için zorunlu)
- `status` (open | in_review | resolved | dismissed)
- `country_code`
- `created_at`
- `updated_at`
- `handled_by_admin_id` (optional)
- `status_note` (son durum notu)

### Lifecycle
```
open → in_review → resolved
                  → dismissed
```

Kurallar:
- Status değişimleri audit-first ile yazılır.
- `other` reason için `reason_note` zorunludur.
