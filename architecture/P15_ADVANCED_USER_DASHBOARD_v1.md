# P15 Advanced User Dashboard (v1)

**Amaç:** Kullanıcıları platformda tutmak (Retention) ve bir sonraki ödemeye (Renewal/Upgrade) hazırlamak.

## 1. Mimari Bileşenler

### Backend (Analytics API)
Mevcut transactional verilerden özet istatistikler çıkaran hafif bir API katmanı.
*   `GET /api/v1/user/stats`: Genel özet (Toplam İlan, Toplam Görüntülenme, Mesajlar).
*   `GET /api/v1/user/listings/{id}/analytics`: Tekil ilan performansı (Günlük görüntülenme grafiği - *Future: Redis tabanlı time-series*).

### Veri Kaynağı
*   **Görüntülenme (Views):** Şimdilik `listings.views_count` (Counter) sütunu. (High traffic durumunda Redis HyperLogLog).
*   **Favoriler:** `listing_favorites` tablosu count aggregation.

## 2. Özellik Seti (Feature Set)

### A. Performans Grafikleri
*   Kullanıcı panelinde "İlanlarım" sayfasında her ilanın yanında:
    *   👁️ Görüntülenme Sayısı
    *   ❤️ Favoriye Ekleme Sayısı
    *   📞 Telefon Gösterme / Mesaj Sayısı

### B. Quota & Plan Visuals
*   **Progress Bar:** "Kalan İlan Hakkı: 3/10"
*   **Renewal Countdown:** "Planın yenilenmesine 5 gün kaldı. Şimdi yenile, %10 kazan." (Auto-renewal açık değilse).

### C. CRM Lite (Mesajlaşma)
*   Platform içi mesajlaşma (Chat) sistemi P16'da planlansa da, P15'te "Alıcı Soruları" paneli hazırlanır.
*   E-posta ile gelen soruların bir kopyası (Log) burada gösterilir.

### D. Akıllı Bildirimler (Smart Alerts)
*   "İlanın süresi 3 gün içinde dolacak. Öne çıkararak (Showcase) daha hızlı sat."
*   "Bu hafta ilanların 500 kişi tarafından görüntülendi."

## 3. Gelir Etkisi (Revenue Impact)
Dashboard sadece bilgi vermekle kalmaz, eyleme yönlendirir:
*   İstatistikler -> "İlanım ilgi görüyor ama satılmadı" -> **"Fiyatı Düşür"** veya **"Doping Al"** önerisi.
*   Quota Dolu -> **"Upgrade Plan"** butonu (Belirgin).
