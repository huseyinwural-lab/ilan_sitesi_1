# P14: Promotion Engine & Coupon System (v1)

**Kapsam:** Manuel Yönetimli Kampanya ve Kupon Sistemi
**Entegrasyon:** Stripe + Internal DB

## 1. Mimari Karar
Kupon sistemi "Hibrit" bir yapıda kurgulanacaktır:
*   **Master Data:** Kupon tanımları (Code, Discount, Duration) veritabanımızda (`promotions`, `coupons`) tutulur.
*   **Execution:** Ödeme anında Stripe Promotion Code API'sı kullanılır veya Stripe Checkout'a `discounts` parametresi geçilir.
*   **Validation:** İş mantığı (Kullanıcı limiti, tarih kontrolü) kendi backendimizde doğrulanır.

## 2. Veritabanı Şeması

### `promotions` (Kampanya Tanımı)
*   `id`: UUID
*   `name`: String (Örn: "Yaz İndirimi")
*   `description`: String
*   `is_active`: Boolean
*   `start_at`: Datetime
*   `end_at`: Datetime
*   `type`: Enum (percentage, fixed_amount)
*   `value`: Decimal (Örn: 20.0 - %20 veya 20 EUR)
*   `stripe_coupon_id`: String (Stripe tarafındaki ID)

### `coupons` (Kullanılabilir Kodlar)
*   `id`: UUID
*   `promotion_id`: UUID (FK)
*   `code`: String (Unique - Örn: `YAZ20`, `WELCOME50`)
*   `usage_limit`: Integer (Toplam kaç kez kullanılabilir, Null = Sınırsız)
*   `usage_count`: Integer
*   `per_user_limit`: Integer (Bir kullanıcı kaç kez kullanabilir)

### `coupon_redemptions` (Kullanım Kaydı)
*   `id`: UUID
*   `coupon_id`: UUID
*   `user_id`: UUID
*   `order_id`: UUID (Invoice/Payment ID)
*   `used_at`: Datetime

## 3. Akış (Workflow)

### A. Admin Kupon Oluşturma
1.  Admin panelden kampanya detayları girilir.
2.  Backend, Stripe API ile bir `Coupon` ve gerekirse `PromotionCode` oluşturur.
3.  DB'ye kayıt atılır.

### B. Kullanıcı Kupon Kullanımı (Checkout)
1.  Kullanıcı ödeme ekranında kodu girer.
2.  Backend `/api/v1/billing/validate-coupon` endpoint'i ile:
    *   Kodun geçerliliğini (Tarih, Limit, Aktiflik) veritabanından sorgular.
    *   Kullanıcının daha önce kullanıp kullanmadığını kontrol eder.
3.  Geçerliyse, `/api/v1/billing/checkout` isteğine `coupon_code` parametresi eklenir.
4.  Stripe Checkout Session oluşturulurken `discounts=[{coupon: '...'}]` eklenir.

## 4. API Endpoints
*   `POST /api/v1/admin/promotions`: Yeni kampanya/kupon oluştur.
*   `GET /api/v1/billing/validate-coupon?code=...`: Kod kontrolü (Public/User).

## 5. Güvenlik & Abuse
*   **Race Condition:** `usage_count` artırımı transaction içinde ve `FOR UPDATE` kilidi ile yapılmalı.
*   **Brute Force:** `validate-coupon` endpoint'i rate-limited olmalı.
