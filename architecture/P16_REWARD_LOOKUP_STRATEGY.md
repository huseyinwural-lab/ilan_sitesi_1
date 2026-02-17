# P16 Reward Lookup Strategy (v1)

**Amaç:** Stripe Event'inden (`charge`, `dispute`) sistemimizdeki `ReferralReward` kaydını bulmak.

## 1. Bağlantı Zinciri (Linkage Chain)

Reward, bir `referee_id` (User) ile ilişkilidir. Bu User'ın `Invoice` kayıtları Stripe `payment_intent` veya `charge` ID'lerini tutar.

`Stripe Event` -> `Charge ID` -> `Payment Intent ID` -> `Invoice (Internal DB)` -> `Referee User ID` -> `ReferralReward`

## 2. Arama Algoritması (Lookup Logic)

### Adım 1: Charge ID ile Invoice Bul
Stripe event payload'unda (örneğin `charge.refunded` içinde) `payment_intent` alanı bulunur.
`invoices` tablosunda `stripe_payment_intent_id` sütunu üzerinden sorgu yapılır.

```sql
SELECT * FROM invoices WHERE stripe_payment_intent_id = :pi_id;
```

### Adım 2: Reward Bul
Bulunan `invoice.user_id` (Referee) kullanılarak `referral_rewards` tablosunda arama yapılır.

```sql
SELECT * FROM referral_rewards WHERE referee_id = :user_id;
```

*   **Not:** MVP'de her Referee için tek bir Reward varsayımı vardır (`unique` constraint). Eğer future scope'ta çoklu reward olursa, `invoice_id` reward tablosuna eklenmeli ve doğrudan eşleştirilmelidir. Şu anki yapıda User ID yeterlidir.

## 3. Hata Yönetimi (Unmapped Events)
Eğer `Invoice` veya `Reward` bulunamazsa:
1.  **Log:** `UNMAPPED_STRIPE_EVENT` seviyesinde log atılır (Event ID, Charge ID detaylarıyla).
2.  **Metrik:** `unmapped_event_count` artırılır.
3.  **Aksiyon:** Webhook `200 OK` döner (Retry loop'una girmemek için), ancak işlem yapılmaz (Manuel inceleme gerektirir).
