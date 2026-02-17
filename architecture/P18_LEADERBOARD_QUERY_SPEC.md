# P18 Leaderboard Query Spec (v1)

**Amaç:** En çok arkadaşını getiren kullanıcıları listelemek (Rekabet Motive Edici).

## 1. Sıralama Kriterleri
*   **Ana Kriter:** `referral_count_confirmed` (Toplam Onaylı Davet Sayısı).
*   **İkincil Kriter (Eşitlikte):** `created_at` (Önce kayıt olan öne geçer) veya `last_referral_date` (Daha güncel olan). MVP: `created_at` ASC.

## 2. Filtreleme & Kapsam
*   **Zaman Aralığı:** "Tüm Zamanlar" (All Time) ve "Bu Ay" (Monthly).
    *   *Not:* `users` tablosundaki denormalize alan "Tüm Zamanlar" içindir. Aylık sıralama için `referral_rewards` tablosu sorgulanmalıdır.
    *   **MVP Kararı:** Sadece "Tüm Zamanlar" (Performans için `users` tablosu).

## 3. Gizlilik (Privacy)
*   Lider tablosunda kullanıcıların tam adı veya e-postası **gösterilmez**.
*   **Format:** `Ad S.` (Örn: "Ahmet Y.") veya `Masked Email` (a***@example.com).

## 4. Cache Stratejisi
*   Veritabanı sorgusu ağırdır (Sort + Limit).
*   **Redis Cache:** `leaderboard:all_time` anahtarı ile saklanır.
*   **TTL:** 10 Dakika.

## 5. API Response
```json
[
  {
    "rank": 1,
    "name": "Ali K.",
    "count": 45,
    "tier": "Platinum"
  },
  {
    "rank": 2,
    "name": "Ayşe M.",
    "count": 32,
    "tier": "Platinum"
  }
]
```
