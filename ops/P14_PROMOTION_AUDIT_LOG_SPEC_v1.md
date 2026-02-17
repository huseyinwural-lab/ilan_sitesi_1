# P14 Promotion Audit Log Spec (v1)

**Amaç:** Adminlerin kampanya ve kupon üzerindeki tüm *değişikliklerinin* (Write ops) kayıt altına alınması.

## Loglanacak Olaylar (Events)

### 1. Kampanya Yönetimi
*   `PROMOTION_CREATE`: Yeni kampanya oluşturulduğunda.
*   `PROMOTION_UPDATE`: Tarih, limit veya açıklama değişikliği.
*   `PROMOTION_DEACTIVATE`: Kampanya durdurulduğunda (Acil durum/Bitiş).

### 2. Kupon Yönetimi
*   `COUPON_CREATE`: Tekli kupon oluşturma.
*   `COUPON_BULK_CREATE`: Çoklu üretim (Log detayında kaç adet üretildiği yazmalı).
*   `COUPON_DISABLE`: Tekil bir kuponun iptali.

## Log Formatı (AuditLog Table)

| Alan | Örnek Veri |
| :--- | :--- |
| `action` | `PROMOTION_CREATE` |
| `resource_type` | `promotion` |
| `resource_id` | `{uuid}` |
| `user_id` | `{admin_uuid}` |
| `new_values` | `{"name": "Summer", "value": 20, "max_redemptions": 100}` |
| `old_values` | `null` (Create) veya önceki değerler (Update) |

## Kritik Kural
Herhangi bir `POST`, `PATCH`, `DELETE` (veya disable) işlemi, veritabanı `commit` işleminden hemen önce veya sonra `log_action` fonksiyonunu çağırmak zorundadır.
