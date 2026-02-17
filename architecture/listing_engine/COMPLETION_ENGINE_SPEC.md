# Completion Engine Specification

## 1. Hesaplama Mantığı
İlanın doluluk oranını (%0 - %100) hesaplar.

### 1.1. Ağırlıklar
*   **Kategori Seçimi**: %10 (Adım 1)
*   **Temel Bilgiler (Başlık, Fiyat)**: %30 (Adım 2)
*   **Açıklama & Özellikler**: %30 (Adım 2)
*   **Fotoğraf (Min 1)**: %20 (Adım 3)
*   **İletişim/Konum**: %10 (Adım 4)

## 2. Kural
*   `submit_listing` işlemi için `completion_percentage == 100` olmalıdır.
