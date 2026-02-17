# P17 Premium Visibility Design (v1)

**Amaç:** İlan sahiplerine (Hem Bireysel Hem Kurumsal) daha fazla görünürlük satmak.

## 1. Showcase (Vitrin)
*   **Tanım:** İlanın, arama sonuçlarının en üstünde "Vitrin İlanları" bölümünde veya ana sayfada gösterilmesi.
*   **Mekanizma:**
    *   Belirli bir slot sayısı vardır (Örn: Her kategoride 10 slot).
    *   Random rotasyon veya bidding (ileride) ile gösterilir.
*   **Süre:** 1 Hafta, 2 Hafta, 4 Hafta.

## 2. Boost (Yukarı Taşı - Doping)
*   **Tanım:** İlanın `updated_at` tarihini (veya özel bir `boosted_at` alanını) güncelleyerek, "En Yeniler" sıralamasında en üste çıkmasını sağlamak.
*   **Mekanizma:** Tek seferlik işlemdir. Etkisi, yeni ilanlar eklendikçe azalır.
*   **Kullanım:** "İlanım altlarda kaldı, tekrar yukarı çıkarmak istiyorum."

## 3. Urgent (Acil Acil)
*   **Tanım:** İlan kartında dikkat çekici bir "ACİL" rozeti ve çerçeve rengi.
*   **Mekanizma:** Görsel farkındalık yaratır. Sıralamayı etkilemez (veya çok az etkiler).
*   **Süre:** 1 Hafta.

## 4. Bold Title (Kalın Başlık)
*   **Tanım:** İlan başlığının listede **kalın** ve renkli yazılması.
*   **Mekanizma:** CTR (Tıklama Oranı) artırıcı.
