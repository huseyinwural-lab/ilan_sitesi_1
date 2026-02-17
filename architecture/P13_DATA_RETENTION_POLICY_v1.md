# P13 Data Retention Policy (v1)

**Amaç:** Veritabanı büyümesini kontrol altına almak ve yasal uyumluluğu sağlamak.

## 1. Aktif Veri (Active Data)
*   **Listings:** `active`, `pending`, `suspended` statüsündeki ilanlar ana tabloda süresiz tutulur.
*   **Expired:** `expired` statüsüne düşen ilanlar, son aktivite tarihinden itibaren **180 gün** boyunca ana tabloda tutulur. Bu süre içinde kullanıcı "Renew" (Yenileme) yapabilir.

## 2. Arşivleme (Archiving) - Faz 2
*   **Kural:** 180 günü geçen `expired` ilanlar `listings_archive` tablosuna (soğuk veri) taşınır.
*   **Erişim:** Arşivlenen ilanlar arama sonuçlarında çıkmaz, kullanıcı panelinde "Arşiv" sekmesinde salt okunur görünür.
*   **Renew:** Arşivden renew yapmak için ek ücret talep edilebilir (Business kuralı).

## 3. Kalıcı Silme (Hard Delete)
*   **Kural:** Oluşturulma tarihinden itibaren **3 yıl** geçen ve `deleted` veya `archived` statüsündeki veriler, yasal saklama yükümlülüğü yoksa kalıcı olarak silinir.
*   **GDPR/KVKK:** Kullanıcı talebi üzerine ("Unutulma Hakkı") kişisel veriler 30 gün içinde anonimleştirilir veya silinir.

## 4. Audit Logs
*   **Saklama Süresi:** 1 yıl.
*   **Rotasyon:** 1 yıldan eski loglar dosya tabanlı (S3/Blob) arşive taşınır ve DB'den silinir.
