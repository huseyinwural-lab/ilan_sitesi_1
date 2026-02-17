# P17 Revenue Current State Analysis (v1)

**Tarih:** 16 Şubat 2026
**Kapsam:** Mevcut Gelir Akışları ve Performans Analizi

## 1. Mevcut Gelir Kalemleri
Şu an sistemde aktif olan gelir kalemleri:
1.  **Dealer Abonelikleri (Recurring):**
    *   Basic, Pro ve Enterprise paketleri.
    *   Aylık ödemeli.
2.  **Listing Fee (One-off):**
    *   Bireysel kullanıcılar için ücretsiz limit aşımında ödenen tek seferlik ücret. (Şu an aktif değil veya ücretsiz kota yüksek).
3.  **Referral Cost (Expense):**
    *   Kazanılan her yeni müşteri için ödenen "Stripe Credit". (Gelir azaltıcı kalem).

## 2. Mevcut Metrikler (Baseline)
*   **ARPU (Average Revenue Per User):** Düşük (Henüz premium ürün yok).
*   **Conversion Rate:** %2-3 (Sektör standardı).
*   **Churn Rate:** Bilinmiyor (Veri yetersiz).

## 3. Eksikler ve Fırsatlar
*   **Upsell Eksikliği:** Kullanıcıya ödeme anında "Daha üst pakete geç" veya "İlanını öne çıkar" teklifi sunulmuyor.
*   **Premium Ürün Yok:** İlanı vitrine taşıma (Showcase) veya acil etiketi gibi mikro ödemeler eksik.
*   **Statik Fiyat:** İstanbul'daki emlak ilanı ile Bayburt'taki emlak ilanı aynı fiyattan listeleniyor (Fırsat kaybı).
