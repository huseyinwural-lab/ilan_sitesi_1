# /api/v1/me/listings Contract

## 1. Endpoints

### 1.1. Taslak Oluşturma
`POST /api/v1/me/listings`
*   **Body**: `{"category_id": "...", "module": "vehicle"}`
*   **Response**: `{"id": "...", "status": "DRAFT", "current_step": 1}`

### 1.2. İlan Listesi
`GET /api/v1/me/listings`
*   **Query**: `?status=active`, `?page=1`
*   **Response**: `[ListingSummaryDTO]`

### 1.3. İlan Detayı
`GET /api/v1/me/listings/{id}`
*   **Response**: Full Listing DTO + `rejected_reason` (varsa).

### 1.4. Güncelleme (Auto-Save)
`PATCH /api/v1/me/listings/{id}`
*   **Body**: `{"title": "...", "price": 100, "current_step": 2}`
*   **Effect**: Updates `last_edited_at`, recalculates `completion_percentage`.

### 1.5. Yayına Gönderme
`POST /api/v1/me/listings/{id}/submit`
*   **Check**: Completion %100 mü?
*   **Effect**: Status -> `PENDING_MODERATION`.

### 1.6. Silme
`DELETE /api/v1/me/listings/{id}`
*   **Effect**: Sets `deleted_at = NOW`, `status = DELETED`.
