# P14 Promotion Admin API (v1)

**Kapsam:** Kampanya ve Kupon Yönetimi
**Base URL:** `/api/v1/admin`

## 1. Promotions (Kampanyalar)

| Method | Endpoint | Açıklama | Authz |
| :--- | :--- | :--- | :--- |
| `GET` | `/promotions` | Kampanyaları listele (Filter: is_active). | Read |
| `POST` | `/promotions` | Yeni kampanya oluştur. | Write |
| `GET` | `/promotions/{id}` | Kampanya detayı ve özet istatistikler. | Read |
| `PATCH` | `/promotions/{id}` | Kampanya güncelle (Name, Desc, End Date). | Write |
| `POST` | `/promotions/{id}/deactivate` | Kampanyayı durdur. | Write |

### Payloads
**Create Promotion:**
```json
{
  "name": "Summer Sale",
  "description": "20% off",
  "promo_type": "percentage",
  "value": 20.0,
  "currency": "EUR",
  "start_at": "2026-06-01T00:00:00Z",
  "end_at": "2026-06-30T23:59:59Z",
  "max_redemptions": 1000
}
```

## 2. Coupons (Kuponlar)

| Method | Endpoint | Açıklama | Authz |
| :--- | :--- | :--- | :--- |
| `GET` | `/promotions/{id}/coupons` | Kampanyaya ait kuponları listele. | Read |
| `POST` | `/promotions/{id}/coupons` | Kupon kodu üret (Single/Bulk). | Write |
| `POST` | `/coupons/{id}/disable` | Kuponu manuel pasife çek. | Write |

**Create Coupon (Bulk Supported):**
```json
{
  "code_prefix": "SUMMER", // Opsiyonel, code verilmezse random
  "code": "SUMMER20", // Tekli üretim için
  "count": 1, // Bulk için > 1
  "usage_limit": 1,
  "per_user_limit": 1
}
```

## 3. Redemptions (Kullanımlar)

| Method | Endpoint | Açıklama | Authz |
| :--- | :--- | :--- | :--- |
| `GET` | `/redemptions` | Kullanım geçmişi (Filter: promo_id, user_id). | Read |

## Hata Kodları
*   `400`: Validasyon hatası (Tarih sırası, negatif değer).
*   `403`: Yetkisiz rol.
*   `404`: Kayıt bulunamadı.
*   `409`: Conflict (Duplicate coupon code).
