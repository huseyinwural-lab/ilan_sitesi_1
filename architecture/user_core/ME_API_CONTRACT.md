# /api/v1/me API Contract

## 1. Endpoints

### 1.1. Profil Görüntüleme
`GET /api/v1/me`
*   **Response**:
    ```json
    {
      "id": "uuid",
      "email": "...",
      "full_name": "...",
      "user_type": "individual",
      "kyc_status": "none",
      "default_country": "DE",
      "badges": ["phone_verified"]
    }
    ```

### 1.2. Profil Güncelleme
`PATCH /api/v1/me`
*   **Request**:
    ```json
    {
      "full_name": "New Name",
      "default_country": "AT"
    }
    ```
*   **Kısıt**: `user_type` buradan değiştirilemez (Upgrade akışı ayrıdır).

### 1.3. Güvenlik Durumu
`GET /api/v1/me/security`
*   **Response**:
    ```json
    {
      "email_verified": true,
      "phone_verified": false,
      "kyc_status": "none",
      "last_password_change": "2024-01-01"
    }
    ```

### 1.4. Telefon Doğrulama (Başlatma)
`POST /api/v1/me/verify-phone`
*   **Request**: `{"phone_number": "+49..."}`
*   **Response**: `{"status": "otp_sent", "expires_in": 180}`
*   *Not: Implementasyon U1.1'de.*
