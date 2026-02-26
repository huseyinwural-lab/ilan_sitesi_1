# CATEGORY API ERROR CONTRACTS

## Kapsam

Kategori yönetimi için zorunlu API hata kontratları:

1. `ORDER_INDEX_ALREADY_USED`
2. `VEHICLE_SEGMENT_NOT_FOUND`

Bu kontratlar Swagger/OpenAPI üzerinde ilgili endpoint response örnekleriyle yayınlanır.

---

## 1) ORDER_INDEX_ALREADY_USED

- **HTTP Status:** `400`
- **Ne zaman döner:**
  - Aynı scope içinde (`country_code + module + parent_id`) aynı `sort_order` tekrar kullanıldığında
- **Response body:**

```json
{
  "detail": {
    "error_code": "ORDER_INDEX_ALREADY_USED",
    "message": "Bu modül ve seviye içinde bu sıra numarası zaten kullanılıyor."
  }
}
```

---

## 2) VEHICLE_SEGMENT_NOT_FOUND

- **HTTP Status:** `400`
- **Ne zaman döner:**
  - Vehicle modülünde girilen serbest metin segment, master data tarafında normalize/case-insensitive eşleşme bulamazsa
- **Response body:**

```json
{
  "detail": {
    "error_code": "VEHICLE_SEGMENT_NOT_FOUND",
    "message": "Girilen segment master data’da bulunamadı."
  }
}
```

---

## Endpoint Referansları

- `POST /api/admin/categories`
- `PATCH /api/admin/categories/{category_id}`
- `GET /api/admin/categories/vehicle-segment/link-status` (segment doğrulama)
