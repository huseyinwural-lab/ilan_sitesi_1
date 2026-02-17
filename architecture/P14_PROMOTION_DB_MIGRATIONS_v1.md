# P14 Promotion DB Migrations (v1)

**Kapsam:** Veritabanı Şeması Tasarımı
**Hedef:** Kampanya ve Kupon verilerinin tutarlılığını sağlamak.

## Tablolar

### 1. `promotions` (Kampanya Tanımı)
Genel kampanya kurallarını tutar.
*   `id`: UUID (PK)
*   `name`: String (Admin için isim)
*   `description`: String (Opsiyonel)
*   `promo_type`: Enum ('percentage', 'fixed_amount')
*   `value`: Decimal (İndirim miktarı. Örn: 20.0)
*   `currency`: String (Fixed amount ise gerekli, percentage ise null olabilir ama EUR default)
*   `start_at`: Datetime (Başlangıç)
*   `end_at`: Datetime (Bitiş)
*   `is_active`: Boolean (Default: True)
*   `max_redemptions`: Integer (Kampanya genelinde toplam kullanım limiti)
*   `stripe_coupon_id`: String (Stripe tarafındaki ID eşleşmesi)
*   `created_at`, `updated_at`

### 2. `coupons` (Kupon Kodları)
Kullanıcının girdiği kodlar. Bir kampanyaya bağlıdır.
*   `id`: UUID (PK)
*   `promotion_id`: UUID (FK -> promotions.id)
*   `code`: String (Unique, Index, Uppercase)
*   `usage_limit`: Integer (Bu spesifik kod kaç kez kullanılabilir)
*   `usage_count`: Integer (Default: 0)
*   `per_user_limit`: Integer (Default: 1 - Bir kullanıcı kaç kez kullanabilir)
*   `is_active`: Boolean (Default: True)
*   `created_at`

### 3. `coupon_redemptions` (Kullanım Geçmişi)
Başarılı kullanımları tutar.
*   `id`: UUID (PK)
*   `coupon_id`: UUID (FK -> coupons.id)
*   `user_id`: UUID (FK -> users.id)
*   `order_id`: UUID (FK -> invoices.id, Nullable - Ödeme referansı)
*   `redeemed_at`: Datetime (Default: NOW)
*   `discount_amount`: Decimal (Uygulanan indirim tutarı - Raporlama için)

## Constraints & Indexes
*   `coupons`: `UNIQUE(code)`
*   `coupon_redemptions`: `UNIQUE(coupon_id, user_id)` (Karar: User başına 1 kullanım/kupon stack yok)
*   `coupon_redemptions`: `INDEX(user_id)`
*   `coupon_redemptions`: `INDEX(order_id)`

## Migration Planı
1.  Model dosyası `app/models/promotion.py` oluşturulacak.
2.  `env.py` güncellenecek.
3.  Alembic revision oluşturulacak.
