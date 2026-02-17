# FAZ-U2 Scope Lock

## 1. Kapsam (In-Scope)
Bu faz, ilanın "Draft" aşamasından "Active", "Sold" veya "Expired" aşamasına kadar olan yaşam döngüsünü (Lifecycle) yöneten Backend motorudur.

### 1.1. Core Components
*   **Listing State Machine**: Durum geçişlerini (Draft -> Pending -> Active) yöneten mantık.
*   **Draft System**: İlanın parça parça kaydedilmesini sağlayan yapı.
*   **API (/api/v1/me/listings)**: Kullanıcının ilanlarını yönettiği CRUD endpointleri.

## 2. Kapsam Dışı (Out-of-Scope) - U2 İçin
*   **Wizard UI / Frontend**: U2.1'e devredildi.
*   **Attribute Rendering**: U2.1'e devredildi.
*   **Media Upload (S3)**: U2.1'e devredildi (Şimdilik mock URL).
*   **Payment Integration**: U2.2'ye devredildi.

## 3. Bağımlılıklar
*   **P27**: Moderasyon kuralları ve `is_premium` mantığı korunmalı.
*   **P28**: `user_type` snapshot mantığı eklenecek.
