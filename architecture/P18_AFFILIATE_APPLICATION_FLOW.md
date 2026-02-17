# P18 Affiliate Application Flow (v1)

**Kapsam:** Kullanıcıların Affiliate programına katılması ve Admin onayı.

## 1. Başvuru (`POST /api/v1/affiliate/apply`)
*   **Giriş:**
    *   `custom_slug`: İstenen özel link (örn: `fenomen_ali`).
    *   `payout_details`: Ödeme bilgileri (IBAN, Ad Soyad).
*   **Validasyon:**
    *   Slug müsait mi? (Unique check).
    *   Slug formatı (A-Z0-9, -_).
    *   Kullanıcı zaten başvurdu mu?
*   **İşlem:**
    *   `Affiliate` tablosuna `pending` statüsünde kayıt atılır.
    *   `users.is_affiliate` henüz `False` kalır.

## 2. İnceleme (`POST /api/v1/admin/affiliates/{id}/review`)
*   **Yetki:** Super Admin.
*   **Giriş:** `action` ('approve', 'reject'), `reject_reason` (opsiyonel).
*   **Onay (Approve):**
    *   Statü `approved` olur.
    *   `users.is_affiliate` = `True`.
    *   Kullanıcıya e-posta gönderilir (Mock).
*   **Red (Reject):**
    *   Statü `rejected` olur.
    *   Slug serbest bırakılır mı? Hayır, kayıt kalır ama pasif olur (Yeniden başvuru için yeni kayıt veya update gerekir - MVP: Yeni kayıt engellenir, update beklenir).

## 3. Dashboard (`GET /api/v1/affiliate/me`)
*   Kullanıcı kendi başvuru durumunu ve (onaylandıysa) istatistiklerini görür.
